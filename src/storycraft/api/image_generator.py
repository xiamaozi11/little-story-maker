import httpx
import os
from pathlib import Path
from typing import List
from PIL import Image
import io
from storycraft.core.logger import setup_logger

logger = setup_logger()

class ImageGenerator:
    """使用 AI 生成绘本插画，支持通义千问和豆包"""

    def __init__(self, api_key: str, output_dir: str = "output", style: str = "漫画风", service: str = "tongyi", session_dir: str = None, image_size: str = None):
        """
        Args:
            api_key: API密钥
            output_dir: 输出目录
            style: 图片风格
            service: 生图服务 (tongyi 或 doubao)
            session_dir: 会话目录（按时间创建的子目录）
            image_size: 图片尺寸 (WIDTHxHEIGHT 格式，如 "1024x1365")
        """
        from storycraft.config import IMAGE_SERVICE, ARK_API_KEY, ARK_BASE_URL, DOUBAO_IMAGE_MODEL, IMAGE_SIZE

        self.api_key = api_key
        self.base_output_dir = Path(output_dir)
        self.base_output_dir.mkdir(exist_ok=True)

        # 使用会话目录或默认目录
        if session_dir:
            self.output_dir = self.base_output_dir / session_dir
        else:
            self.output_dir = self.base_output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.style = style
        self.character_description = ""  # 角色固定描述，用于保持画面一致性
        self.service = service or IMAGE_SERVICE
        self.image_size = image_size or IMAGE_SIZE  # 图片尺寸配置

        # 豆包配置
        self.ark_api_key = ARK_API_KEY
        self.ark_base_url = ARK_BASE_URL
        self.doubao_model = DOUBAO_IMAGE_MODEL

        # HTTP客户端（通义千问用）
        self.client = httpx.Client(timeout=120.0)

        logger.info(f"初始化图片生成器，服务: {self.service}, 模型: {self.doubao_model if self.service == 'doubao' else 'wan2.6-t2i'}, 尺寸: {self.image_size}")

    def generate(self, prompt: str, scene_id: str) -> str:
        """生成单张图片"""
        logger.info(f"开始生成图片: {scene_id}")
        enhanced_prompt = self._enhance_prompt(prompt)
        image_data = self._call_api(enhanced_prompt)
        image_path = self._save_image(image_data, scene_id)
        logger.info(f"图片生成成功: {image_path}")
        return str(image_path)

    def generate_batch(self, prompts: List[str], character_description: str = "") -> List[str]:
        """批量生成图片

        Args:
            prompts: 图片提示词列表
            character_description: 角色固定描述，用于保持画面一致性
        """
        self.character_description = character_description  # 保存角色描述
        logger.info(f"开始批量生成 {len(prompts)} 张图片，服务: {self.service}")
        if character_description:
            logger.info(f"使用角色描述: {character_description[:50]}...")

        # 豆包支持组图生成，一次性生成多张关联图片
        if self.service == "doubao" and len(prompts) > 1:
            return self._generate_batch_doubao(prompts)

        # 通义千问或单张图片，使用串行生成
        return self._generate_batch_sequential(prompts)

    def _generate_batch_sequential(self, prompts: List[str]) -> List[str]:
        """串行生成图片（通义千问或单张图片）"""
        import time
        image_paths = []

        for idx, prompt in enumerate(prompts):
            scene_id = f"scene_{idx + 1}"

            # 添加延迟避免触发 API 限流（除了第一个请求）
            if idx > 0:
                delay = 3  # 每个请求之间等待3秒
                logger.info(f"等待 {delay} 秒后生成下一张图片（避免触发 API 限流）...")
                time.sleep(delay)

            try:
                path = self.generate(prompt, scene_id)
                image_paths.append(path)
            except Exception as e:
                logger.error(f"生成场景 {scene_id} 失败: {e}")
                # 使用占位图
                placeholder = self._create_placeholder(scene_id)
                image_paths.append(placeholder)

        return image_paths

    def _generate_batch_doubao(self, prompts: List[str]) -> List[str]:
        """使用豆包组图功能批量生成图片"""
        try:
            from volcenginesdkarkruntime import Ark

            # 初始化豆包客户端
            client = Ark(
                base_url=self.ark_base_url,
                api_key=self.ark_api_key
            )

            # 构建组合提示词（用换行符分隔多个场景）
            # 豆包会根据提示词中的场景标签自动生成多张图片
            combined_prompt = "\n".join([f"[Scene {i+1}] {p}" for i, p in enumerate(prompts)])
            enhanced_prompt = self._enhance_prompt(combined_prompt)

            logger.info(f"使用豆包组图生成，场景数: {len(prompts)}")

            # 调用豆包生图API
            # 注意：不传 n 参数，让豆包根据提示词自动识别场景数量
            response = client.images.generate(
                model=self.doubao_model,
                prompt=enhanced_prompt,
                size=self.image_size,  # 使用配置的尺寸，如 "1024x1365" (3:4 竖版)
                response_format="url",
                watermark=False,
                # 启用组图生成
                sequential_image_generation="auto"
            )

            # 豆包会返回多张图片的URL
            image_paths = []
            for idx, img_data in enumerate(response.data):
                scene_id = f"scene_{idx + 1}"
                try:
                    # 下载图片
                    img_url = img_data.url
                    logger.info(f"豆包生成图片 {idx + 1}/{len(response.data)}: {img_url[:50]}...")

                    img_response = self.client.get(img_url, timeout=60)
                    img_response.raise_for_status()

                    # 保存图片
                    image_path = self._save_image(img_response.content, scene_id)
                    image_paths.append(str(image_path))
                    logger.info(f"图片生成成功: {image_path}")

                except Exception as e:
                    logger.error(f"下载豆包图片 {scene_id} 失败: {e}")
                    placeholder = self._create_placeholder(scene_id)
                    image_paths.append(placeholder)

            # 如果豆包返回的图片数量不够，补充占位图
            while len(image_paths) < len(prompts):
                scene_id = f"scene_{len(image_paths) + 1}"
                logger.warning(f"豆包返回图片数量不足，添加占位图: {scene_id}")
                placeholder = self._create_placeholder(scene_id)
                image_paths.append(placeholder)

            return image_paths

        except ImportError:
            logger.error("未安装 volcengine-python-sdk，请运行: pip install 'volcengine-python-sdk[ark]'")
            # 回退到串行生成
            return self._generate_batch_sequential(prompts)
        except Exception as e:
            logger.error(f"豆包组图生成失败: {e}，回退到串行生成")
            # 回退到串行生成
            return self._generate_batch_sequential(prompts)

    def _enhance_prompt(self, prompt: str) -> str:
        """增强提示词以获得指定的图片风格和角色一致性"""
        from storycraft.config import IMAGE_STYLES

        # 获取用户选择的风格描述
        style_desc = IMAGE_STYLES.get(self.style, IMAGE_STYLES["漫画风"])

        # 基础增强（适用于所有风格）
        base_enhancements = [
            "children's book illustration style",
            "suitable for 3-5 years old",
            "simple and clear composition"
        ]

        # 构建提示词：场景提示词已含本场景角色外貌，勿再拼接全体角色描述
        parts = []
        parts.append(prompt)
        parts.append(style_desc)
        parts.extend(base_enhancements)
        parts.append("only depict characters mentioned in this scene")

        return ", ".join(parts)

    def _call_api(self, prompt: str) -> bytes:
        """调用通义千问 AI 图片生成 API

        支持的模型：wan2.6-t2i, qwen-image-v1 等
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 使用 wan2.6-t2i 模型（最新最强的模型，支持自定义尺寸）
        # 将尺寸格式转换为通义千问格式（用 * 分隔符）
        # 例如："1920x2560" -> "1920*2560"
        qwen_size = self.image_size.replace("x", "*") if self.image_size else "1024*1024"

        payload = {
            "model": "wan2.6-t2i",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "prompt_extend": True,
                "watermark": False,
                "n": 1,
                "size": qwen_size
            }
        }

        try:
            # 调用通义千问多模态 API
            logger.info(f"调用通义千问 API，尺寸: {qwen_size}")

            response = self.client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                headers=headers,
                json=payload,
                timeout=120
            )

            response.raise_for_status()
            data = response.json()

            # wan2.6-t2i 的响应格式：output.choices[0].message.content[0].image
            if data.get("output") and data["output"].get("choices"):
                choices = data["output"]["choices"]
                if len(choices) > 0 and choices[0].get("message", {}).get("content"):
                    content = choices[0]["message"]["content"]
                    if len(content) > 0 and content[0].get("image"):
                        image_url = content[0]["image"]

                        # 下载图片（带重试机制）
                        logger.info(f"成功调用 wan2.6-t2i API，图片URL: {image_url[:50]}...")

                        # 尝试下载图片，最多重试3次
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                # 逐次增加超时时间：60s -> 90s -> 120s
                                timeout = 60 + (attempt * 30)
                                img_response = self.client.get(image_url, timeout=timeout)
                                img_response.raise_for_status()

                                logger.info(f"图片下载成功（第{attempt + 1}次尝试），大小: {len(img_response.content)} bytes")
                                return img_response.content
                            except Exception as download_error:
                                if attempt < max_retries - 1:
                                    logger.warning(f"下载失败（第{attempt + 1}次尝试）: {str(download_error)[:100]}，重试中...")
                                else:
                                    raise download_error

            # 如果格式不对，抛出异常
            raise Exception(f"API响应格式不正确: {data}")

        except Exception as e:
            # 如果API调用失败，记录错误并返回占位图
            logger.error(f"AI图片生成失败 ({str(e)})，使用占位图")

            from PIL import Image, ImageDraw

            # 创建占位图，显示提示词信息
            img = Image.new('RGB', (1024, 1024), color='#F5F5DC')
            draw = ImageDraw.Draw(img)

            # 绘制边框
            draw.rectangle([50, 50, 974, 974], outline='#DEB887', width=10)

            # 添加说明文字
            title = "AI 图片提示词"
            draw.text((512, 300), title, fill='#8B4513', anchor='mm')

            # 显示提示词（自动换行）
            words = prompt
            lines = []
            current_line = ""
            for word in words.split():
                if len(current_line + word) < 30:
                    current_line += word + " "
                else:
                    lines.append(current_line)
                    current_line = word + " "
            lines.append(current_line)

            y_offset = 400
            for line in lines[:8]:  # 最多显示8行
                draw.text((512, y_offset), line.strip(), fill='#333333', anchor='mm')
                y_offset += 50

            # 添加提示
            draw.text((512, 850), "请使用AI绘画工具生成", fill='#666666', anchor='mm')
            draw.text((512, 900), "并根据此提示词创建插画", fill='#666666', anchor='mm')

            byte_arr = io.BytesIO()
            img.save(byte_arr, format='PNG')
            return byte_arr.getvalue()

    def _save_image(self, image_data: bytes, scene_id: str) -> Path:
        """保存图片到文件"""
        image_path = self.output_dir / f"{scene_id}.png"
        with open(image_path, 'wb') as f:
            f.write(image_data)
        return image_path

    def _create_placeholder(self, scene_id: str) -> str:
        """创建占位图片"""
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (1024, 1024), color='#F5F5DC')
        draw = ImageDraw.Draw(img)
        draw.text((512, 512), f"场景 {scene_id}", fill='black', anchor='mm')

        placeholder_path = self.output_dir / f"{scene_id}_placeholder.png"
        img.save(placeholder_path)
        return str(placeholder_path)

    def __del__(self):
        """清理 HTTP 客户端"""
        if hasattr(self, 'client'):
            self.client.close()
