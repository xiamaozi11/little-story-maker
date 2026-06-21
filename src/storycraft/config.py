import os
from dotenv import load_dotenv

load_dotenv()

# AI 服务配置
API_KEY = os.getenv("API_KEY", "")
API_ENDPOINT = os.getenv("API_ENDPOINT", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 文本生成配置
TEXT_MODEL = os.getenv("TEXT_MODEL", "qwen-plus")

# 图片生成服务选择
IMAGE_SERVICE = os.getenv("IMAGE_SERVICE", "doubao")  # tongyi 或 doubao，默认 doubao（支持组图生成）

# 豆包配置
ARK_API_KEY = os.getenv("ARK_API_KEY", "")
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
DOUBAO_IMAGE_MODEL = os.getenv("DOUBAO_IMAGE_MODEL", "doubao-seedream-4-5-251128")

# 通义千问配置（图片生成）
TONGYI_IMAGE_MODEL = os.getenv("TONGYI_IMAGE_MODEL", "wan2.6-t2i")

# 图片尺寸配置
# 两个服务都支持自定义尺寸 (WIDTHxHEIGHT 格式)
#
# 尺寸限制说明：
# - 豆包：要求至少 3,686,400 像素（如 1920x1920）
# - wan2.6-t2i：要求 1280×1280 到 1440×1440 之间，宽高比 1:4 到 4:1
#
# 兼容两个服务的尺寸（wan2.6-t2i 推荐）:
# - "1280x1280" (1:1 正方形，1.64M 像素) - 通义千问默认，豆包不满足最小要求
# - "1104x1472" (3:4 竖版，1.63M 像素) - 适合绘本，wan2.6-t2i 推荐
# - "960x1280" (3:4 竖版，1.23M 像素) - 通用竖版
#
# 仅豆包支持的大尺寸（wan2.6-t2i 不支持）:
# - "1920x2560" (3:4 竖版，4.9M 像素) - 豆包推荐，适合绘本
# - "2048x2730" (3:4 竖版，5.6M 像素) - 豆包高清
# - "2048x2048" (1:1 正方形，4.2M 像素) - 豆包正方形
IMAGE_SIZE = os.getenv("IMAGE_SIZE", "1104x1472")  # 默认 3:4 竖版（wan2.6-t2i 推荐）

# 应用配置
MAX_SCENES = 30
MIN_SCENES = 1
DEFAULT_SCENES = 10

# 图片风格配置
IMAGE_STYLES = {
    "漫画风": "manga style, black and white, ink drawing, outlines, monochrome, suitable for kindle e-reader",
    "动漫": "anime style, colorful, vibrant, cel shading, Japanese animation style",
    "中国风": "Chinese style painting, traditional Chinese art, ink wash, elegant, oriental aesthetics",
    "水墨画": "ink wash painting, watercolor style, soft brush strokes, minimalist, artistic",
    "古典": "classical painting style, renaissance art, oil painting texture, museum quality",
    "油画": "oil painting, thick brush strokes, textured canvas, rich colors, classical art",
    "水彩画": "watercolor painting, soft colors, gentle brush strokes, light and airy",
    "卡通": "cartoon style, cute, colorful, simple shapes, child-friendly illustration"
}
DEFAULT_IMAGE_STYLE = "卡通"

# PDF 配置
PDF_IMAGE_QUALITY = 85  # JPEG压缩质量 (1-100)，优先文件大小
PDF_MAX_IMAGE_DIMENSION = 1200  # 图片最大尺寸（宽度或高度）

# 输出配置
OUTPUT_DIR = "output"
FONT_SIZE = 24
PAGE_WIDTH = 600
PAGE_HEIGHT = 800
