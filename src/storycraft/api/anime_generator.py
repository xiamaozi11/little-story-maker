"""动漫短视频生成：分镜 → 角色素材 → Seedance 2.0 分段视频（串行衔接）。"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from storycraft.api.image_generator import ImageGenerator
from storycraft.api.text_generator import TextGenerator
from storycraft.core.logger import setup_logger

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from seedance20_client import (  # noqa: E402
    build_seedance20_prompt_with_refs,
    post_seedance20_and_wait,
)

logger = setup_logger()

SHOTS_PER_SEGMENT = 5
SEGMENT_DURATION_SEC = 15
MAX_SEGMENTS_PER_SCRIPT = 4
MAX_SHOTS_PER_SCRIPT = SHOTS_PER_SEGMENT * MAX_SEGMENTS_PER_SCRIPT


def _group_shots(shots: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    segments: List[List[Dict[str, Any]]] = []
    for i in range(0, len(shots), SHOTS_PER_SEGMENT):
        chunk = shots[i : i + SHOTS_PER_SEGMENT]
        if len(chunk) == SHOTS_PER_SEGMENT:
            segments.append(chunk)
    return segments[:MAX_SEGMENTS_PER_SCRIPT]


def _build_segment_prompt(
    shots: List[Dict[str, Any]],
    *,
    script_title: str,
    segment_index: int,
    is_continuation: bool,
) -> str:
    lines = [f"【{script_title} · 第{segment_index + 1}段 · 15秒动漫短片】"]
    if is_continuation:
        lines.append("承接上一段视频最后一帧画面，动作与场景自然延续，不要跳切。")
    for i, shot in enumerate(shots):
        start = i * 3
        end = start + 3
        text = shot.get("text", "")
        dialogue = shot.get("dialogue", "")
        vp = shot.get("video_prompt", "")
        lines.append(f"镜头{i + 1}（{start}-{end}秒）：{text}")
        if dialogue:
            lines.append(f"  对白：{dialogue}")
        if vp:
            lines.append(f"  画面：{vp}")
    lines.append(
        "要求：日本动漫 cel shading 风格，儿童向，色彩明亮，动作流畅，"
        "镜头间自然过渡，角色口型与对白匹配，无暴力恐怖元素。"
    )
    return "\n".join(lines)


class AnimeGenerator:
    """编排动漫生成全流程。"""

    def __init__(
        self,
        text_generator: TextGenerator,
        image_generator: ImageGenerator,
        output_dir: Path,
        *,
        seedance_api_key: Optional[str] = None,
        video_size: str = "960x1696",
    ):
        self.text_generator = text_generator
        self.image_generator = image_generator
        self.output_dir = output_dir
        self.seedance_api_key = seedance_api_key
        self.video_size = video_size
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_storyboard(
        self, idea: str, character: str, num_segments: int = 2
    ) -> Dict[str, Any]:
        return self.text_generator.generate_anime_storyboard(
            idea, character, num_segments
        )

    def generate_character_assets(
        self,
        characters: List[Dict[str, Any]],
        character_description: str = "",
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """为主要人物生成参考立绘（动漫生成前必须完成）。"""
        results: List[Dict[str, Any]] = []
        for idx, char in enumerate(characters):
            name = char.get("name", f"角色{idx + 1}")
            on_progress and on_progress(f"生成角色素材：{name}")
            prompt = char.get("image_prompt", "")
            if not prompt:
                desc = char.get("description", name)
                prompt = (
                    f"Anime character reference sheet, {desc}, "
                    f"full body, simple background, cel shading, child-friendly"
                )
            if character_description:
                prompt = f"{prompt}. Character design: {character_description}"

            try:
                path = self.image_generator.generate(prompt, f"character_{idx + 1}")
                results.append(
                    {
                        **char,
                        "image_path": path,
                        "image_status": "ok",
                    }
                )
            except Exception as e:
                logger.error(f"角色 {name} 素材生成失败: {e}")
                results.append(
                    {
                        **char,
                        "image_status": "failed",
                        "image_error": str(e),
                    }
                )
        return results

    def _character_image_urls(self, characters: List[Dict[str, Any]]) -> List[str]:
        """角色参考图需为公网 URL；本地路径时由调用方先上传。"""
        urls: List[str] = []
        for char in characters:
            url = char.get("image_url") or char.get("image_path")
            if url and str(url).startswith("http"):
                urls.append(str(url))
        return urls

    def generate_script_videos(
        self,
        script: Dict[str, Any],
        characters: List[Dict[str, Any]],
        *,
        script_index: int = 0,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
    ) -> Dict[str, Any]:
        """为一个剧本串行生成 15s 视频段，前段完成后才生成后段。"""
        shots = script.get("shots", [])
        segments_shots = _group_shots(shots)
        if not segments_shots:
            raise ValueError("剧本镜头不足 5 个，无法生成视频")

        char_urls = self._character_image_urls(characters)
        if not char_urls:
            raise ValueError("缺少角色参考图 URL，请先生成并上传角色素材")

        char_labels = [c.get("name", f"角色{i + 1}") for i, c in enumerate(characters)]
        segments_out: List[Dict[str, Any]] = []
        prev_video_url: Optional[str] = None
        total = len(segments_shots)

        for seg_idx, seg_shots in enumerate(segments_shots):
            on_progress and on_progress(
                f"剧本{script_index + 1} 第{seg_idx + 1}/{total}段视频",
                seg_idx + 1,
                total,
            )
            base_prompt = _build_segment_prompt(
                seg_shots,
                script_title=script.get("title", "动漫"),
                segment_index=seg_idx,
                is_continuation=prev_video_url is not None,
            )
            image_labels = char_labels[: len(char_urls)]
            prompt = build_seedance20_prompt_with_refs(
                base_prompt,
                image_labels=image_labels,
                video_labels=["上一段视频"] if prev_video_url else None,
            )

            by_pass: Dict[str, Any] = {
                "ratio": "9:16",
                "resolution": "720p",
            }
            if prev_video_url:
                by_pass["videos"] = [prev_video_url]

            result = post_seedance20_and_wait(
                prompt,
                duration=SEGMENT_DURATION_SEC,
                size=self.video_size,
                generate_audio=True,
                generate_mode=1,
                by_pass=by_pass,
                images=char_urls,
                api_key=self.seedance_api_key,
                verbose=True,
            )

            seg_data: Dict[str, Any] = {
                "segment_index": seg_idx,
                "shot_indices": list(
                    range(seg_idx * SHOTS_PER_SEGMENT, (seg_idx + 1) * SHOTS_PER_SEGMENT)
                ),
                "status": "ok" if result.get("ok") else "failed",
                "task_id": result.get("task_id"),
                "video_url": result.get("video_url"),
            }
            if not result.get("ok"):
                seg_data["error"] = result.get("error", "视频生成失败")
                segments_out.append(seg_data)
                break

            prev_video_url = result.get("video_url")
            segments_out.append(seg_data)

        return {
            "script_index": script_index,
            "title": script.get("title"),
            "segments": segments_out,
            "completed": all(s.get("status") == "ok" for s in segments_out),
        }

    def generate_all(
        self,
        idea: str,
        character: str,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """完整流程：分镜 → 角色素材 → 各剧本视频。"""
        on_progress and on_progress("生成分镜剧本...")
        board = self.generate_storyboard(idea, character)

        on_progress and on_progress("生成主要角色素材...")
        characters = self.generate_character_assets(
            board.get("characters", []),
            board.get("character_description", ""),
            on_progress=on_progress,
        )

        scripts_result: List[Dict[str, Any]] = []
        for i, script in enumerate(board.get("scripts", [])):
            on_progress and on_progress(f"生成剧本「{script.get('title')}」视频...")
            scripts_result.append(
                self.generate_script_videos(
                    script,
                    characters,
                    script_index=i,
                    on_progress=lambda msg, cur, tot: on_progress
                    and on_progress(f"{msg} ({cur}/{tot})"),
                )
            )

        return {
            "synopsis": board.get("synopsis"),
            "character_description": board.get("character_description"),
            "characters": characters,
            "scripts": scripts_result,
        }
