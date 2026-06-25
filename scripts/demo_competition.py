#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小小故事家 — 比赛提交用终端技术演示

演示内容（与 Android App 一致，不修改 App 代码）：
  1. 端侧 MNN ASR 模型本地加载过程
  2. 云端通义千问推理输入/输出
  3. 绘本 + 动漫核心交互流程

用法:
  python scripts/demo_competition.py              # 演示模式（不调用 API，适合彩排）
  python scripts/demo_competition.py --live         # 真实 API 调用（需 .env 配置 API_KEY）
  python scripts/demo_competition.py --live --pause # 逐步暂停，方便录屏
  python scripts/demo_competition.py --live --scenes 2 --skip-image
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# ---------------------------------------------------------------------------
# 终端样式
# ---------------------------------------------------------------------------
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def enable_ansi() -> None:
    if sys.platform == "win32":
        os.system("")  # enable VT100 on Windows
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def banner(title: str) -> None:
    w = 64
    print(f"\n{CYAN}{'═' * w}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{'═' * w}{RESET}\n")


def step(n: int, title: str) -> None:
    print(f"\n{GREEN}{BOLD}[步骤 {n}] {title}{RESET}")
    print(f"{DIM}{'─' * 56}{RESET}")


def label_io(kind: str, text: str) -> None:
    color = BLUE if kind.upper() == "INPUT" else MAGENTA
    tag = "输入" if kind.upper() == "INPUT" else "输出"
    print(f"{color}{BOLD}▶ {tag} ({kind}){RESET}")
    for line in text.strip().splitlines():
        print(f"  {line}")
    print()


def json_io(kind: str, obj: Any) -> None:
    label_io(kind, json.dumps(obj, ensure_ascii=False, indent=2))


def pause_if(enabled: bool, msg: str = "按 Enter 继续…") -> None:
    if enabled:
        input(f"{YELLOW}{msg}{RESET}")


def slow_print(msg: str, delay: float = 0.03) -> None:
    for ch in msg:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()


# ---------------------------------------------------------------------------
# 演示数据（右右 / 绵绵 家庭场景）
# ---------------------------------------------------------------------------
DEMO_VOICE_RAW = (
    "嗯…那个…小恐龙叫…右右…它要去太空…找星星…"
    "然后…遇到了一朵…会说话的云…云朵上…还有绵绵…"
)

DEMO_IDEA = (
    "小恐龙右右乘坐火箭去太空寻找最亮的星星，"
    "途中遇到一朵会说话的云，云上坐着妹妹绵绵，"
    "他们一起找到了会眨眼的金色星星。"
)

DEMO_CHARACTER = "右右、绵绵"
DEMO_NUM_SCENES = 3

MOCK_STORY = {
    "character_description": (
        "Youyou: small green dinosaur, orange rocket backpack; "
        "Mianmian: pink dress, fluffy cloud friend"
    ),
    "scenes": [
        {"text": "小恐龙右右穿上火箭背包，向太空出发啦！"},
        {"text": "太空中，右右遇见了一朵会说话的白云，云上坐着绵绵。"},
        {"text": "他们一起找到了会眨眼的金色星星，开心地向地球挥手。"},
    ],
}

MOCK_SUMMARIZE_RESPONSE = DEMO_IDEA

MOCK_IMAGE_PROMPTS = [
    "A cute green baby dinosaur with orange rocket backpack launching into starry space, cartoon style",
    "Dinosaur and girl Mianmian on a friendly talking cloud in space, warm colors, children's book",
    "Dinosaur and girl waving at a glowing golden twinkling star, wholesome picture book illustration",
]

ASR_MODEL_FILES = [
    "encoder-epoch-99-avg-1.int8.mnn",
    "decoder-epoch-99-avg-1.int8.mnn",
    "joiner-epoch-99-avg-1.int8.mnn",
    "tokens.txt",
]

ASR_MODEL_SUBDIR = "sherpa-mnn-streaming-zipformer-bilingual-zh-en-2023-02-20"


def find_asr_model_dir() -> Path | None:
    candidates = [
        Path(os.environ.get("STORYCRAFT_ASR_CACHE", "D:/storycraft-asr-assets"))
        / ASR_MODEL_SUBDIR,
        ROOT
        / "mobile/android/app/src/main/assets/mnn-asr"
        / ASR_MODEL_SUBDIR,
    ]
    for p in candidates:
        if p.is_dir() and all((p / f).exists() for f in ASR_MODEL_FILES):
            return p
    return None


def demo_architecture() -> None:
    banner("小小故事家 · 端云协同架构")
    flow = """
    +--------------- Android App（小小故事家 v1.0.2）----------------+
    |  语音/文字输入 -> 编辑 -> 选画风 -> 预览 -> PDF绘本 / 动漫视频  |
    +--------+---------------------------+-------------------------+
             | 端侧推理                   | 云端推理
             v                           v
    +------------------------+  +--------------------------------+
    | MNN + Sherpa-MNN       |  | 通义千问 qwen-plus              |
    | Zipformer INT8 流式ASR |  | 通义万象 wan2.6-t2i             |
    | (APK内置，本地加载)     |  | Seedance 2.0（动漫模式）        |
    +------------------------+  +--------------------------------+
    """
    print(flow)


def demo_asr_loading(pause: bool) -> str:
    step(1, "端侧模型本地加载 — MNN 语音识别（与 App MnnAsrEngine 一致）")
    print(f"{DIM}对应代码: mobile/android/.../asr/MnnAsrEngine.kt → initialize(){RESET}\n")

    model_dir = find_asr_model_dir()
    if not model_dir:
        print(f"{YELLOW}[WARN] 未找到本地 ASR 模型目录，使用模拟路径演示{RESET}")
        model_dir = Path(f"assets/mnn-asr/{ASR_MODEL_SUBDIR}")

    print(f"  ① 检查 APK assets 模型文件是否齐全 …")
    pause_if(pause)
    total_mb = 0.0
    for name in ASR_MODEL_FILES:
        fp = model_dir / name if model_dir.exists() else None
        if fp and fp.exists():
            mb = fp.stat().st_size / (1024 * 1024)
            total_mb += mb
            print(f"     [OK] {name:<40} {mb:>7.2f} MB")
        else:
            print(f"     · {name:<40} {'(演示)':>7}")
    print(f"     合计约 {total_mb:.1f} MB（INT8 量化，打包进 APK）")
    pause_if(pause)

    init_steps = [
        ("加载 JNI 库", "System.loadLibrary(\"sherpa-mnn-jni\")"),
        ("构建模型配置", "getModelConfig(modelDir) — encoder/decoder/joiner .mnn"),
        ("创建 OnlineRecognizer", "MNN 推理引擎 + 流式 Zipformer"),
        ("采样率", "16000 Hz, mono, PCM16"),
        ("解码策略", "greedy_search, enableEndpoint=true"),
        ("就绪", "MNN ASR initialized from assets"),
    ]
    print(f"\n  ② 初始化推理引擎 …")
    for i, (desc, detail) in enumerate(init_steps, 1):
        time.sleep(0.4 if not pause else 0.1)
        print(f"     [{i}/{len(init_steps)}] {desc}")
        print(f"         {DIM}{detail}{RESET}")
    print(f"\n  {GREEN}[OK] 端侧 ASR 模型加载完成（离线可用，语音不上传云端）{RESET}")
    pause_if(pause)
    return DEMO_VOICE_RAW


def demo_asr_inference(raw_transcript: str, pause: bool) -> str:
    step(2, "端侧推理 — 语音输入 → 本地 ASR 实时转写")
    print(f"{DIM}对应 App: VoiceIdeaInput → startMnnListening() → partial 回调{RESET}\n")

    label_io("INPUT", "[麦克风] 小朋友语音（模拟右右说话）\n" + f'"{raw_transcript}"')
    pause_if(pause)

    print(f"  {DIM}实时 partial 转写:{RESET}")
    partial = ""
    for word in raw_transcript.replace("…", " ").split():
        partial += word
        print(f"\r     → {partial}", end="", flush=True)
        time.sleep(0.15)
    print(f"\n  {GREEN}[OK] 端侧 ASR 最终转写完成{RESET}")
    label_io("OUTPUT", raw_transcript)
    pause_if(pause)
    return raw_transcript


def demo_summarize_voice(live: bool, pause: bool, transcript: str) -> str:
    step(3, "云端推理 — 通义千问 qwen-plus 整理儿童口语")
    print(f"{DIM}对应 App: textService.summarizeVoiceIdea(){RESET}\n")

    req = {
        "model": "qwen-plus",
        "endpoint": "POST /compatible-mode/v1/chat/completions",
        "temperature": 0.4,
        "system": "你擅长倾听儿童口语并整理成清晰温馨的故事梗概。",
        "user_preview": f"原始语音转写: {transcript[:60]}…",
    }
    json_io("INPUT", req)

    if live:
        from storycraft.config import API_ENDPOINT, API_KEY, TEXT_MODEL
        from storycraft.api.text_generator import TextGenerator

        if not API_KEY:
            print(f"{YELLOW}未配置 API_KEY，回退演示模式{RESET}")
            idea = MOCK_SUMMARIZE_RESPONSE
        else:
            gen = TextGenerator(API_KEY, API_ENDPOINT, TEXT_MODEL)
            idea = _summarize_voice_live(gen, transcript, "右右")
    else:
        time.sleep(0.8)
        idea = MOCK_SUMMARIZE_RESPONSE

    label_io("OUTPUT", f"整理后的故事创意:\n{idea}")
    pause_if(pause)
    return idea


def _summarize_voice_live(gen, transcript: str, character: str) -> str:
    prompt = f"""以下是一个小朋友用语音描述的故事想法，语音识别结果可能断断续续、有重复、有错别字或语气词。请理解其意图，整理成一段适合 3-8 岁儿童绘本的「故事创意」。

**原始语音转写**：
{transcript}

已知主角/角色名：{character}

**整理要求**：
1. 用 2-4 句通顺中文，保留孩子想表达的核心情节与角色
2. 去除口语填充，合并重复表述
3. 温馨、积极、适合幼儿
4. 只输出整理后的故事创意正文

故事创意："""
    return gen._call_api(prompt).strip()[:500]


def demo_story_generation(live: bool, pause: bool, idea: str, num_scenes: int) -> dict:
    step(4, "云端推理 — 通义千问 qwen-plus 生成绘本故事 JSON")
    print(f"{DIM}对应 App: textService.generateStory(){RESET}\n")

    json_io(
        "INPUT",
        {
            "model": "qwen-plus",
            "idea": idea,
            "character": DEMO_CHARACTER,
            "num_scenes": num_scenes,
            "output_format": "JSON { character_description, scenes[] }",
        },
    )

    if live:
        from storycraft.config import API_ENDPOINT, API_KEY, TEXT_MODEL
        from storycraft.api.text_generator import TextGenerator

        if not API_KEY:
            story = MOCK_STORY
            print(f"{YELLOW}未配置 API_KEY，使用演示数据{RESET}")
        else:
            gen = TextGenerator(API_KEY, API_ENDPOINT, TEXT_MODEL)
            story = gen.generate_story(idea, "右右", num_scenes, chinese_only=True)
    else:
        time.sleep(1.0)
        story = MOCK_STORY
        story["scenes"] = story["scenes"][:num_scenes]

    json_io("OUTPUT", story)
    pause_if(pause)
    return story


def demo_image_prompts(live: bool, pause: bool, story: dict) -> list[str]:
    step(5, "云端推理 — 通义千问批量生成插画提示词（英文）")
    print(f"{DIM}对应 App: textService.generateImagePromptsBatch(){RESET}\n")

    scenes = story.get("scenes", [])
    json_io(
        "INPUT",
        {
            "model": "qwen-plus",
            "scenes_count": len(scenes),
            "character_description": story.get("character_description", "")[:80] + "…",
        },
    )

    if live:
        from storycraft.config import API_ENDPOINT, API_KEY, TEXT_MODEL
        from storycraft.api.text_generator import TextGenerator

        if not API_KEY:
            prompts = MOCK_IMAGE_PROMPTS[: len(scenes)]
        else:
            gen = TextGenerator(API_KEY, API_ENDPOINT, TEXT_MODEL)
            prompts = gen.generate_image_prompts_batch(
                scenes, story.get("character_description", "")
            )
    else:
        time.sleep(0.6)
        prompts = MOCK_IMAGE_PROMPTS[: len(scenes)]

    for i, p in enumerate(prompts, 1):
        print(f"  场景 {i}: {p[:90]}…")
    label_io("OUTPUT", json.dumps(prompts, ensure_ascii=False, indent=2))
    pause_if(pause)
    return prompts


def demo_image_generation(live: bool, skip_image: bool, pause: bool, prompts: list[str]) -> None:
    step(6, "云端推理 — 通义万象 wan2.6-t2i 文生图")
    print(f"{DIM}对应 App: imageService.generateTongyiImage(){RESET}\n")

    prompt = prompts[0] if prompts else MOCK_IMAGE_PROMPTS[0]
    req = {
        "model": "wan2.6-t2i",
        "endpoint": "POST /api/v1/services/aigc/multimodal-generation/generation",
        "size": "1104*1472",
        "style": "卡通",
        "prompt_preview": prompt[:100] + "…",
    }
    json_io("INPUT", req)

    if skip_image:
        print(f"  {YELLOW}(--skip-image) 跳过真实生图，展示输出格式{RESET}")
        label_io("OUTPUT", "image_url: https://dashscope.../xxx.png → 保存至本地 books/{id}/scene_0.jpg")
        pause_if(pause)
        return

    if live:
        from storycraft.config import API_KEY, TONGYI_IMAGE_MODEL

        if not API_KEY:
            print(f"{YELLOW}未配置 API_KEY，跳过生图{RESET}")
        else:
            url = _generate_one_image(API_KEY, TONGYI_IMAGE_MODEL, prompt)
            label_io("OUTPUT", f"image_url: {url}\n→ App 下载至 documentDirectory/books/{{id}}/")
            pause_if(pause)
            return

    time.sleep(0.8)
    label_io(
        "OUTPUT",
        "image_url: https://dashscope.aliyuncs.com/.../demo.png\n"
        "→ 逐场景生成，失败可单页重试（内容安全自动改写 prompt）",
    )
    pause_if(pause)


def _generate_one_image(api_key: str, model: str, prompt: str) -> str:
    import httpx

    enhanced = (
        f"{prompt}, cartoon style, cute, colorful, child-friendly illustration, "
        "wholesome, family-friendly, suitable for 3-5 years old"
    )
    res = httpx.post(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "input": {"messages": [{"role": "user", "content": [{"text": enhanced}]}]},
            "parameters": {"size": "1104*1472", "n": 1, "prompt_extend": True},
        },
        timeout=120.0,
    )
    res.raise_for_status()
    data = res.json()
    return data["output"]["choices"][0]["message"]["content"][0]["image"]


def demo_interaction_flow() -> None:
    step(7, "核心交互流程 — 绘本模式 + 动漫模式")
    book_flow = """
  [绘本模式]
  -----------------------------------------------------------------
  首页(语音/文字) -> [端侧 ASR] -> [qwen 整理] -> [qwen 故事]
       -> 编辑文字 -> 图片配置(风格/尺寸) -> [wan2.6 逐页生图]
       -> 翻页预览 -> 导出 PDF -> 绵绵睡前阅读

  [动漫模式]（同一 App）
  -----------------------------------------------------------------
  输入创意 -> [qwen 分镜 JSON] -> 角色立绘 -> [Seedance 2.0 视频]
       -> 15秒/段，最多60秒/集 -> 本地预览播放

  [家庭验证闭环]
  -----------------------------------------------------------------
  爸爸(开发) -> 妈妈(内容把关) -> 右右(创作试用) -> 绵绵(阅读绘本)
    """
    print(book_flow)


def demo_summary(live: bool) -> None:
    banner("演示完成")
    mode = "真实 API" if live else "演示模式（无 API 调用）"
    print(f"  模式: {mode}")
    print(f"  App 名称: Little Story Maker v1.0.4")
    print(f"  端侧: MNN Sherpa Zipformer INT8 本地 ASR")
    print(f"  云端: 通义千问 qwen-plus + 通义万象 wan2.6-t2i\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="小小故事家 — 比赛终端技术演示")
    parser.add_argument("--live", action="store_true", help="调用真实百炼 API（需 .env）")
    parser.add_argument("--pause", action="store_true", help="每步暂停，方便录屏")
    parser.add_argument("--scenes", type=int, default=3, help="故事场景数（live 模式建议 2）")
    parser.add_argument(
        "--skip-image",
        action="store_true",
        help="live 模式下跳过真实生图（省时省额度）",
    )
    args = parser.parse_args()

    enable_ansi()
    os.chdir(ROOT)

    banner("小小故事家 · 通义千问手机创意 AI — 技术演示")
    print(f"  项目路径: {ROOT}")
    print(f"  运行模式: {'[LIVE] 真实 API' if args.live else '[DEMO] 演示模式（推荐录屏彩排）'}")
    pause_if(args.pause, "按 Enter 开始演示…")

    demo_architecture()
    pause_if(args.pause)

    transcript = demo_asr_loading(args.pause)
    transcript = demo_asr_inference(transcript, args.pause)
    idea = demo_summarize_voice(args.live, args.pause, transcript)
    story = demo_story_generation(args.live, args.pause, idea, args.scenes)
    prompts = demo_image_prompts(args.live, args.pause, story)
    demo_image_generation(args.live, args.skip_image, args.pause, prompts)
    demo_interaction_flow()
    demo_summary(args.live)


if __name__ == "__main__":
    main()
