import AsyncStorage from '@react-native-async-storage/async-storage';
import { Book, BookSummary, Scene } from '../types/book';

const BOOKS_KEY = '@storycraft/books';
const BOOK_PREFIX = '@storycraft/book/';

function sceneFromRaw(raw: Record<string, unknown>, index: number): Scene {
  return {
    index,
    scene_number: index + 1,
    text: String(raw.text ?? ''),
    text_en: raw.text_en ? String(raw.text_en) : undefined,
    image_prompt: raw.image_prompt ? String(raw.image_prompt) : undefined,
    image_path: raw.image_path ? String(raw.image_path) : undefined,
    image_status: raw.image_status as Scene['image_status'],
    image_error: raw.image_error ? String(raw.image_error) : undefined,
  };
}

function normalizeBook(data: Record<string, unknown>): Book {
  const rawScenes = (data.scenes as Record<string, unknown>[]) ?? [];
  const scenes = rawScenes.map((s, i) => sceneFromRaw(s, i));
  return {
    id: String(data.id),
    idea: String(data.idea ?? ''),
    character: String(data.character ?? ''),
    num_scenes: Number(data.num_scenes ?? scenes.length),
    character_description: String(data.character_description ?? ''),
    story_generated: Boolean(data.story_generated),
    has_images: Boolean(data.has_images),
    content_type: (data.content_type as Book['content_type']) ?? 'book',
    image_style: data.image_style ? String(data.image_style) : undefined,
    image_service: data.image_service as Book['image_service'],
    image_size: data.image_size ? String(data.image_size) : undefined,
    scenes,
    anime: data.anime as Book['anime'],
    pdf_path: data.pdf_path ? String(data.pdf_path) : undefined,
    title: data.title ? String(data.title) : undefined,
    author: data.author ? String(data.author) : undefined,
    created_at: String(data.created_at ?? new Date().toISOString()),
    updated_at: String(data.updated_at ?? new Date().toISOString()),
  };
}

async function getBookIds(): Promise<string[]> {
  const raw = await AsyncStorage.getItem(BOOKS_KEY);
  if (!raw) return [];
  return JSON.parse(raw) as string[];
}

async function setBookIds(ids: string[]): Promise<void> {
  await AsyncStorage.setItem(BOOKS_KEY, JSON.stringify(ids));
}

export async function saveBook(book: Book): Promise<void> {
  const updated = { ...book, updated_at: new Date().toISOString() };
  await AsyncStorage.setItem(BOOK_PREFIX + book.id, JSON.stringify(updated));

  const ids = await getBookIds();
  if (!ids.includes(book.id)) {
    ids.unshift(book.id);
    await setBookIds(ids);
  }
}

export async function getBook(id: string): Promise<Book | null> {
  const raw = await AsyncStorage.getItem(BOOK_PREFIX + id);
  if (!raw) return null;
  return normalizeBook(JSON.parse(raw) as Record<string, unknown>);
}

export async function listBooks(): Promise<BookSummary[]> {
  const ids = await getBookIds();
  const summaries: BookSummary[] = [];

  for (const id of ids) {
    const book = await getBook(id);
    if (book) {
      summaries.push({
        id: book.id,
        character: book.character,
        idea: book.idea,
        num_scenes: book.scenes.length,
        has_images: book.has_images,
        content_type: book.content_type,
        created_at: book.created_at,
        title: book.title,
      });
    }
  }
  return summaries;
}

export async function deleteBook(id: string): Promise<void> {
  await AsyncStorage.removeItem(BOOK_PREFIX + id);
  const ids = (await getBookIds()).filter((i) => i !== id);
  await setBookIds(ids);
}

export function createBookId(character: string): string {
  const ts = new Date()
    .toISOString()
    .replace(/[-:T.Z]/g, '')
    .slice(0, 14);
  const safe = character.replace(/[^\w\u4e00-\u9fff-]/g, '') || 'book';
  return `${ts}_${safe}`;
}
