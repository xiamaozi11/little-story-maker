import {
  DEFAULT_ANIME_SEGMENTS,
  MAX_ANIME_SEGMENTS,
  MIN_ANIME_SEGMENTS,
  SHOTS_PER_SEGMENT,
} from '../config/constants';
import { AnimeStoryboardResult } from '../types/anime';
import { AppSettings } from './settings';

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

function buildAnimeStoryboardPrompt(
  idea: string,
  character: string,
  numSegments: number
): string {
  const segments = Math.max(
    MIN_ANIME_SEGMENTS,
    Math.min(MAX_ANIME_SEGMENTS, numSegments)
  );
  const targetShots = segments * SHOTS_PER_SEGMENT;
  const totalDuration = segments * 15;

  return `请为3-8岁儿童创作动漫短视频分镜剧本。

故事创意：${idea}
主要角色：${character}（可为多名，用顿号/逗号分隔）

**本次视频规划（必须严格遵守，不可增减）**：
- 用户选择生成 ${segments} 段短视频，每段 15 秒，总时长 ${totalDuration} 秒
- scripts 数组长度必须为 1，只输出一个完整剧本
- 该剧本 shots 数组长度必须恰好为 ${targetShots} 个（${segments} 段 × 每段 5 镜头）
- 镜头 1~5 为第 1 段，镜头 6~10 为第 2 段，以此类推；每镜头约 3 秒
- 每段内部 5 个镜头动作连贯、情绪递进；段与段之间自然衔接（下一段承接上一段结尾画面）
- 全 ${segments} 段构成完整起承转合，适合儿童观看
- 禁止输出超过或少于 ${targetShots} 个镜头

**角色设定**：
- characters 列出主要人物（2~4 名），含外貌与性格
- character_description 为全体角色英文外貌库，供后续生图参考

**镜头要求**：
- 每个镜头写清画面动作、景别（特写/中景/全景）、情绪
- video_prompt 为英文，描述该镜头动画画面，适合 AI 视频生成
- 有角色说话或旁白的镜头，必须写 dialogue（中文，格式「角色名：「台词内容」」；旁白用「旁白：「…」」）；纯动作无台词可省略 dialogue
- 对白要符合 3–8 岁儿童用语，简短生动，与画面情绪一致
- 镜头之间动作连贯，适合 15 秒一段的流畅动漫短片

请只输出 JSON（无其他文字）：
{
  "synopsis": "故事梗概（中文，2-3句）",
  "character_description": "全体角色英文外貌设定",
  "characters": [
    {
      "name": "角色中文名",
      "description": "外貌与性格（中文）",
      "image_prompt": "角色立绘参考图英文提示词，动漫风格，全身或半身，纯色背景"
    }
  ],
  "scripts": [
    {
      "title": "剧本标题",
      "synopsis": "本集梗概（中文）",
      "shots": [
        {
          "text": "镜头中文描述",
          "dialogue": "角色名：「台词内容」（无对白可省略此字段）",
          "video_prompt": "镜头英文动画画面描述"
        }
      ]
    }
  ]
}`;
}

function parseAnimeStoryboard(
  response: string,
  numSegments: number
): AnimeStoryboardResult {
  const segments = Math.max(
    MIN_ANIME_SEGMENTS,
    Math.min(MAX_ANIME_SEGMENTS, numSegments)
  );
  const targetShots = segments * SHOTS_PER_SEGMENT;

  try {
    const start = response.indexOf('{');
    const end = response.lastIndexOf('}') + 1;
    const data = JSON.parse(response.slice(start, end)) as AnimeStoryboardResult & {
      scripts: { title: string; synopsis: string; shots: { text: string; video_prompt?: string; dialogue?: string }[] }[];
    };

    const primary = data.scripts?.[0];
    const shots = (primary?.shots ?? []).slice(0, targetShots);
    const valid = Math.floor(shots.length / SHOTS_PER_SEGMENT) * SHOTS_PER_SEGMENT;

    const scripts =
      valid >= SHOTS_PER_SEGMENT
        ? [
            {
              title: primary?.title || '未命名',
              synopsis: primary?.synopsis || '',
              shots: shots.slice(0, valid),
            },
          ]
        : [];

    if (scripts.length === 0) {
      scripts.push({
        title: '第一集',
        synopsis: data.synopsis ?? '',
        shots: Array.from({ length: targetShots }, (_, i) => ({
          text: `镜头 ${i + 1}`,
          video_prompt: `Anime shot ${i + 1}, child-friendly, cel shading`,
        })),
      });
    }

    return {
      synopsis: data.synopsis ?? '',
      character_description: data.character_description ?? '',
      characters: data.characters ?? [],
      scripts,
      num_segments: segments,
    };
  } catch {
    return {
      synopsis: '',
      character_description: '',
      characters: [],
      scripts: [
        {
          title: '第一集',
          synopsis: '',
          shots: Array.from({ length: targetShots }, (_, i) => ({
            text: `镜头 ${i + 1}`,
            video_prompt: `Anime shot ${i + 1}`,
          })),
        },
      ],
      num_segments: segments,
    };
  }
}

export async function generateAnimeStoryboard(
  settings: AppSettings,
  idea: string,
  character: string,
  numSegments: number = DEFAULT_ANIME_SEGMENTS
): Promise<AnimeStoryboardResult> {
  if (!idea.trim() || !character.trim()) {
    throw new Error('故事创意和主角不能为空');
  }
  const segments = Math.max(
    MIN_ANIME_SEGMENTS,
    Math.min(MAX_ANIME_SEGMENTS, numSegments)
  );
  const prompt = buildAnimeStoryboardPrompt(idea, character, segments);
  const response = await chatCompletion(
    settings,
    '你是专业的儿童动漫分镜编剧，擅长将故事拆解为连贯的镜头剧本，并为角色撰写适合儿童的对白。',
    prompt,
    0.75
  );
  return parseAnimeStoryboard(response, segments);
}

export function buildSegmentPrompt(
  shots: { text: string; video_prompt?: string; dialogue?: string }[],
  scriptTitle: string,
  segmentIndex: number,
  isContinuation: boolean
): string {
  const lines = [`【${scriptTitle} · 第${segmentIndex + 1}段 · 15秒动漫短片】`];
  if (isContinuation) {
    lines.push('承接上一段视频最后一帧画面，动作与场景自然延续，不要跳切。');
  }
  shots.forEach((shot, i) => {
    const start = i * 3;
    const end = start + 3;
    lines.push(`镜头${i + 1}（${start}-${end}秒）：${shot.text}`);
    if (shot.dialogue?.trim()) {
      lines.push(`  对白：${shot.dialogue.trim()}`);
    }
    if (shot.video_prompt) {
      lines.push(`  画面：${shot.video_prompt}`);
    }
  });
  lines.push(
    '要求：日本动漫 cel shading 风格，儿童向，色彩明亮，动作流畅，镜头间自然过渡，角色口型与对白匹配，无暴力恐怖元素。'
  );
  return lines.join('\n');
}

export function groupShotsIntoSegments<
  T extends { text: string; video_prompt?: string; dialogue?: string },
>(shots: T[]): T[][] {
  const segments: T[][] = [];
  for (let i = 0; i < shots.length; i += SHOTS_PER_SEGMENT) {
    const chunk = shots.slice(i, i + SHOTS_PER_SEGMENT);
    if (chunk.length === SHOTS_PER_SEGMENT) {
      segments.push(chunk);
    }
  }
  return segments.slice(0, MAX_ANIME_SEGMENTS);
}
