import { IMAGE_STYLES } from '../config/constants';
import { saveImageFromUrl } from '../storage/fileStore';
import { AppSettings } from './settings';
import { rewritePromptForSafety } from './textService';

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** 儿童绘本安全约束，降低绿网误拦概率 */
const CHILD_SAFE_RULES =
  'wholesome, family-friendly, G-rated, no violence, no weapons, no scary elements, ' +
  'cute cartoon illustration for toddlers, bright soft colors, warm atmosphere';

export type SceneImageStatus = 'ok' | 'failed' | 'pending';

export interface SceneImageResult {
  index: number;
  path?: string;
  status: SceneImageStatus;
  error?: string;
  promptUsed?: string;
}

export function isContentModerationError(message: string): boolean {
  const lower = message.toLowerCase();
  return (
    lower.includes('datainspectionfailed') ||
    lower.includes('green net') ||
    lower.includes('inappropriate content') ||
    lower.includes('内容不合规') ||
    lower.includes('绿网')
  );
}

function enhancePrompt(
  prompt: string,
  style: string,
  extraSafe = false
): string {
  const styleDesc = IMAGE_STYLES[style] ?? IMAGE_STYLES['卡通'];
  const parts: string[] = [];
  if (extraSafe) {
    parts.push(
      'A gentle children picture book illustration for ages 3-5,',
      CHILD_SAFE_RULES + ','
    );
  }
  parts.push(
    prompt,
    styleDesc,
    "children's book illustration style",
    'suitable for 3-5 years old',
    'simple and clear composition',
    'only depict characters mentioned in this scene',
    CHILD_SAFE_RULES
  );
  return parts.join(', ');
}

async function downloadToFile(
  bookId: string,
  sceneId: string,
  url: string
): Promise<string> {
  return saveImageFromUrl(bookId, sceneId, url);
}

async function generateTongyiImage(
  settings: AppSettings,
  prompt: string,
  imageSize: string,
  promptExtend = true
): Promise<string> {
  const qwenSize = imageSize.replace('x', '*');

  const res = await fetch(
    'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${settings.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: settings.imageModel,
        input: {
          messages: [
            {
              role: 'user',
              content: [{ text: prompt }],
            },
          ],
        },
        parameters: {
          prompt_extend: promptExtend,
          watermark: false,
          n: 1,
          size: qwenSize,
        },
      }),
    }
  );

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`百炼生图失败 (${res.status}): ${err.slice(0, 300)}`);
  }

  const data = await res.json();
  const imageUrl =
    data?.output?.choices?.[0]?.message?.content?.[0]?.image as
      | string
      | undefined;

  if (!imageUrl) {
    throw new Error('百炼生图响应格式异常');
  }
  return imageUrl;
}

async function generateDoubaoSingle(
  settings: AppSettings,
  prompt: string,
  imageSize: string
): Promise<string> {
  const res = await fetch(`${settings.arkBaseUrl}/images/generations`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${settings.arkApiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: settings.doubaoModel,
      prompt,
      size: imageSize,
      response_format: 'url',
      watermark: false,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`豆包生图失败 (${res.status}): ${err.slice(0, 300)}`);
  }

  const data = await res.json();
  const url = data.data?.[0]?.url as string | undefined;
  if (!url) throw new Error('豆包生图响应格式异常');
  return url;
}

export interface GenerateSceneOptions {
  bookId: string;
  index: number;
  prompt: string;
  sceneText: string;
  style: string;
  service: 'doubao' | 'tongyi';
  imageSize: string;
  characterDescription: string;
  settings: AppSettings;
}

/** 单场景生图，含绿网失败自动降级重试 */
export async function generateSingleSceneImage(
  options: GenerateSceneOptions
): Promise<SceneImageResult> {
  const {
    bookId,
    index,
    prompt,
    sceneText,
    style,
    service,
    imageSize,
    characterDescription,
    settings,
  } = options;

  const sceneId = `scene_${index + 1}`;
  let lastError = '';
  let currentPrompt = prompt;

  const attempts: {
    prompt: string;
    promptExtend: boolean;
    extraSafe: boolean;
    rewrite?: boolean;
  }[] = [
    { prompt: currentPrompt, promptExtend: true, extraSafe: false },
    { prompt: currentPrompt, promptExtend: false, extraSafe: true },
    { prompt: currentPrompt, promptExtend: false, extraSafe: true, rewrite: true },
  ];

  for (let attempt = 0; attempt < attempts.length; attempt++) {
    const cfg = attempts[attempt];
    try {
      if (cfg.rewrite) {
        currentPrompt = await rewritePromptForSafety(
          settings,
          sceneText,
          currentPrompt,
          characterDescription
        );
      }

      const enhanced = enhancePrompt(
        cfg.prompt === currentPrompt ? currentPrompt : currentPrompt,
        style,
        cfg.extraSafe
      );

      let url: string;
      if (service === 'tongyi') {
        url = await generateTongyiImage(
          settings,
          enhanced,
          imageSize,
          cfg.promptExtend
        );
      } else {
        url = await generateDoubaoSingle(settings, enhanced, imageSize);
      }

      const path = await downloadToFile(bookId, sceneId, url);
      return {
        index,
        path,
        status: 'ok',
        promptUsed: currentPrompt,
      };
    } catch (e) {
      lastError = e instanceof Error ? e.message : String(e);
      if (!isContentModerationError(lastError) && attempt === 0) {
        // 非内容审核错误，仅重试一次
        await sleep(2000);
        continue;
      }
      if (attempt < attempts.length - 1) {
        await sleep(1500);
      }
    }
  }

  return {
    index,
    status: 'failed',
    error: lastError || '生图失败',
    promptUsed: currentPrompt,
  };
}

export interface GenerateImagesOptions {
  bookId: string;
  prompts: string[];
  sceneTexts: string[];
  style: string;
  service: 'doubao' | 'tongyi';
  imageSize: string;
  characterDescription: string;
  settings: AppSettings;
  onProgress?: (current: number, total: number, result: SceneImageResult) => void;
  onSceneComplete?: (result: SceneImageResult) => void | Promise<void>;
}

/** 逐张生成，单张失败不中断整本 */
export async function generateImages(
  options: GenerateImagesOptions
): Promise<SceneImageResult[]> {
  const {
    bookId,
    prompts,
    sceneTexts,
    style,
    service,
    imageSize,
    characterDescription,
    settings,
    onProgress,
    onSceneComplete,
  } = options;

  const results: SceneImageResult[] = [];

  for (let i = 0; i < prompts.length; i++) {
    if (i > 0) await sleep(3000);
    onProgress?.(i + 1, prompts.length, { index: i, status: 'pending' });

    const result = await generateSingleSceneImage({
      bookId,
      index: i,
      prompt: prompts[i],
      sceneText: sceneTexts[i] ?? '',
      style,
      service,
      imageSize,
      characterDescription,
      settings,
    });

    results.push(result);
    await onSceneComplete?.(result);
  }

  return results;
}

/** 手动重新生成单张（可自定义提示词） */
export async function regenerateSceneImage(
  settings: AppSettings,
  options: Omit<GenerateSceneOptions, 'settings'>
): Promise<SceneImageResult> {
  return generateSingleSceneImage({ ...options, settings });
}
