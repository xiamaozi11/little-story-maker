"""StoryCraft REST API — 供 Android 移动端调用。"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from storycraft.api.image_generator import ImageGenerator
from storycraft.api.anime_generator import AnimeGenerator
from storycraft.api.session_store import SessionStore
from storycraft.api.text_generator import TextGenerator
from storycraft.config import (
    API_ENDPOINT,
    API_KEY,
    DEFAULT_IMAGE_STYLE,
    DEFAULT_SCENES,
    IMAGE_STYLES,
    IMAGE_SIZE,
    MAX_SCENES,
    MIN_SCENES,
    OUTPUT_DIR,
    TEXT_MODEL,
)
from storycraft.core.pdf_generator import PDFGenerator

app = FastAPI(title="StoryCraft API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = SessionStore(OUTPUT_DIR)

DOUBAO_SIZES = {
    "1920x2560 (3:4 竖版，推荐)": "1920x2560",
    "2048x2730 (3:4 竖版，高清)": "2048x2730",
    "2048x2048 (1:1 正方形)": "2048x2048",
    "2560x1920 (4:3 横版)": "2560x1920",
    "2048x1536 (4:3 横版小)": "2048x1536",
}

TONGYI_SIZES = {
    "1104x1472 (3:4 竖版，推荐)": "1104x1472",
    "1280x1280 (1:1 正方形)": "1280x1280",
    "960x1280 (3:4 竖版)": "960x1280",
    "1472x1104 (4:3 横版)": "1472x1104",
    "960x1696 (9:16 竖版长)": "960x1696",
}


class GenerateStoryRequest(BaseModel):
    idea: str = Field(..., min_length=1, max_length=500)
    character: str = Field(..., min_length=1, max_length=20)
    num_scenes: int = Field(DEFAULT_SCENES, ge=MIN_SCENES, le=MAX_SCENES)


class UpdateSceneRequest(BaseModel):
    text: str = Field(..., min_length=1)


class GeneratePicturesRequest(BaseModel):
    image_service: str = Field("doubao", pattern="^(doubao|tongyi)$")
    image_style: str = Field(DEFAULT_IMAGE_STYLE)
    image_size: str = Field(IMAGE_SIZE)


class GeneratePdfRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    author: str = Field("云朵爸爸", max_length=50)


class RegenerateScenesRequest(BaseModel):
    scene_numbers: List[int] = Field(..., min_length=1)


class GenerateAnimeStoryRequest(BaseModel):
    idea: str = Field(..., min_length=1, max_length=500)
    character: str = Field(..., min_length=1, max_length=20)
    num_segments: int = Field(2, ge=1, le=4)


class GenerateAnimeVideosRequest(BaseModel):
    image_service: str = Field("tongyi", pattern="^(doubao|tongyi)$")
    image_style: str = Field("动漫")
    image_size: str = Field(IMAGE_SIZE)
    video_size: str = Field("960x1696")


def _check_api_key() -> None:
    if not API_KEY:
        raise HTTPException(status_code=500, detail="请先在 .env 中配置 API_KEY")


def _make_session_id(character: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_character = "".join(c for c in character if c.isalnum() or c in "_-")
    return f"{timestamp}_{safe_character}"


def _public_scenes(scenes: List[Dict[str, Any]], session_id: str) -> List[Dict[str, Any]]:
    result = []
    for idx, scene in enumerate(scenes):
        item = {
            "index": idx,
            "scene_number": idx + 1,
            "text": scene.get("text", ""),
            "text_en": scene.get("text_en"),
            "image_prompt": scene.get("image_prompt"),
        }
        image_path = scene.get("image_path")
        if image_path:
            filename = Path(image_path).name
            item["image_url"] = f"/api/files/{session_id}/{filename}"
        result.append(item)
    return result


def _public_session(session: Dict[str, Any]) -> Dict[str, Any]:
    session_id = session["session_id"]
    has_images = bool(
        session.get("scenes") and "image_path" in session["scenes"][0]
    )
    pdf_url = None
    if session.get("pdf_path"):
        pdf_url = f"/api/files/{session_id}/{Path(session['pdf_path']).name}"

    return {
        "session_id": session_id,
        "idea": session.get("idea", ""),
        "character": session.get("character", ""),
        "num_scenes": len(session.get("scenes", [])),
        "character_description": session.get("character_description", ""),
        "story_generated": session.get("story_generated", False),
        "story_confirmed": session.get("story_confirmed", False),
        "has_images": has_images,
        "image_style": session.get("image_style"),
        "image_service": session.get("image_service"),
        "image_size": session.get("image_size"),
        "scenes": _public_scenes(session.get("scenes", []), session_id),
        "pdf_url": pdf_url,
        "created_at": session.get("created_at"),
    }


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
def get_config() -> Dict[str, Any]:
    return {
        "min_scenes": MIN_SCENES,
        "max_scenes": MAX_SCENES,
        "default_scenes": DEFAULT_SCENES,
        "image_styles": list(IMAGE_STYLES.keys()),
        "default_image_style": DEFAULT_IMAGE_STYLE,
        "image_services": [
            {"id": "doubao", "label": "豆包"},
            {"id": "tongyi", "label": "通义千问"},
        ],
        "doubao_sizes": DOUBAO_SIZES,
        "tongyi_sizes": TONGYI_SIZES,
    }


@app.get("/api/sessions")
def list_sessions() -> List[Dict[str, Any]]:
    return store.list_sessions()


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> Dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return _public_session(session)


@app.post("/api/sessions/story")
def generate_story(req: GenerateStoryRequest) -> Dict[str, Any]:
    _check_api_key()
    try:
        text_gen = TextGenerator(API_KEY, API_ENDPOINT, TEXT_MODEL)
        story_data = text_gen.generate_story(
            req.idea, req.character, req.num_scenes, chinese_only=True
        )
        session_id = _make_session_id(req.character)
        session_dir = Path(OUTPUT_DIR) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        session = store.create(
            session_id=session_id,
            idea=req.idea,
            character=req.character,
            num_scenes=req.num_scenes,
            scenes=story_data["scenes"],
            character_description=story_data.get("character_description", ""),
        )

        story_file = session_dir / "story_draft.txt"
        with open(story_file, "w", encoding="utf-8") as f:
            f.write(f"故事创意：{req.idea}\n主角：{req.character}\n\n")
            for idx, scene in enumerate(story_data["scenes"], 1):
                f.write(f"【场景 {idx}】\n{scene['text']}\n\n")

        return _public_session(session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"故事生成失败: {e}") from e


@app.put("/api/sessions/{session_id}/scenes/{index}")
def update_scene(session_id: str, index: int, req: UpdateSceneRequest) -> Dict[str, Any]:
    try:
        session = store.update_scene(session_id, index, req.text)
        return _public_session(session)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/sessions/{session_id}/pictures")
def generate_pictures(
    session_id: str, req: GeneratePicturesRequest
) -> Dict[str, Any]:
    _check_api_key()
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if not session.get("scenes"):
        raise HTTPException(status_code=400, detail="请先生成故事")

    if req.image_style not in IMAGE_STYLES:
        raise HTTPException(status_code=400, detail="无效的图片风格")

    try:
        text_gen = TextGenerator(API_KEY, API_ENDPOINT, TEXT_MODEL)
        scenes = session["scenes"]

        need_translate = any(
            "text_en" not in s or not s.get("text_en") for s in scenes
        )
        if need_translate:
            translations = text_gen.translate_scenes_batch(scenes)
            for idx, scene in enumerate(scenes):
                scene["text_en"] = translations[idx]

        need_prompts = any(
            "image_prompt" not in s or not s.get("image_prompt") for s in scenes
        )
        if need_prompts:
            prompts = text_gen.generate_image_prompts_batch(
                scenes, session.get("character_description", "")
            )
            for idx, scene in enumerate(scenes):
                scene["image_prompt"] = prompts[idx]

        img_gen = ImageGenerator(
            API_KEY,
            OUTPUT_DIR,
            style=req.image_style,
            service=req.image_service,
            image_size=req.image_size,
        )
        if session.get("character_description"):
            img_gen.character_description = session["character_description"]

        session_dir = Path(OUTPUT_DIR) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        img_gen.output_dir = session_dir

        image_prompts = [s.get("image_prompt", "") for s in scenes]
        image_paths = img_gen.generate_batch(
            image_prompts, session.get("character_description", "")
        )
        for idx, img_path in enumerate(image_paths):
            scenes[idx]["image_path"] = img_path

        session["scenes"] = scenes
        session["image_style"] = req.image_style
        session["image_service"] = req.image_service
        session["image_size"] = req.image_size
        session["story_confirmed"] = True
        store.save(session_id, session)

        return _public_session(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"绘本生成失败: {e}") from e


@app.post("/api/sessions/{session_id}/pdf")
def generate_pdf(session_id: str, req: GeneratePdfRequest) -> Dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if not session.get("scenes") or "image_path" not in session["scenes"][0]:
        raise HTTPException(status_code=400, detail="请先生成插画")

    try:
        output_path = Path(OUTPUT_DIR) / session_id
        pdf_gen = PDFGenerator(str(output_path))
        pdf_path = pdf_gen.generate(session["scenes"], req.title, req.author)
        session["pdf_path"] = pdf_path
        store.save(session_id, session)

        result = _public_session(session)
        result["pdf_size_mb"] = round(Path(pdf_path).stat().st_size / (1024 * 1024), 2)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败: {e}") from e


@app.post("/api/sessions/{session_id}/regenerate")
def regenerate_scenes(
    session_id: str, req: RegenerateScenesRequest
) -> Dict[str, Any]:
    _check_api_key()
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session.get("image_service") != "tongyi":
        raise HTTPException(status_code=400, detail="仅通义千问支持重新生成场景图片")

    try:
        img_gen = ImageGenerator(
            API_KEY,
            OUTPUT_DIR,
            style=session.get("image_style", DEFAULT_IMAGE_STYLE),
            service=session["image_service"],
            image_size=session.get("image_size", IMAGE_SIZE),
        )
        if session.get("character_description"):
            img_gen.character_description = session["character_description"]
        img_gen.output_dir = Path(OUTPUT_DIR) / session_id

        for scene_num in req.scene_numbers:
            idx = scene_num - 1
            if idx < 0 or idx >= len(session["scenes"]):
                continue
            scene = session["scenes"][idx]
            new_path = img_gen.generate(
                scene.get("image_prompt", ""), f"scene_{scene_num}"
            )
            session["scenes"][idx]["image_path"] = new_path

        store.save(session_id, session)
        return _public_session(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新生成失败: {e}") from e


@app.post("/api/sessions/anime/story")
def generate_anime_story(req: GenerateAnimeStoryRequest) -> Dict[str, Any]:
    """根据梗概生成动漫分镜剧本（可含多个短视频剧本）。"""
    _check_api_key()
    try:
        text_gen = TextGenerator(API_KEY, API_ENDPOINT, TEXT_MODEL)
        board = text_gen.generate_anime_storyboard(
            req.idea, req.character, req.num_segments
        )
        session_id = _make_session_id(req.character)
        session_dir = Path(OUTPUT_DIR) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        session = store.create(
            session_id=session_id,
            idea=req.idea,
            character=req.character,
            num_scenes=0,
            scenes=[],
            character_description=board.get("character_description", ""),
        )
        session["content_type"] = "anime"
        session["anime"] = board
        store.save(session_id, session)
        return _public_anime_session(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"动漫分镜生成失败: {e}") from e


def _public_anime_session(session: Dict[str, Any]) -> Dict[str, Any]:
    base = _public_session(session)
    anime = session.get("anime", {})
    base["content_type"] = "anime"
    base["anime"] = anime
    return base


@app.post("/api/sessions/{session_id}/anime/characters")
def generate_anime_characters(session_id: str) -> Dict[str, Any]:
    """生成主要角色参考素材（动漫视频生成前必须完成）。"""
    _check_api_key()
    session = store.get(session_id)
    if not session or session.get("content_type") != "anime":
        raise HTTPException(status_code=404, detail="动漫会话不存在")
    anime = session.get("anime", {})
    try:
        img_gen = ImageGenerator(
            API_KEY,
            OUTPUT_DIR,
            style=session.get("image_style", "动漫"),
            service=session.get("image_service", "tongyi"),
            image_size=session.get("image_size", IMAGE_SIZE),
        )
        session_dir = Path(OUTPUT_DIR) / session_id
        img_gen.output_dir = session_dir

        ag = AnimeGenerator(TextGenerator(API_KEY, API_ENDPOINT, TEXT_MODEL), img_gen, session_dir)
        characters = ag.generate_character_assets(
            anime.get("characters", []),
            anime.get("character_description", ""),
        )
        anime["characters"] = characters
        session["anime"] = anime
        store.save(session_id, session)
        return _public_anime_session(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"角色素材生成失败: {e}") from e


@app.post("/api/sessions/{session_id}/anime/videos")
def generate_anime_videos(
    session_id: str, req: GenerateAnimeVideosRequest
) -> Dict[str, Any]:
    """串行生成各剧本的 15s 视频段（Seedance 2.0）。"""
    _check_api_key()
    session = store.get(session_id)
    if not session or session.get("content_type") != "anime":
        raise HTTPException(status_code=404, detail="动漫会话不存在")

    anime = session.get("anime", {})
    characters = anime.get("characters", [])
    if not any(c.get("image_status") == "ok" for c in characters):
        raise HTTPException(status_code=400, detail="请先生成主要角色素材")

    try:
        session_dir = Path(OUTPUT_DIR) / session_id
        img_gen = ImageGenerator(
            API_KEY,
            OUTPUT_DIR,
            style=req.image_style,
            service=req.image_service,
            image_size=req.image_size,
        )
        img_gen.output_dir = session_dir

        text_gen = TextGenerator(API_KEY, API_ENDPOINT, TEXT_MODEL)
        seedance_key = os.getenv("VOLC_SEEDANCE_API_KEY", "") or API_KEY
        ag = AnimeGenerator(
            text_gen,
            img_gen,
            session_dir,
            seedance_api_key=seedance_key,
            video_size=req.video_size,
        )

        # 本地路径需映射为可访问 URL（若已配置静态文件服务）
        for char in characters:
            path = char.get("image_path")
            if path and not char.get("image_url"):
                fname = Path(path).name
                char["image_url"] = f"/api/files/{session_id}/{fname}"

        scripts_board = anime.get("scripts", [])
        videos_result = []
        for i, script in enumerate(scripts_board):
            videos_result.append(
                ag.generate_script_videos(script, characters, script_index=i)
            )

        anime["videos"] = videos_result
        anime["has_videos"] = any(
            v.get("completed") for v in videos_result
        )
        session["anime"] = anime
        session["image_style"] = req.image_style
        session["image_service"] = req.image_service
        session["image_size"] = req.image_size
        store.save(session_id, session)
        return _public_anime_session(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"动漫视频生成失败: {e}") from e


@app.get("/api/files/{session_id}/{filename}")
def get_file(session_id: str, filename: str):
    file_path = Path(OUTPUT_DIR) / session_id / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")

    media = "application/octet-stream"
    if filename.lower().endswith(".png"):
        media = "image/png"
    elif filename.lower().endswith((".jpg", ".jpeg")):
        media = "image/jpeg"
    elif filename.lower().endswith(".pdf"):
        media = "application/pdf"
    elif filename.lower().endswith(".mp4"):
        media = "video/mp4"

    return FileResponse(file_path, media_type=media, filename=filename)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True)
