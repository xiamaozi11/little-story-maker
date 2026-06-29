import * as FileSystem from 'expo-file-system';

const BOOKS_ROOT = `${FileSystem.documentDirectory}books/`;

export function getBookDir(bookId: string): string {
  return `${BOOKS_ROOT}${bookId}/`;
}

export function getSegmentVideoPath(
  bookId: string,
  scriptIndex: number,
  segmentIndex: number
): string {
  return `${getBookDir(bookId)}script${scriptIndex}_seg${segmentIndex}.mp4`;
}

export function getMergedVideoPath(bookId: string, scriptIndex: number): string {
  return `${getBookDir(bookId)}script${scriptIndex}_merged.mp4`;
}

export async function ensureBookDir(bookId: string): Promise<string> {
  const dir = getBookDir(bookId);
  const info = await FileSystem.getInfoAsync(dir);
  if (!info.exists) {
    await FileSystem.makeDirectoryAsync(dir, { intermediates: true });
  }
  return dir;
}

export async function saveImage(
  bookId: string,
  sceneId: string,
  base64: string
): Promise<string> {
  const dir = await ensureBookDir(bookId);
  const path = `${dir}${sceneId}.png`;
  await FileSystem.writeAsStringAsync(path, base64, {
    encoding: FileSystem.EncodingType.Base64,
  });
  return path;
}

export async function saveImageFromUrl(
  bookId: string,
  sceneId: string,
  url: string
): Promise<string> {
  const dir = await ensureBookDir(bookId);
  const path = `${dir}${sceneId}.png`;
  const result = await FileSystem.downloadAsync(url, path);
  return result.uri;
}

export async function saveVideoFromUrl(
  bookId: string,
  videoId: string,
  url: string
): Promise<string> {
  const dir = await ensureBookDir(bookId);
  const path = `${dir}${videoId}.mp4`;
  const result = await FileSystem.downloadAsync(url, path);
  return result.uri;
}

export async function readImageBase64(imagePath: string): Promise<string> {
  return FileSystem.readAsStringAsync(imagePath, {
    encoding: FileSystem.EncodingType.Base64,
  });
}

export async function getFileSizeMb(filePath: string): Promise<number> {
  const info = await FileSystem.getInfoAsync(filePath);
  if (!info.exists || !('size' in info) || !info.size) return 0;
  return Math.round((info.size / (1024 * 1024)) * 100) / 100;
}

export async function deleteBookFiles(bookId: string): Promise<void> {
  const dir = getBookDir(bookId);
  const info = await FileSystem.getInfoAsync(dir);
  if (info.exists) {
    await FileSystem.deleteAsync(dir, { idempotent: true });
  }
}
