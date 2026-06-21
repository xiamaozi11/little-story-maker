import pytest
import os
from pathlib import Path
from storycraft.api.text_generator import TextGenerator
from storycraft.api.image_generator import ImageGenerator
from storycraft.core.story_builder import StoryBuilder
from storycraft.core.pdf_generator import PDFGenerator

@pytest.mark.integration
def test_full_pipeline(tmp_path):
    """测试完整的绘本生成流程"""
    # 这个测试需要有效的 API key
    api_key = os.getenv("API_KEY")
    if not api_key:
        pytest.skip("需要 API_KEY 环境变量")

    # 1. 初始化组件
    text_gen = TextGenerator(
        api_key=api_key,
        api_endpoint=os.getenv("API_ENDPOINT"),
        model=os.getenv("TEXT_MODEL", "test-model")
    )
    img_gen = ImageGenerator(api_key=api_key, output_dir=str(tmp_path))
    story_builder = StoryBuilder(text_gen, img_gen)
    pdf_gen = PDFGenerator(output_dir=str(tmp_path))

    # 2. 生成故事
    story_data = story_builder.build("animals", "小兔子", 3)

    assert len(story_data["scenes"]) == 3
    assert story_builder.validate_scenes(story_data["scenes"])

    # 3. 生成 PDF
    pdf_path = pdf_gen.generate(
        story_data["scenes"],
        title="小兔子的冒险",
        author="测试"
    )

    assert os.path.exists(pdf_path)
    assert pdf_gen.validate_pdf(pdf_path)

    # 清理
    for scene in story_data["scenes"]:
        if os.path.exists(scene["image_path"]):
            os.remove(scene["image_path"])
    os.remove(pdf_path)

@pytest.mark.integration
def test_error_handling():
    """测试错误处理"""
    # 使用无效的 API key
    text_gen = TextGenerator(
        api_key="invalid_key",
        api_endpoint="https://invalid.api.com",
        model="test-model"
    )

    with pytest.raises(Exception):
        text_gen.generate_story("animals", "小兔子", 3)
