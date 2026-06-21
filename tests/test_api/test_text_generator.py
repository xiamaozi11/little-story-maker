import pytest
from storycraft.api.text_generator import TextGenerator
from storycraft.config import API_KEY, API_ENDPOINT, TEXT_MODEL

@pytest.fixture
def generator():
    return TextGenerator(
        api_key=API_KEY,
        api_endpoint=API_ENDPOINT,
        model=TEXT_MODEL
    )

def test_generate_story(generator):
    """测试生成完整故事"""
    theme = "animals"
    character = "小兔子"
    num_scenes = 3

    result = generator.generate_story(theme, character, num_scenes)

    assert "scenes" in result
    assert len(result["scenes"]) == num_scenes
    assert "text" in result["scenes"][0]
    assert "image_prompt" in result["scenes"][0]

def test_generate_story_with_invalid_theme(generator):
    """测试使用无效主题"""
    with pytest.raises(ValueError):
        generator.generate_story("", "小兔子", 3)

def test_validate_story_content(generator):
    """测试生成的故事内容适合3-5岁儿童"""
    result = generator.generate_story("animals", "小兔子", 3)

    # 检查句子长度（适合儿童）
    for scene in result["scenes"]:
        text = scene["text"]
        # 每个场景应该是1-2个简单句子
        assert len(text) < 100  # 长度限制
