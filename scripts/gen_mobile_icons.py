"""生成移动端占位图标。"""
from pathlib import Path

from PIL import Image, ImageDraw

assets = Path(__file__).parent.parent / "mobile" / "assets"
assets.mkdir(parents=True, exist_ok=True)

for name, w, h in [
    ("icon.png", 1024, 1024),
    ("adaptive-icon.png", 1024, 1024),
    ("splash.png", 1284, 2778),
]:
    img = Image.new("RGB", (w, h), "#FFF8F0")
    draw = ImageDraw.Draw(img)
    draw.ellipse([w // 4, h // 4, 3 * w // 4, 3 * h // 4], fill="#FF8C42")
    draw.text((w // 2 - 60, h // 2 - 20), "Story", fill="white")
    img.save(assets / name)
    print(f"created {name}")
