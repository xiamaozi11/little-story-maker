import { AppSettings } from './settings';

export interface StoryResult {
  scenes: { text: string; text_en?: string; image_prompt?: string }[];
  character_description: string;
}

async function chatCompletion(
  settings: AppSettings,
  system: string,
  user: string,
  temperature = 0.8
): Promise<string> {
  const res = await fetch(`${settings.apiEndpoint}/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${settings.apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: settings.textModel,
      messages: [
        { role: 'system', content: system },
        { role: 'user', content: user },
      ],
      temperature,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`文本 API 失败 (${res.status}): ${err.slice(0, 200)}`);
  }

  const data = await res.json();
  return data.choices[0].message.content as string;
}

function buildStoryPrompt(
  idea: string,
  character: string,
  numScenes: number
): string {
  return `请为3-5岁的儿童创作一个绘本故事（仅中文版本）。

故事创意：${idea}
主要角色：${character}（可为一名或多名角色，用顿号/逗号分隔）
场景数量：${numScenes}个场景

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
{
  "character_description": "全体角色的固定外貌特征（英文），每名角色单独一条",
  "scenes": [
    {
      "text": "场景的文字描述（中文）"
    }
  ]
}`;
}

const IMAGE_PROMPT_CHAR_NOTE = (characterDescription: string) =>
  characterDescription
    ? `\n\n**角色外貌设定库（仅供参考，勿全部画进每个场景）**：\n${characterDescription}`
    : '';

const IMAGE_PROMPT_SCENE_RULES = `要求：
1. 提示词必须是英文
2. 每个场景的提示词要详细描述画面内容、角色动作、表情、场景、构图、光线等
3. **只画本场景原文中出现的角色**；未出场的角色不要出现在画面中
4. 若提供了角色外貌设定库，仅引用本场景出场角色的外貌，并保持与设定库一致
5. 画面风格要统一，适合3-5岁儿童绘本，温馨、明亮、色彩柔和
6. **内容安全**：避免暴力、武器、恐怖、血腥、成人元素；用可爱卡通风格描述`;

function parseStoryResponse(
  response: string,
  numScenes: number
): StoryResult {
  try {
    const start = response.indexOf('{');
    const end = response.lastIndexOf('}') + 1;
    const data = JSON.parse(response.slice(start, end)) as StoryResult;
    const scenes = (data.scenes ?? []).slice(0, numScenes);
    return {
      scenes,
      character_description: data.character_description ?? '',
    };
  } catch {
    return {
      scenes: Array.from({ length: numScenes }, (_, i) => ({
        text: `场景 ${i + 1}`,
      })),
      character_description: '',
    };
  }
}

export async function generateStory(
  settings: AppSettings,
  idea: string,
  character: string,
  numScenes: number
): Promise<StoryResult> {
  if (!idea.trim() || !character.trim()) {
    throw new Error('故事点子和主角名字不能为空');
  }
  if (numScenes < 1 || numScenes > 30) {
    throw new Error('场景数量必须在 1-30 之间');
  }

  const prompt = buildStoryPrompt(idea, character, numScenes);
  const response = await chatCompletion(
    settings,
    '你是一个专业的儿童绘本作家,擅长创作温馨、简单、富有教育意义的故事。',
    prompt,
    0.8
  );
  return parseStoryResponse(response, numScenes);
}

/** 将小朋友断断续续的语音转写文本凝练为故事创意（百炼 LLM） */
export async function summarizeVoiceIdea(
  settings: AppSettings,
  rawTranscript: string,
  characterHint?: string
): Promise<string> {
  const transcript = rawTranscript.trim();
  if (!transcript) {
    throw new Error('没有识别到语音内容');
  }

  const charNote = characterHint?.trim()
    ? `\n已知主角/角色名：${characterHint.trim()}`
    : '';

  const prompt = `以下是一个小朋友用语音描述的故事想法，语音识别结果可能断断续续、有重复、有错别字或语气词。请理解其意图，整理成一段适合 3-8 岁儿童绘本的「故事创意」。

**原始语音转写**：
${transcript}
${charNote}

**整理要求**：
1. 用 2-4 句通顺中文，保留孩子想表达的核心情节与角色
2. 去除「嗯」「那个」「然后然后」等口语填充，合并重复表述
3. 可适度补全逻辑，但不要添加与原意无关的新情节
4. 温馨、积极、适合幼儿
5. 只输出整理后的故事创意正文，不要标题、不要 JSON、不要解释

故事创意：`;

  const response = await chatCompletion(
    settings,
    '你擅长倾听儿童口语并整理成清晰温馨的故事梗概。',
    prompt,
    0.4
  );

  const idea = response.trim().replace(/^故事创意[：:]\s*/, '').trim();
  if (!idea) {
    throw new Error('未能整理出故事创意，请重试或改用文字输入');
  }
  return idea.slice(0, 500);
}

export async function translateScenesBatch(
  settings: AppSettings,
  scenes: { text: string }[]
): Promise<string[]> {
  const scenesText = scenes.map((s, i) => `${i + 1}. ${s.text}`).join('\n');
  const prompt = `请将以下儿童绘本的中文场景文本批量翻译成英文。

原文：
${scenesText}

要求：
1. 保持简单易懂，适合3-5岁儿童理解
2. 保持温馨和友好的语气
3. 不要改变原意，只做语言转换
4. 按照原文顺序，每一行输出一个翻译结果
5. 只输出翻译结果，不要包含序号或其他文字

英文翻译：`;

  const response = await chatCompletion(
    settings,
    '你是一个专业的儿童文学翻译，擅长将中文故事翻译成简单易懂的英文。',
    prompt,
    0.3
  );

  const translations = response
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);

  if (translations.length !== scenes.length) {
    const results: string[] = [];
    for (const scene of scenes) {
      results.push(await translateScene(settings, scene.text));
    }
    return results;
  }
  return translations;
}

async function translateScene(
  settings: AppSettings,
  text: string
): Promise<string> {
  const prompt = `请将以下儿童绘本的中文场景文本翻译成英文。

原文：${text}

要求：
1. 保持简单易懂，适合3-5岁儿童理解
2. 保持温馨和友好的语气
3. 不要改变原意，只做语言转换
4. 直接输出翻译结果，不要包含其他文字

英文翻译：`;

  return chatCompletion(
    settings,
    '你是一个专业的儿童文学翻译，擅长将中文故事翻译成简单易懂的英文。',
    prompt,
    0.3
  );
}

export async function generateImagePromptsBatch(
  settings: AppSettings,
  scenes: { text: string }[],
  characterDescription: string
): Promise<string[]> {
  const scenesText = scenes.map((s, i) => `${i + 1}. ${s.text}`).join('\n');

  const prompt = `请为以下儿童绘本故事场景批量生成AI绘画提示词（英文）。

原文：
${scenesText}
${IMAGE_PROMPT_CHAR_NOTE(characterDescription)}

${IMAGE_PROMPT_SCENE_RULES}
7. 按照原文顺序，每一行输出一个英文提示词
8. 只输出英文提示词，不要包含序号或其他文字

英文提示词：`;

  const response = await chatCompletion(
    settings,
    '你是一个专业的儿童绘本插画设计师，擅长为儿童故事创作温馨、生动的AI绘画提示词。',
    prompt,
    0.7
  );

  const prompts = response
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);

  if (prompts.length !== scenes.length) {
    const results: string[] = [];
    for (const scene of scenes) {
      results.push(
        await generateSingleImagePrompt(settings, scene.text, characterDescription)
      );
    }
    return results;
  }
  return prompts;
}

async function generateSingleImagePrompt(
  settings: AppSettings,
  text: string,
  characterDescription: string
): Promise<string> {
  const prompt = `请为以下儿童绘本场景生成AI绘画提示词（英文）。

场景内容：${text}
${IMAGE_PROMPT_CHAR_NOTE(characterDescription)}

${IMAGE_PROMPT_SCENE_RULES}
7. 直接输出英文提示词，不要包含其他文字

英文提示词：`;

  return chatCompletion(
    settings,
    '你是一个专业的儿童绘本插画设计师，擅长为儿童故事创作温馨、生动的AI绘画提示词。',
    prompt,
    0.7
  );
}

/** 绿网审核失败时，将提示词改写为更温和的儿童绘本版本 */
export async function rewritePromptForSafety(
  settings: AppSettings,
  sceneText: string,
  originalPrompt: string,
  characterDescription: string
): Promise<string> {
  const prompt = `以下儿童绘本场景的 AI 绘画提示词可能触发了内容安全审核，请改写为更温和、合规的版本。

场景中文：${sceneText}
原英文提示词：${originalPrompt}
${IMAGE_PROMPT_CHAR_NOTE(characterDescription)}

改写要求：
1. 保留故事核心情节；只保留本场景出场的角色，未出场角色不要画入画面
2. 使用可爱卡通、温馨明亮的儿童绘本风格
3. 避免任何可能被误判为暴力、恐怖、武器、血腥、成人内容的描述
4. 用简单、积极、家庭友好的词汇
5. 只输出改写后的英文提示词，不要其他文字

改写后的英文提示词：`;

  const result = await chatCompletion(
    settings,
    '你是儿童绘本插画专家，擅长将画面描述改写为适合3-5岁幼儿、通过内容审核的温和版本。',
    prompt,
    0.5
  );

  return result.trim().split('\n')[0].trim();
}
