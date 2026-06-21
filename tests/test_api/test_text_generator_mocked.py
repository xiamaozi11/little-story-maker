import pytest
from unittest.mock import Mock, patch
from storycraft.api.text_generator import TextGenerator
from storycraft.config import API_KEY, API_ENDPOINT, TEXT_MODEL

@pytest.fixture
def generator():
    return TextGenerator(
        api_key=API_KEY,
        api_endpoint=API_ENDPOINT,
        model=TEXT_MODEL
    )

def test_generate_story_with_mock(generator):
    """测试生成完整故事（使用mock）"""
    theme = "animals"
    character = "小兔子"
    num_scenes = 3

    # Mock the API response
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": '''{
  "scenes": [
    {
      "text": "小兔子在草地上跳来跳去",
      "image_prompt": "A cute rabbit hopping on green grass"
    },
    {
      "text": "小兔子遇到了好朋友小松鼠",
      "image_prompt": "A cute rabbit meeting a friendly squirrel"
    },
    {
      "text": "他们一起开心地玩耍",
      "image_prompt": "Rabbit and squirrel playing together happily"
    }
  ]
}'''
            }
        }]
    }

    with patch.object(generator.client, 'post', return_value=mock_response):
        result = generator.generate_story(theme, character, num_scenes)

    assert "scenes" in result
    assert len(result["scenes"]) == num_scenes
    assert "text" in result["scenes"][0]
    assert "image_prompt" in result["scenes"][0]
    assert result["scenes"][0]["text"] == "小兔子在草地上跳来跳去"

def test_generate_story_with_invalid_theme(generator):
    """测试使用无效主题"""
    with pytest.raises(ValueError, match="主题和角色不能为空"):
        generator.generate_story("", "小兔子", 3)

    with pytest.raises(ValueError, match="主题和角色不能为空"):
        generator.generate_story("animals", "", 3)

def test_validate_story_content_with_mock(generator):
    """测试生成的故事内容适合3-5岁儿童（使用mock）"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": '''{
  "scenes": [
    {
      "text": "小兔子在草地上跳来跳去",
      "image_prompt": "A cute rabbit hopping on green grass"
    },
    {
      "text": "小兔子遇到了好朋友小松鼠",
      "image_prompt": "A cute rabbit meeting a friendly squirrel"
    },
    {
      "text": "他们一起开心地玩耍",
      "image_prompt": "Rabbit and squirrel playing together happily"
    }
  ]
}'''
            }
        }]
    }

    with patch.object(generator.client, 'post', return_value=mock_response):
        result = generator.generate_story("animals", "小兔子", 3)

    # 检查句子长度（适合儿童）
    for scene in result["scenes"]:
        text = scene["text"]
        # 每个场景应该是1-2个简单句子
        assert len(text) < 100  # 长度限制

def test_generate_story_with_invalid_scene_count(generator):
    """测试使用无效的场景数量"""
    with pytest.raises(ValueError, match="场景数量必须在 1-10 之间"):
        generator.generate_story("animals", "小兔子", 0)

    with pytest.raises(ValueError, match="场景数量必须在 1-10 之间"):
        generator.generate_story("animals", "小兔子", 11)

def test_parse_response_with_invalid_json(generator):
    """测试解析无效的JSON响应"""
    # 当API返回无效JSON时，应该返回默认场景
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": "This is not valid JSON"
            }
        }]
    }

    with patch.object(generator.client, 'post', return_value=mock_response):
        result = generator.generate_story("animals", "小兔子", 2)

    # 应该返回默认场景
    assert "scenes" in result
    assert len(result["scenes"]) == 2
    assert "场景 1" in result["scenes"][0]["text"]
    assert "场景 2" in result["scenes"][1]["text"]

def test_build_prompt(generator):
    """测试提示词构建"""
    prompt = generator._build_prompt("animals", "小兔子", 3)

    assert "小兔子" in prompt
    assert "3" in prompt
    assert "animals" not in prompt  # 应该使用主题描述而不是英文
    assert "关于可爱动物朋友的故事" in prompt
