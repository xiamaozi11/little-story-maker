import { APP_CONFIG } from '../config/constants';
import {
  createBookId,
  getBook,
  saveBook,
} from '../storage/historyStore';
import { getFileSizeMb } from '../storage/fileStore';
import { Book, Scene } from '../types/book';
import { generateImages, regenerateSceneImage } from './imageService';
import { generatePdf } from './pdfService';
import { loadSettings } from './settings';
import {
  generateImagePromptsBatch,
  generateStory,
  translateScenesBatch,
} from './textService';

export { APP_CONFIG };

export interface GeneratePicturesResult {
  book: Book;
  successCount: number;
  failedCount: number;
  failedScenes: number[];
}

export async function createStory(
  idea: string,
  character: string,
  numScenes: number
): Promise<Book> {
  const settings = await loadSettings();
  const story = await generateStory(settings, idea, character, numScenes);
  const id = createBookId(character);
  const now = new Date().toISOString();

  const scenes: Scene[] = story.scenes.map((s, i) => ({
    index: i,
    scene_number: i + 1,
    text: s.text,
  }));

  const book: Book = {
    id,
    idea,
    character,
    num_scenes: numScenes,
    character_description: story.character_description,
    story_generated: true,
    has_images: false,
    scenes,
    created_at: now,
    updated_at: now,
  };

  await saveBook(book);
  return book;
}

export async function updateSceneText(
  bookId: string,
  index: number,
  text: string
): Promise<Book> {
  const book = await getBook(bookId);
  if (!book) throw new Error('绘本不存在');

  book.scenes[index].text = text;
  delete book.scenes[index].text_en;
  await saveBook(book);
  return book;
}

export async function updateSceneImagePrompt(
  bookId: string,
  index: number,
  imagePrompt: string
): Promise<Book> {
  const book = await getBook(bookId);
  if (!book) throw new Error('绘本不存在');

  book.scenes[index].image_prompt = imagePrompt;
  book.scenes[index].image_status = 'pending';
  delete book.scenes[index].image_path;
  delete book.scenes[index].image_error;
  await saveBook(book);
  return book;
}

function applyImageResult(book: Book, index: number, result: {
  path?: string;
  status: 'ok' | 'failed' | 'pending';
  error?: string;
  promptUsed?: string;
}) {
  const scene = book.scenes[index];
  if (result.promptUsed) {
    scene.image_prompt = result.promptUsed;
  }
  scene.image_status = result.status;
  if (result.status === 'ok' && result.path) {
    scene.image_path = result.path;
    delete scene.image_error;
  } else if (result.status === 'failed') {
    delete scene.image_path;
    scene.image_error = result.error;
  }
}

function syncBookImageFlags(book: Book) {
  // 有成功或失败记录均可进入预览（失败页可重试）
  book.has_images = book.scenes.some(
    (s) => s.image_status === 'ok' || s.image_status === 'failed'
  );
}

export async function generatePictures(
  bookId: string,
  imageService: 'doubao' | 'tongyi',
  imageStyle: string,
  imageSize: string,
  onProgress?: (message: string, current?: number, total?: number) => void
): Promise<GeneratePicturesResult> {
  const settings = await loadSettings();
  const book = await getBook(bookId);
  if (!book) throw new Error('绘本不存在');

  onProgress?.('正在翻译故事...');
  const needTranslate = book.scenes.some((s) => !s.text_en);
  if (needTranslate) {
    const translations = await translateScenesBatch(settings, book.scenes);
    book.scenes.forEach((s, i) => {
      s.text_en = translations[i];
    });
    await saveBook(book);
  }

  onProgress?.('正在生成图片提示词...');
  const needPrompts = book.scenes.some((s) => !s.image_prompt);
  if (needPrompts) {
    const prompts = await generateImagePromptsBatch(
      settings,
      book.scenes,
      book.character_description
    );
    book.scenes.forEach((s, i) => {
      s.image_prompt = prompts[i];
    });
    await saveBook(book);
  }

  book.image_style = imageStyle;
  book.image_service = imageService;
  book.image_size = imageSize;

  onProgress?.('正在生成插画...', 0, book.scenes.length);

  const results = await generateImages({
    bookId,
    prompts: book.scenes.map((s) => s.image_prompt ?? ''),
    sceneTexts: book.scenes.map((s) => s.text),
    style: imageStyle,
    service: imageService,
    imageSize,
    characterDescription: book.character_description,
    settings,
    onProgress: (current, total) =>
      onProgress?.(`正在生成插画 ${current}/${total}...`, current, total),
    onSceneComplete: async (result) => {
      applyImageResult(book, result.index, result);
      syncBookImageFlags(book);
      await saveBook(book);
    },
  });

  results.forEach((r) => applyImageResult(book, r.index, r));
  syncBookImageFlags(book);
  await saveBook(book);

  const failedScenes = results
    .filter((r) => r.status === 'failed')
    .map((r) => r.index + 1);
  const successCount = results.filter((r) => r.status === 'ok').length;

  return {
    book,
    successCount,
    failedCount: failedScenes.length,
    failedScenes,
  };
}

export async function retrySceneImage(
  bookId: string,
  index: number,
  customPrompt?: string
): Promise<Book> {
  const settings = await loadSettings();
  const book = await getBook(bookId);
  if (!book) throw new Error('绘本不存在');

  const scene = book.scenes[index];
  const prompt = customPrompt?.trim() || scene.image_prompt || '';
  if (!prompt) throw new Error('请先填写图片提示词');

  const style = book.image_style ?? APP_CONFIG.default_image_style;
  const service = book.image_service ?? 'tongyi';
  const imageSize = book.image_size ?? '1104x1472';

  const result = await regenerateSceneImage(settings, {
    bookId,
    index,
    prompt,
    sceneText: scene.text,
    style,
    service,
    imageSize,
    characterDescription: book.character_description,
  });

  applyImageResult(book, index, result);
  syncBookImageFlags(book);
  await saveBook(book);
  return book;
}

export async function exportPdf(
  bookId: string,
  title: string,
  author: string
): Promise<{ book: Book; sizeMb: number }> {
  const book = await getBook(bookId);
  if (!book) throw new Error('绘本不存在');
  const okScenes = book.scenes.filter((s) => s.image_status === 'ok');
  if (okScenes.length === 0) throw new Error('没有可用的插画，请先生成或重试失败的场景');

  const pdfPath = await generatePdf(book, title, author);
  book.pdf_path = pdfPath;
  book.title = title;
  book.author = author;
  await saveBook(book);

  const sizeMb = await getFileSizeMb(pdfPath);
  return { book, sizeMb };
}

export { getBook, listBooks, deleteBook } from '../storage/historyStore';
export type { Book, Scene } from '../types/book';
