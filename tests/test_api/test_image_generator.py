import pytest
import os
from PIL import Image
from storycraft.api.image_generator import ImageGenerator
from storycraft.config import API_KEY

@pytest.fixture
def generator():
    return ImageGenerator(api_key=API_KEY)

def test_generate_image(generator):
    """测试生成单张图片"""
    prompt = "A cute rabbit playing in a sunny garden, children's book illustration style"

    image_path = generator.generate(prompt, "test_scene_1")

    assert os.path.exists(image_path)
    # 验证是有效的图片文件
    with Image.open(image_path) as img:
        assert img.size[0] > 0
        assert img.size[1] > 0

    # 清理
    os.remove(image_path)

def test_generate_multiple_images(generator):
    """测试生成多张图片"""
    prompts = [
        "Scene 1: rabbit in garden",
        "Scene 2: rabbit with friends"
    ]

    image_paths = generator.generate_batch(prompts)

    assert len(image_paths) == 2
    for path in image_paths:
        assert os.path.exists(path)

    # 清理
    for path in image_paths:
        os.remove(path)

def test_image_dimensions(generator):
    """测试生成的图片尺寸符合要求"""
    prompt = "A simple test image"

    image_path = generator.generate(prompt, "test_dim")

    with Image.open(image_path) as img:
        # 检查图片尺寸合理
        assert img.size[0] >= 512  # 最小宽度
        assert img.size[1] >= 512  # 最小高度

    os.remove(image_path)
