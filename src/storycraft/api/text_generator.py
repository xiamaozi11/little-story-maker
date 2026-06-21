import httpx
import json
from typing import Dict, List
from storycraft.core.logger import setup_logger

logger = setup_logger()

class TextGenerator:
    """使用豆包/通义千问生成儿童故事"""

    def __init__(self, api_key: str, api_endpoint: str, model: str):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.model = model
        self.client = httpx.Client(timeout=60.0)

    def generate_story(self, idea: str, character: str, num_scenes: int, chinese_only: bool = False) -> Dict:
        """生成故事

        Args:
            idea: 故事点子/创意描述（用户输入的故事想法）
            character: 主角名字
            num_scenes: 场景数量
            chinese_only: 是否只生成中文（不生成英文翻译）

        Returns:
            包含场景列表和角色描述的字典
        """
        logger.info(f"开始生成故事: idea={idea[:50]}..., character={character}, num_scenes={num_scenes}, chinese_only={chinese_only}")

        if not idea or not character:
            raise ValueError("故事点子和主角名字不能为空")

        if num_scenes < 1 or num_scenes > 30:
            raise ValueError("场景数量必须在 1-30 之间")

        prompt = self._build_prompt(idea, character, num_scenes, chinese_only)
        logger.info(f"已构建提示词")

        response = self._call_api(prompt)
        logger.info(f"AI API 调用成功")

        result = self._parse_response(response, num_scenes)
        logger.info(f"成功解析 {len(result['scenes'])} 个场景")

        return result

    def _build_prompt(self, idea: str, character: str, num_scenes: int, chinese_only: bool = False) -> str:
        """构建 AI 提示词"""
        if chinese_only:
            # 只生成中文故事，不生成图片提示词
            prompt = f"""请为3-5岁的儿童创作一个绘本故事（仅中文版本）。

故事创意：{idea}
主要角色：{character}（可为一名或多名角色，用顿号/逗号分隔）
场景数量：{num_scenes}个场景

要求：
1. 基于用户提供的"故事创意"展开完整故事
2. 语言简单易懂，适合3-5岁儿童理解
3. 有重复性元素，方便儿童记忆
4. 每个场景1-2句话，情节清晰；每个场景只描写该场景实际出场的角色
5. 充满温馨和正能量
6. 故事要有起承转合，逻辑连贯

**角色设定（重要）**：
- character_description 是全体角色的外貌设定库（英文），供后续插画参考
- 若有多名角色，请逐条列出，格式如："Rabbit Duoduo: white fur, pink dress; Squirrel Tiaotiao: brown tail, red vest; ..."
- 各角色外貌在全书中保持一致，但不必每个场景都出场

请按照以下 JSON 格式输出（不要包含其他文字）：
{{
  "character_description": "全体角色的固定外貌特征（英文），每名角色单独一条",
  "scenes": [
    {{
      "text": "场景的文字描述（中文）"
    }}
  ]
}}"""
        else:
            # 生成中英文双语版本（包含图片提示词）
            prompt = f"""请为3-5岁的儿童创作一个绘本故事（中英文双语版本）。

故事创意：{idea}
主要角色：{character}（可为一名或多名角色，用顿号/逗号分隔）
场景数量：{num_scenes}个场景

要求：
1. 基于用户提供的"故事创意"展开完整故事
2. 语言简单易懂，适合3-5岁儿童理解
3. 有重复性元素，方便儿童记忆
4. 每个场景1-2句话，情节清晰；每个场景只描写该场景实际出场的角色
5. 充满温馨和正能量
6. 故事要有起承转合，逻辑连贯
7. **重要**：每个场景需要提供中英文双语版本

**角色与图片要求（重要）**：
- character_description 是全体角色的外貌设定库（英文），每名角色单独描述外貌
- 各角色在全书中外貌保持一致，但不必每个场景都出场
- 每个场景的 image_prompt 只描述该场景出场的角色，未出场角色不要画入画面
- 场景之间保持画面风格统一

请按照以下 JSON 格式输出（不要包含其他文字）：
{{
  "character_description": "全体角色的固定外貌特征（英文），每名角色单独一条",
  "scenes": [
    {{
      "text": "场景的文字描述（中文）",
      "text_en": "The scene description in English, simple and easy for children to understand",
      "image_prompt": "适合AI绘画的场景详细描述（英文），只包含本场景出场角色及其固定外貌，描述动作、表情、场景、构图等"
    }}
  ]
}}"""

        return prompt

    def _call_api(self, prompt: str) -> str:
        """调用 AI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的儿童绘本作家,擅长创作温馨、简单、富有教育意义的故事。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.8
        }

        response = self.client.post(
            f"{self.api_endpoint}/chat/completions",
            headers=headers,
            json=payload
        )

        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    def _parse_response(self, response: str, num_scenes: int) -> Dict:
        """解析 API 响应"""
        try:
            # 尝试提取 JSON
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]

            data = json.loads(json_str)
            scenes = data.get("scenes", [])
            character_description = data.get("character_description", "")

            if len(scenes) != num_scenes:
                # 如果场景数量不对，进行调整
                scenes = scenes[:num_scenes]

            return {
                "scenes": scenes,
                "character_description": character_description
            }

        except (json.JSONDecodeError, KeyError) as e:
            # 如果解析失败，返回默认场景
            logger.error(f"解析响应失败: {e}")
            return {
                "scenes": [
                    {
                        "text": f"场景 {i+1}",
                        "image_prompt": f"Scene {i+1} for children's book"
                    }
                    for i in range(num_scenes)
                ],
                "character_description": ""
            }

    def translate_scene(self, text: str) -> str:
        """翻译单个场景的文本为英文

        Args:
            text: 中文场景文本

        Returns:
            英文翻译
        """
        prompt = f"""请将以下儿童绘本的中文场景文本翻译成英文。

原文：{text}

要求：
1. 保持简单易懂，适合3-5岁儿童理解
2. 保持温馨和友好的语气
3. 不要改变原意，只做语言转换
4. 直接输出翻译结果，不要包含其他文字

英文翻译："""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的儿童文学翻译，擅长将中文故事翻译成简单易懂的英文。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3
        }

        response = self.client.post(
            f"{self.api_endpoint}/chat/completions",
            headers=headers,
            json=payload
        )

        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    def translate_scenes_batch(self, scenes: list) -> list:
        """批量翻译场景文本为英文

        Args:
            scenes: 场景列表，每个场景包含 'text' 字段

        Returns:
            英文翻译列表，与输入scenes顺序一致
        """
        # 构建批量翻译请求
        scenes_text = "\n".join([f"{idx+1}. {scene['text']}" for idx, scene in enumerate(scenes)])

        prompt = f"""请将以下儿童绘本的中文场景文本批量翻译成英文。

原文：
{scenes_text}

要求：
1. 保持简单易懂，适合3-5岁儿童理解
2. 保持温馨和友好的语气
3. 不要改变原意，只做语言转换
4. 按照原文顺序，每一行输出一个翻译结果
5. 只输出翻译结果，不要包含序号或其他文字

英文翻译："""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的儿童文学翻译，擅长将中文故事翻译成简单易懂的英文。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3
        }

        response = self.client.post(
            f"{self.api_endpoint}/chat/completions",
            headers=headers,
            json=payload
        )

        response.raise_for_status()
        data = response.json()

        # 解析批量翻译结果
        translations_text = data["choices"][0]["message"]["content"].strip()
        translations = [line.strip() for line in translations_text.split('\n') if line.strip()]

        # 确保翻译数量匹配，否则降级为逐个翻译
        if len(translations) != len(scenes):
            logger.warning(f"翻译数量({len(translations)})与场景数量({len(scenes)})不匹配，使用逐个翻译")
            return [self.translate_scene(scene['text']) for scene in scenes]

        return translations

    def generate_image_prompts_batch(self, scenes: list, character_description: str = "") -> list:
        """根据中文故事批量生成图片提示词

        Args:
            scenes: 场景列表，每个场景包含 'text' 字段
            character_description: 角色外貌描述，用于保持角色一致性

        Returns:
            图片提示词列表，与输入scenes顺序一致
        """
        # 构建批量请求
        scenes_text = "\n".join([f"{idx+1}. {scene['text']}" for idx, scene in enumerate(scenes)])

        character_desc_note = f"\n\n**角色外貌设定库（仅供参考，勿全部画进每个场景）**：\n{character_description}" if character_description else ""

        prompt = f"""请为以下儿童绘本故事场景批量生成AI绘画提示词（英文）。

原文：
{scenes_text}
{character_desc_note}

要求：
1. 提示词必须是英文
2. 每个场景的提示词要详细描述画面内容、角色动作、表情、场景、构图、光线等
3. **只画本场景原文中出现的角色**；未出场的角色不要出现在画面中
4. 若提供了角色外貌设定库，仅引用本场景出场角色的外貌，并保持与设定库一致
5. **角色称呼须保留外貌/物种前缀**：若原文或角色设定中角色全称为「小兔子朵朵」「小熊乐乐」等（外貌/物种 + 名字），英文提示词中每次提及该角色时都必须带上此前缀，不可只写名字。例如「小兔子朵朵」应写为 "little rabbit Duoduo"，不可只写 "Duoduo"
6. 画面风格要统一，适合儿童绘本
7. 温馨、明亮、色彩丰富
8. 按照原文顺序，每一行输出一个英文提示词
9. 只输出英文提示词，不要包含序号或其他文字

英文提示词："""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的儿童绘本插画设计师，擅长为儿童故事创作温馨、生动的AI绘画提示词。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }

        response = self.client.post(
            f"{self.api_endpoint}/chat/completions",
            headers=headers,
            json=payload
        )

        response.raise_for_status()
        data = response.json()

        # 解析批量提示词结果
        prompts_text = data["choices"][0]["message"]["content"].strip()
        image_prompts = [line.strip() for line in prompts_text.split('\n') if line.strip()]

        # 确保提示词数量匹配
        if len(image_prompts) != len(scenes):
            logger.warning(f"提示词数量({len(image_prompts)})与场景数量({len(scenes)})不匹配，使用逐个生成")
            # 降级为逐个生成
            return [self._generate_single_image_prompt(scene['text'], character_description) for scene in scenes]

        return image_prompts

    def _generate_single_image_prompt(self, text: str, character_description: str = "") -> str:
        """为单个场景生成图片提示词

        Args:
            text: 中文场景文本
            character_description: 角色外貌描述

        Returns:
            英文图片提示词
        """
        char_desc = f"\n\n**角色外貌设定库（仅供参考，勿全部画进每个场景）**：\n{character_description}" if character_description else ""

        prompt = f"""请为以下儿童绘本场景生成AI绘画提示词（英文）。

场景内容：{text}
{char_desc}

要求：
1. 提示词必须是英文
2. 详细描述画面内容、角色动作、表情、场景、构图、光线等
3. **只画本场景原文中出现的角色**；未出场的角色不要出现在画面中
4. 若提供了角色外貌设定库，仅引用本场景出场角色的外貌，并保持与设定库一致
5. 画面风格要适合儿童绘本，温馨、明亮、色彩丰富
6. 直接输出英文提示词，不要包含其他文字

英文提示词："""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的儿童绘本插画设计师，擅长为儿童故事创作温馨、生动的AI绘画提示词。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }

        response = self.client.post(
            f"{self.api_endpoint}/chat/completions",
            headers=headers,
            json=payload
        )

        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    def generate_anime_storyboard(
        self, idea: str, character: str, num_segments: int = 2
    ) -> Dict:
        """根据故事梗概生成动漫分镜剧本。

        每段 15 秒（5 镜头），num_segments 指定生成几段短视频（1~4 段，共 15~60 秒）。
        """
        shots_per_segment = 5
        segment_duration = 15
        num_segments = max(1, min(4, num_segments))
        target_shots = num_segments * shots_per_segment
        total_duration = num_segments * segment_duration

        prompt = f"""请为3-8岁儿童创作动漫短视频分镜剧本。

故事创意：{idea}
主要角色：{character}（可为多名，用顿号/逗号分隔）

**本次视频规划（必须严格遵守，不可增减）**：
- 用户选择生成 {num_segments} 段短视频，每段 15 秒，总时长 {total_duration} 秒
- scripts 数组长度必须为 1，只输出一个完整剧本
- 该剧本 shots 数组长度必须恰好为 {target_shots} 个（{num_segments} 段 × 每段 5 镜头）
- 镜头 1~5 为第 1 段，镜头 6~10 为第 2 段，以此类推；每镜头约 3 秒
- 每段内部 5 个镜头动作连贯、情绪递进；段与段之间自然衔接（下一段承接上一段结尾画面）
- 全 {num_segments} 段构成完整起承转合，适合儿童观看
- 禁止输出超过或少于 {target_shots} 个镜头

**角色设定**：
- characters 列出主要人物（2~4 名），含外貌与性格
- character_description 为全体角色英文外貌库，供后续生图参考

**镜头要求**：
- 每个镜头写清画面动作、景别（特写/中景/全景）、情绪
- video_prompt 为英文，描述该镜头动画画面，适合 AI 视频生成
- 镜头之间动作连贯，适合 15 秒一段的流畅动漫短片

请只输出 JSON（无其他文字）：
{{
  "synopsis": "故事梗概（中文，2-3句）",
  "character_description": "全体角色英文外貌设定",
  "characters": [
    {{
      "name": "角色中文名",
      "description": "外貌与性格（中文）",
      "image_prompt": "角色立绘参考图英文提示词，动漫风格，全身或半身，纯色背景"
    }}
  ],
  "scripts": [
    {{
      "title": "剧本标题",
      "synopsis": "本集梗概（中文）",
      "shots": [
        {{
          "text": "镜头中文描述",
          "video_prompt": "镜头英文动画画面描述"
        }}
      ]
    }}
  ]
}}"""

        response = self._call_api(prompt)
        return self._parse_anime_storyboard(
            response, target_shots, shots_per_segment, num_segments
        )

    def _parse_anime_storyboard(
        self,
        response: str,
        target_shots: int,
        shots_per_segment: int,
        num_segments: int,
    ) -> Dict:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            data = json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析动漫分镜失败: {e}")
            return {
                "synopsis": "",
                "character_description": "",
                "characters": [],
                "scripts": [],
                "num_segments": num_segments,
            }

        scripts = []
        raw_scripts = data.get("scripts", [])
        primary = raw_scripts[0] if raw_scripts else {}
        shots = (primary.get("shots") or [])[:target_shots]
        valid_count = (len(shots) // shots_per_segment) * shots_per_segment
        if valid_count >= shots_per_segment:
            scripts.append(
                {
                    "title": primary.get("title", "未命名"),
                    "synopsis": primary.get("synopsis", ""),
                    "shots": shots[:valid_count],
                }
            )

        if not scripts:
            scripts = [
                {
                    "title": "第一集",
                    "synopsis": data.get("synopsis", ""),
                    "shots": [
                        {
                            "text": f"镜头 {i + 1}",
                            "video_prompt": f"Anime shot {i + 1}, child-friendly",
                        }
                        for i in range(target_shots)
                    ],
                }
            ]

        return {
            "synopsis": data.get("synopsis", ""),
            "character_description": data.get("character_description", ""),
            "characters": data.get("characters", []),
            "scripts": scripts,
            "num_segments": num_segments,
        }

    def __del__(self):
        """清理 HTTP 客户端"""
        if hasattr(self, 'client'):
            self.client.close()
