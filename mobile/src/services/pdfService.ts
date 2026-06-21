import * as Print from 'expo-print';
import * as FileSystem from 'expo-file-system';
import * as ImageManipulator from 'expo-image-manipulator';
import { ensureBookDir } from '../storage/fileStore';
import { Book } from '../types/book';

/** PDF 页面宽度约 612px，插图无需原图分辨率，压缩后可避免 Android OOM */
const PDF_IMAGE_MAX_WIDTH = 600;
const PDF_JPEG_QUALITY = 0.72;

async function imageToDataUri(imagePath?: string): Promise<string> {
  if (!imagePath) return '';
  let tempUri: string | undefined;
  try {
    const info = await FileSystem.getInfoAsync(imagePath);
    if (!info.exists) return '';

    const result = await ImageManipulator.manipulateAsync(
      imagePath,
      [{ resize: { width: PDF_IMAGE_MAX_WIDTH } }],
      {
        compress: PDF_JPEG_QUALITY,
        format: ImageManipulator.SaveFormat.JPEG,
      }
    );
    tempUri = result.uri;

    const base64 = await FileSystem.readAsStringAsync(tempUri, {
      encoding: FileSystem.EncodingType.Base64,
    });
    return `data:image/jpeg;base64,${base64}`;
  } catch {
    return '';
  } finally {
    if (tempUri) {
      await FileSystem.deleteAsync(tempUri, { idempotent: true });
    }
  }
}

/** 顺序处理图片，避免多张原图同时驻留内存 */
async function loadSceneImages(scenes: Book['scenes']): Promise<string[]> {
  const uris: string[] = [];
  for (const scene of scenes) {
    uris.push(await imageToDataUri(scene.image_path));
  }
  return uris;
}

function buildHtml(
  book: Book,
  title: string,
  author: string,
  imageDataUris: string[]
): string {
  const pages = book.scenes
    .map((scene, i) => {
      const img = imageDataUris[i]
        ? `<img src="${imageDataUris[i]}" style="width:100%;max-height:55vh;object-fit:contain;border-radius:12px;" />`
        : '';
      return `
        <div class="page">
          ${img}
          <p class="scene-num">场景 ${scene.scene_number}</p>
          <p class="text">${escapeHtml(scene.text)}</p>
          ${scene.text_en ? `<p class="text-en">${escapeHtml(scene.text_en)}</p>` : ''}
        </div>
      `;
    })
    .join('');

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    @page { margin: 24px; }
    body {
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      color: #2D3436;
      margin: 0;
      padding: 0;
    }
    .cover {
      text-align: center;
      padding: 80px 24px;
      page-break-after: always;
    }
    .cover h1 { font-size: 32px; color: #FF8C42; margin-bottom: 16px; }
    .cover .author { font-size: 18px; color: #636E72; }
    .page {
      page-break-after: always;
      padding: 16px 0;
      text-align: center;
    }
    .scene-num {
      font-size: 14px;
      color: #FF8C42;
      font-weight: bold;
      margin: 12px 0 8px;
    }
    .text {
      font-size: 20px;
      line-height: 1.8;
      text-align: left;
      padding: 0 8px;
    }
    .text-en {
      font-size: 16px;
      color: #636E72;
      line-height: 1.6;
      text-align: left;
      padding: 8px 8px 0;
      font-style: italic;
    }
  </style>
</head>
<body>
  <div class="cover">
    <h1>${escapeHtml(title)}</h1>
    <p class="author">作者：${escapeHtml(author)}</p>
  </div>
  ${pages}
</body>
</html>`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export async function generatePdf(
  book: Book,
  title: string,
  author: string
): Promise<string> {
  const imageDataUris = await loadSceneImages(book.scenes);

  const html = buildHtml(book, title, author, imageDataUris);
  const { uri } = await Print.printToFileAsync({ html });

  await ensureBookDir(book.id);
  const dest = `${FileSystem.documentDirectory}books/${book.id}/${title.replace(/[/\\?%*:|"<>]/g, '_')}.pdf`;
  await FileSystem.copyAsync({ from: uri, to: dest });
  await FileSystem.deleteAsync(uri, { idempotent: true });
  return dest;
}
