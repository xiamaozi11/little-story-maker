import * as FileSystem from 'expo-file-system';
import { Platform } from 'react-native';
import { ensureBookDir } from '../storage/fileStore';

function stripFileUri(path: string): string {
  return path.startsWith('file://') ? path.slice(7) : path;
}

/** 使用 FFmpeg 将多段 MP4 无损拼接为一条完整视频（仅 Android 原生构建可用） */
export async function mergeLocalVideos(
  bookId: string,
  inputPaths: string[],
  outputBaseName: string
): Promise<string> {
  if (Platform.OS !== 'android') {
    throw new Error('视频合成目前仅支持 Android 版 App');
  }
  if (inputPaths.length < 2) {
    throw new Error('至少需要 2 段视频才能合成');
  }

  for (const p of inputPaths) {
    const info = await FileSystem.getInfoAsync(p);
    if (!info.exists) {
      throw new Error('部分视频文件不存在，请重新生成后再合成');
    }
  }

  let FFmpegKit: typeof import('ffmpeg-kit-react-native').FFmpegKit;
  let ReturnCode: typeof import('ffmpeg-kit-react-native').ReturnCode;
  try {
    const mod = await import('ffmpeg-kit-react-native');
    FFmpegKit = mod.FFmpegKit;
    ReturnCode = mod.ReturnCode;
  } catch {
    throw new Error(
      '未找到 FFmpeg 模块，请重新构建 APK（npm run build:apk:local）后再试'
    );
  }

  const dir = await ensureBookDir(bookId);
  const listPath = `${dir}concat_${outputBaseName}.txt`;
  const outputPath = `${dir}${outputBaseName}.mp4`;

  const listContent = inputPaths
    .map((p) => {
      const abs = stripFileUri(p);
      return `file '${abs.replace(/'/g, "'\\''")}'`;
    })
    .join('\n');

  await FileSystem.writeAsStringAsync(listPath, listContent);

  const listAbs = stripFileUri(listPath);
  const outAbs = stripFileUri(outputPath);
  const cmd = `-y -f concat -safe 0 -i "${listAbs}" -c copy "${outAbs}"`;

  const session = await FFmpegKit.execute(cmd);
  await FileSystem.deleteAsync(listPath, { idempotent: true });

  const rc = await session.getReturnCode();
  if (!ReturnCode.isSuccess(rc)) {
    const logs = (await session.getAllLogsAsString()) ?? '';
    throw new Error(`视频合成失败：${logs.slice(-300) || '未知错误'}`);
  }

  const outInfo = await FileSystem.getInfoAsync(outputPath);
  if (!outInfo.exists) {
    throw new Error('合成完成但未找到输出文件');
  }

  return outputPath;
}
