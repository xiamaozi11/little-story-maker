import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
from storycraft.core.story_builder import StoryBuilder


@pytest.fixture
def mock_text_generator():
    """Mock text generator"""
    mock = Mock()
    return mock


@pytest.fixture
def mock_image_generator():
    """Mock image generator"""
    mock = Mock()
    return mock


@pytest.fixture
def story_builder(mock_text_generator, mock_image_generator):
    """Create story builder with mocked dependencies"""
    return StoryBuilder(mock_text_generator, mock_image_generator)


@pytest.fixture
def sample_scenes():
    """Sample scene data"""
    return [
        {
            "text": "从前有一只小兔子",
            "image_prompt": "A cute little rabbit in a meadow"
        },
        {
            "text": "小兔子找到了一个大胡萝卜",
            "image_prompt": "Rabbit holding a big carrot"
        }
    ]


@pytest.fixture
def sample_image_paths(tmp_path):
    """Create temporary image files"""
    paths = []
    for i in range(2):
        img_path = tmp_path / f"scene_{i+1}.png"
        # Create a minimal valid PNG file
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='white')
        img.save(img_path)
        paths.append(str(img_path))
    return paths


class TestStoryBuilderBuild:
    """Test StoryBuilder.build method"""

    def test_build_returns_complete_story(self, story_builder, mock_text_generator,
                                        mock_image_generator, sample_scenes, sample_image_paths):
        """Test that build combines text and images correctly"""
        # Setup mocks
        mock_text_generator.generate_story.return_value = {"scenes": sample_scenes}
        mock_image_generator.generate_batch.return_value = sample_image_paths

        # Execute
        result = story_builder.build("animals", "小白兔", 2)

        # Verify
        assert "scenes" in result
        assert len(result["scenes"]) == 2

        # Check first scene
        scene1 = result["scenes"][0]
        assert scene1["scene_number"] == 1
        assert scene1["text"] == sample_scenes[0]["text"]
        assert scene1["image_path"] == sample_image_paths[0]

        # Check second scene
        scene2 = result["scenes"][1]
        assert scene2["scene_number"] == 2
        assert scene2["text"] == sample_scenes[1]["text"]
        assert scene2["image_path"] == sample_image_paths[1]

    def test_build_calls_text_generator_correctly(self, story_builder, mock_text_generator,
                                                 mock_image_generator, sample_scenes, sample_image_paths):
        """Test that build calls text generator with correct parameters"""
        mock_text_generator.generate_story.return_value = {"scenes": sample_scenes}
        mock_image_generator.generate_batch.return_value = sample_image_paths

        story_builder.build("growth", "小明", 3)

        mock_text_generator.generate_story.assert_called_once_with("growth", "小明", 3)

    def test_build_calls_image_generator_correctly(self, story_builder, mock_text_generator,
                                                  mock_image_generator, sample_scenes, sample_image_paths):
        """Test that build calls image generator with correct prompts"""
        mock_text_generator.generate_story.return_value = {"scenes": sample_scenes}
        mock_image_generator.generate_batch.return_value = sample_image_paths

        story_builder.build("daily_life", "小红", 2)

        expected_prompts = [
            "A cute little rabbit in a meadow",
            "Rabbit holding a big carrot"
        ]
        mock_image_generator.generate_batch.assert_called_once_with(expected_prompts)


class TestStoryBuilderValidateScenes:
    """Test StoryBuilder.validate_scenes method"""

    def test_validate_scenes_with_valid_data(self, story_builder, sample_image_paths):
        """Test validation with valid scene data"""
        scenes = [
            {
                "text": "场景1",
                "image_path": sample_image_paths[0]
            },
            {
                "text": "场景2",
                "image_path": sample_image_paths[1]
            }
        ]

        assert story_builder.validate_scenes(scenes) is True

    def test_validate_scenes_missing_text(self, story_builder, sample_image_paths):
        """Test validation fails when text is missing"""
        scenes = [
            {
                "image_path": sample_image_paths[0]
            }
        ]

        assert story_builder.validate_scenes(scenes) is False

    def test_validate_scenes_missing_image_path(self, story_builder):
        """Test validation fails when image_path is missing"""
        scenes = [
            {
                "text": "场景1"
            }
        ]

        assert story_builder.validate_scenes(scenes) is False

    def test_validate_scenes_nonexistent_image(self, story_builder):
        """Test validation fails when image file doesn't exist"""
        scenes = [
            {
                "text": "场景1",
                "image_path": "/nonexistent/path/image.png"
            }
        ]

        assert story_builder.validate_scenes(scenes) is False

    def test_validate_scenes_empty_list(self, story_builder):
        """Test validation with empty scene list"""
        assert story_builder.validate_scenes([]) is True
