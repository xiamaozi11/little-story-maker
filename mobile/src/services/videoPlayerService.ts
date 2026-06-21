import * as FileSystem from 'expo-file-system';
import * as IntentLauncher from 'expo-intent-launcher';
import { Linking, Platform } from 'react-native';

function normalizeUri(uri: string): string {
  if (uri.startsWith('file://') || uri.startsWith('http://') || uri.startsWith('https://')) {
    return uri;
  }
  return `file://${uri}`;
}

export async function openVideoUri(uri: string): Promise<void> {
  const normalized = normalizeUri(uri);

  if (normalized.startsWith('http://') || normalized.startsWith('https://')) {
    const can = await Linking.canOpenURL(normalized);
    if (!can) {
      throw new Error(`无法打开: ${normalized}`);
    }
    await Linking.openURL(normalized);
    return;
  }

  const info = await FileSystem.getInfoAsync(normalized);
  if (!info.exists) {
    throw new Error('视频文件不存在');
  }

  if (Platform.OS === 'android') {
    const contentUri = await FileSystem.getContentUriAsync(normalized);
    await IntentLauncher.startActivityAsync('android.intent.action.VIEW', {
      data: contentUri,
      flags: 1,
      type: 'video/mp4',
    });
    return;
  }

  const can = await Linking.canOpenURL(normalized);
  if (!can) {
    throw new Error(`无法打开: ${normalized}`);
  }
  await Linking.openURL(normalized);
}
