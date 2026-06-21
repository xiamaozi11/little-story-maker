from typing import Dict, List
from pathlib import Path
from datetime import datetime
from storycraft.api.text_generator import TextGenerator
from storycraft.api.image_generator import ImageGenerator
from storycraft.core.logger import setup_logger

logger = setup_logger()

class StoryBuilder:
    """组合文本生成和图片生成,构建完整故事"""

    def __init__(self, text_generator: TextGenerator, image_generator: ImageGenerator):
        self.text_generator = text_generator
        self.image_generator = image_generator

    def build(self, idea: str, character: str, num_scenes: int) -> Dict:
        """构建完整故事"""
        # 创建会话目录（按日期时间和主角名）
        from storycraft.config import OUTPUT_DIR
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 清理主角名作为文件夹名（移除特殊字符）
        safe_character = "".join(c for c in character if c.isalnum() or c in "_-")
        session_dir = f"{timestamp}_{safe_character}"

        # 更新 image_generator 的输出目录
        self.image_generator.output_dir = Path(OUTPUT_DIR) / session_dir
        self.image_generator.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"创建会话目录: {session_dir}")

        # 1. 生成故事文本
        story_data = self.text_generator.generate_story(idea, character, num_scenes)
        scenes = story_data["scenes"]
        character_description = story_data.get("character_description", "")

        # 2. 为每个场景生成图片（传入角色描述以保持一致性）
        image_prompts = [scene["image_prompt"] for scene in scenes]
        image_paths = self.image_generator.generate_batch(image_prompts, character_description)

        # 3. 组合文本和图片
        complete_scenes = [
            {
                "scene_number": idx + 1,
                "text": scene["text"],
                "image_prompt": scene["image_prompt"],
                "image_path": img_path
            }
            for idx, (scene, img_path) in enumerate(zip(scenes, image_paths))
        ]

        # 4. 保存故事和提示词到 txt 文件
        self._save_story_to_file(
            output_dir=self.image_generator.output_dir,
            idea=idea,
            character=character,
            character_description=character_description,
            scenes=complete_scenes,
            image_style=self.image_generator.style,
            image_service=self.image_generator.service
        )

        return {
            "scenes": complete_scenes,
            "session_dir": session_dir  # 返回会话目录供 PDF 生成器使用
        }

    def _save_story_to_file(self, output_dir: Path, idea: str, character: str,
                           character_description: str, scenes: List[Dict],
                           image_style: str, image_service: str) -> None:
        """保存故事和提示词到 txt 文件

        Args:
            output_dir: 输出目录
            idea: 故事创意/点子
            character: 主角名字
            character_description: 角色外貌描述
            scenes: 场景列表
            image_style: 图片风格
            image_service: 图片生成服务
        """
        try:
            story_file = output_dir / "story.txt"

            content = f"""{'='*60}
Kindle 儿童绘本故事记录
{'='*60}

📝 故事信息
{'─'*60}
故事创意：{idea}
主角名字：{character}
场景数量：{len(scenes)}
生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🎨 图片配置
{'─'*60}
图片服务：{'豆包 (Doubao)' if image_service == 'doubao' else '通义千问 (Tongyi)'}
图片风格：{image_style}

👤 角色描述
{'─'*60}
{character_description if character_description else '（无角色描述）'}

📖 故事场景
{'─'*60}
"""

            for idx, scene in enumerate(scenes, 1):
                content += f"""
【场景 {idx}】

📄 故事文本：
{scene['text']}

📄 English Text:
{scene.get('text_en', '(N/A)')}

🖼️ 图片文件：
{Path(scene['image_path']).name}

{'─'*40}
"""

            content += f"""
{'='*60}
文件结束
{'='*60}
"""

            # 写入文件
            with open(story_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"故事已保存到: {story_file}")

        except Exception as e:
            logger.error(f"保存故事文件失败: {e}")

    def validate_scenes(self, scenes: List[Dict]) -> bool:
        """验证场景数据完整性"""
        required_fields = ["text", "image_path"]

        for scene in scenes:
            if not all(field in scene for field in required_fields):
                return False
            if not Path(scene["image_path"]).exists():
                return False
        return True
