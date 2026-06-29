#!/usr/bin/env python3
"""使用百炼万象 wan2.6-t2i 生成 Little Story Maker App 图标。"""
from __future__ import annotations

import os
import sys
from io import BytesIO
from pathlib import Path

import httpx
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "mobile" / "assets"
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

LOGO_PROMPT = (
    "Mobile app icon for a children's storybook creator app called Little Story Maker. "
    "Centered cute open picture book with sparkling magic stars and a small friendly pencil, "
    "warm orange and cream palette (#FF8C42, #FFF8F0), soft rounded square composition, "
    "flat kawaii illustration, clean simple shapes, no text, no watermark, "
    "high contrast readable at small size, professional app store icon style."
)


def generate_image(api_key: str, model: str, prompt: str, size: str = "1280*1280") -> bytes:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
        "parameters": {
            "prompt_extend": True,
            "watermark": False,
            "n": 1,
            "size": size,
        },
    }
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        image_url = data["output"]["choices"][0]["message"]["content"][0]["image"]
        img_resp = client.get(image_url, timeout=120.0)
        img_resp.raise_for_status()
        return img_resp.content


def make_icon(source: Image.Image, size: int) -> Image.Image:
    img = source.convert("RGBA")
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    return img


def make_splash(source: Image.Image, width: int, height: int) -> Image.Image:
    bg = Image.new("RGB", (width, height), "#FFF8F0")
    logo_size = min(width, height) // 2
    logo = make_icon(source, logo_size)
    x = (width - logo_size) // 2
    y = int(height * 0.32)
    bg.paste(logo, (x, y), logo)
    return bg


def save_assets(source: Image.Image) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    icon = make_icon(source, 1024)
    icon_rgb = Image.new("RGB", icon.size, "#FFF8F0")
    icon_rgb.paste(icon, mask=icon.split()[3] if icon.mode == "RGBA" else None)
    icon_rgb.save(ASSETS / "icon.png", optimize=True)
    icon.save(ASSETS / "adaptive-icon.png", optimize=True)
    splash = make_splash(source, 1284, 2778)
    splash.save(ASSETS / "splash.png", optimize=True)
    print(f"Saved: {ASSETS / 'icon.png'}")
    print(f"Saved: {ASSETS / 'adaptive-icon.png'}")
    print(f"Saved: {ASSETS / 'splash.png'}")


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("API_KEY", "").strip()
    model = os.getenv("TONGYI_IMAGE_MODEL", "wan2.6-t2i")
    if not api_key:
        print("ERROR: 请在 .env 中配置 API_KEY", file=sys.stderr)
        return 1

    print(f"Calling 百炼万象 ({model})...")
    raw = generate_image(api_key, model, LOGO_PROMPT)
    source = Image.open(BytesIO(raw))
    save_assets(source)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
