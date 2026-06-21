import {
  DEFAULT_ANIME_IMAGE_STYLE,
  DEFAULT_ANIME_VIDEO_SIZE,
  IMAGE_STYLES,
  SEGMENT_DURATION_SEC,
  SHOTS_PER_SEGMENT,
} from '../config/constants';
import {
  createBookId,
  getBook,
  saveBook,
} from '../storage/historyStore';
import { saveImageFromUrl, saveVideoFromUrl } from '../storage/fileStore';
import {
  AnimeCharacter,
  AnimeData,
  AnimeScript,
  AnimeSegment,
  AnimeShot,
} from '../types/anime';
import { Book } from '../types/book';
import {
  buildSegmentPrompt,
  generateAnimeStoryboard,
  groupShotsIntoSegments,
} from './animeTextService';
import { buildSeedancePromptWithRefs, postSeedanceAndWait } from './seedanceService';
import { loadSettings } from './settings';

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** 与 anime_generator._character_image_urls 一致：仅公网 http(s) URL */
function getCharacterRefsForSeedance(characters: AnimeCharacter[]): {
  urls: string[];
  labels: string[];
} {
  const refs = characters.filter(
    (c) => c.image_status === 'ok' && c.image_url && /^https?:\/\//i.test(c.image_url)
  );
  return {
    urls: refs.map((c) => c.image_url as string),
    labels: refs.map((c) => c.name),
  };
}

function shotsWithIndex(
  shots: { text: string; video_prompt?: string }[],
  baseIndex = 0
): AnimeShot[] {
  return shots.map((s, i) => ({
    index: baseIndex + i,
    text: s.text,
    video_prompt: s.video_prompt,
  }));
}

function buildAnimeDataFromBoard(
  board: Awaited<ReturnType<typeof generateAnimeStoryboard>>
): AnimeData {
  const scripts: AnimeScript[] = board.scripts.map((script, scriptIndex) => {
    const shots = shotsWithIndex(script.shots);
    const segmentGroups = groupShotsIntoSegments(script.shots);
    const segments: AnimeSegment[] = segmentGroups.map((group, segIdx) => ({
      segment_index: segIdx,
      shots: shotsWithIndex(group, segIdx * SHOTS_PER_SEGMENT),
      status: 'pending',
    }));
    return {
      index: scriptIndex,
      title: script.title,
      synopsis: script.synopsis,
      shots,
      segments,
    };
  });

  const characters: AnimeCharacter[] = board.characters.map((c) => ({
    name: c.name,
    description: c.description,
    image_prompt: c.image_prompt,
    image_status: 'pending',
  }));

  return {
    synopsis: board.synopsis,
    characters,
    scripts,
    has_videos: false,
    video_size: DEFAULT_ANIME_VIDEO_SIZE,
    num_segments: board.num_segments,
  };
}

export async function createAnimeStory(
  idea: string,
  character: string,
  numSegments?: number
): Promise<Book> {
  const settings = await loadSettings();
  const board = await generateAnimeStoryboard(
    settings,
    idea,
    character,
    numSegments
  );
  const id = createBookId(character);
  const now = new Date().toISOString();

  const book: Book = {
    id,
    idea,
    character,
    num_scenes: 0,
    character_description: board.character_description,
    story_generated: true,
    has_images: false,
    content_type: 'anime',
    scenes: [],
    anime: buildAnimeDataFromBoard(board),
    created_at: now,
    updated_at: now,
  };

  await saveBook(book);
  return book;
}

export async function generateAnimeCharacterAssets(
  bookId: string,
  imageService: 'doubao' | 'tongyi',
  imageStyle: string,
  imageSize: string,
  onProgress?: (message: string, current?: number, total?: number) => void
): Promise<Book> {
  const settings = await loadSettings();
  const book = await getBook(bookId);
  if (!book?.anime) throw new Error('动漫项目不存在');

  const { characters } = book.anime;
  const total = characters.length;

  for (let i = 0; i < characters.length; i++) {
    const char = characters[i];
    onProgress?.(`生成角色素材：${char.name}`, i + 1, total);

    char.image_status = 'generating';
    await saveBook(book);

    try {
      const url = await generateCharacterImageUrl(
        settings,
        char,
        imageStyle,
        imageService,
        imageSize,
        book.character_description
      );
      char.image_url = url;
      char.image_path = await saveImageFromUrl(bookId, `character_${i + 1}`, url);
      char.image_status = 'ok';
      delete char.image_error;
    } catch (e) {
      char.image_status = 'failed';
      char.image_error = e instanceof Error ? e.message : '角色素材生成失败';
    }

    if (i < characters.length - 1) await sleep(2000);
  }

  book.image_style = imageStyle;
  book.image_service = imageService;
  book.image_size = imageSize;
  book.anime.characters = characters;
  await saveBook(book);
  return book;
}

async function generateCharacterImageUrl(
  settings: Awaited<ReturnType<typeof loadSettings>>,
  char: AnimeCharacter,
  style: string,
  service: 'doubao' | 'tongyi',
  imageSize: string,
  characterDescription: string
): Promise<string> {
  const styleDesc = IMAGE_STYLES[style] ?? IMAGE_STYLES['动漫'];
  const base = char.image_prompt || char.description;
  const prompt = characterDescription
    ? `${base}, ${styleDesc}, anime reference sheet. ${characterDescription}`
    : `${base}, ${styleDesc}, anime reference sheet, child-friendly`;

  if (service === 'tongyi') {
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
            messages: [{ role: 'user', content: [{ text: prompt }] }],
          },
          parameters: {
            prompt_extend: true,
            watermark: false,
            n: 1,
            size: qwenSize,
          },
        }),
      }
    );
    if (!res.ok) throw new Error(`生图失败 ${res.status}`);
    const data = await res.json();
    const url = data?.output?.choices?.[0]?.message?.content?.[0]?.image as string;
    if (!url) throw new Error('生图响应无 URL');
    return url;
  }

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
  if (!res.ok) throw new Error(`豆包生图失败 ${res.status}`);
  const data = await res.json();
  const url = data.data?.[0]?.url as string;
  if (!url) throw new Error('豆包响应无 URL');
  return url;
}

export interface GenerateAnimeVideosResult {
  book: Book;
  completedScripts: number;
  failedSegments: string[];
  failedDetails: string[];
}

async function generateScriptSegmentsFrom(
  bookId: string,
  book: Book,
  script: AnimeScript,
  settings: Awaited<ReturnType<typeof loadSettings>>,
  charUrls: string[],
  charLabels: string[],
  startSegmentIndex: number,
  onProgress?: (message: string) => void
): Promise<{ scriptOk: boolean; failedSegments: string[]; failedDetails: string[] }> {
  const failedSegments: string[] = [];
  const failedDetails: string[] = [];
  let prevVideoUrl: string | undefined;

  if (startSegmentIndex > 0) {
    const prevSeg = script.segments[startSegmentIndex - 1];
    if (prevSeg?.status === 'ok' && prevSeg.video_url) {
      prevVideoUrl = prevSeg.video_url;
    }
  }

  for (let i = startSegmentIndex; i < script.segments.length; i++) {
    const segment = script.segments[i];
    const segShots = segment.shots.map((s) => ({
      text: s.text,
      video_prompt: s.video_prompt,
    }));

    segment.status = 'generating';
    delete segment.error;
    await saveBook(book);

    onProgress?.(
      `剧本「${script.title}」第 ${segment.segment_index + 1}/${script.segments.length} 段（15秒）`
    );

    const basePrompt = buildSegmentPrompt(
      segShots,
      script.title,
      segment.segment_index,
      Boolean(prevVideoUrl)
    );

    const prompt = buildSeedancePromptWithRefs(basePrompt, {
      imageLabels: charLabels,
      videoLabels: prevVideoUrl ? ['上一段视频'] : undefined,
    });

    const byPass: { ratio: string; resolution: string; videos?: string[] } = {
      ratio: '9:16',
      resolution: '720p',
    };
    if (prevVideoUrl) {
      byPass.videos = [prevVideoUrl];
    }

    const result = await postSeedanceAndWait({
      settings,
      prompt,
      duration: SEGMENT_DURATION_SEC,
      size: book.anime!.video_size ?? DEFAULT_ANIME_VIDEO_SIZE,
      generateAudio: true,
      generateMode: 1,
      images: charUrls,
      byPass,
      onPoll: (attempt, state) => {
        onProgress?.(
          `Seedance 轮询 #${attempt} · ${state}（剧本「${script.title}」第${segment.segment_index + 1}段）`
        );
      },
    });

    if (!result.ok || !result.videoUrl) {
      segment.status = 'failed';
      segment.error = result.error ?? '视频生成失败';
      const label = `${script.title} 第${segment.segment_index + 1}段`;
      failedSegments.push(label);
      failedDetails.push(`${label}：${segment.error}`);
      await saveBook(book);
      return { scriptOk: false, failedSegments, failedDetails };
    }

    segment.video_url = result.videoUrl;
    segment.task_id = result.taskId;
    segment.status = 'ok';
    try {
      segment.video_path = await saveVideoFromUrl(
        bookId,
        `script${script.index}_seg${segment.segment_index}`,
        result.videoUrl
      );
    } catch {
      // 下载失败不影响继续用远程 URL 衔接
    }

    prevVideoUrl = result.videoUrl;
    await saveBook(book);
  }

  return { scriptOk: true, failedSegments, failedDetails };
}

function finalizeAnimeVideoBook(book: Book): void {
  book.anime!.has_videos = book.anime!.scripts.some((s) =>
    s.segments.some((seg) => seg.status === 'ok')
  );
  book.has_images = book.anime!.has_videos;
}

export async function generateAnimeVideos(
  bookId: string,
  onProgress?: (message: string) => void
): Promise<GenerateAnimeVideosResult> {
  const settings = await loadSettings();
  const book = await getBook(bookId);
  if (!book?.anime) throw new Error('动漫项目不存在');

  const { urls: charUrls, labels: charLabels } = getCharacterRefsForSeedance(
    book.anime.characters
  );

  if (charUrls.length === 0) {
    throw new Error('请先生成主要角色素材（需含公网图片 URL，Seedance 无法读取本地路径）');
  }

  const failedSegments: string[] = [];
  const failedDetails: string[] = [];
  let completedScripts = 0;

  for (const script of book.anime.scripts) {
    onProgress?.(`开始生成剧本「${script.title}」`);
    const result = await generateScriptSegmentsFrom(
      bookId,
      book,
      script,
      settings,
      charUrls,
      charLabels,
      0,
      onProgress
    );
    failedSegments.push(...result.failedSegments);
    failedDetails.push(...result.failedDetails);
    script.completed = result.scriptOk && script.segments.every((s) => s.status === 'ok');
    if (script.completed) completedScripts += 1;
    if (!result.scriptOk) continue;
  }

  finalizeAnimeVideoBook(book);
  await saveBook(book);

  return { book, completedScripts, failedSegments, failedDetails };
}

/** 从指定段起重新生成（含后续段）；用于失败重试 */
export async function regenerateAnimeSegment(
  bookId: string,
  scriptIndex: number,
  segmentIndex: number,
  onProgress?: (message: string) => void
): Promise<GenerateAnimeVideosResult> {
  const settings = await loadSettings();
  const book = await getBook(bookId);
  if (!book?.anime) throw new Error('动漫项目不存在');

  const script = book.anime.scripts[scriptIndex];
  if (!script) throw new Error('剧本不存在');

  const { urls: charUrls, labels: charLabels } = getCharacterRefsForSeedance(
    book.anime.characters
  );
  if (charUrls.length === 0) {
    throw new Error('请先生成主要角色素材');
  }

  for (let i = segmentIndex; i < script.segments.length; i++) {
    const seg = script.segments[i];
    seg.status = 'pending';
    delete seg.error;
    delete seg.video_url;
    delete seg.video_path;
    delete seg.task_id;
  }
  script.completed = false;
  await saveBook(book);

  onProgress?.(`重新生成「${script.title}」第 ${segmentIndex + 1} 段起`);

  const result = await generateScriptSegmentsFrom(
    bookId,
    book,
    script,
    settings,
    charUrls,
    charLabels,
    segmentIndex,
    onProgress
  );

  script.completed = result.scriptOk && script.segments.every((s) => s.status === 'ok');
  finalizeAnimeVideoBook(book);
  await saveBook(book);

  const completedScripts = book.anime.scripts.filter((s) => s.completed).length;
  return {
    book,
    completedScripts,
    failedSegments: result.failedSegments,
    failedDetails: result.failedDetails,
  };
}

/** 重新生成所有失败或未完成的视频段 */
export async function regenerateFailedAnimeVideos(
  bookId: string,
  onProgress?: (message: string) => void
): Promise<GenerateAnimeVideosResult> {
  const book = await getBook(bookId);
  if (!book?.anime) throw new Error('动漫项目不存在');

  const failedSegments: string[] = [];
  const failedDetails: string[] = [];
  let completedScripts = 0;
  let latestBook = book;

  for (let si = 0; si < book.anime.scripts.length; si++) {
    const script = book.anime.scripts[si];
    const firstRetryIdx = script.segments.findIndex(
      (seg) => seg.status === 'failed' || seg.status === 'pending'
    );
    if (firstRetryIdx < 0) {
      if (script.completed) completedScripts += 1;
      continue;
    }

    const result = await regenerateAnimeSegment(bookId, si, firstRetryIdx, onProgress);
    latestBook = result.book;
    failedSegments.push(...result.failedSegments);
    failedDetails.push(...result.failedDetails);
    if (result.failedSegments.length === 0) completedScripts += 1;
  }

  return {
    book: latestBook,
    completedScripts,
    failedSegments,
    failedDetails,
  };
}

export { DEFAULT_ANIME_IMAGE_STYLE };
