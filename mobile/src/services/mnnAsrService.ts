import {
  EmitterSubscription,
  NativeEventEmitter,
  NativeModules,
  PermissionsAndroid,
  Platform,
} from 'react-native';

interface MnnAsrNativeModule {
  isAvailable(): Promise<boolean>;
  isModelReady(): Promise<boolean>;
  initialize(): Promise<boolean>;
  startListening(): Promise<boolean>;
  stopListening(): Promise<{ transcript: string }>;
  addListener(eventName: string): void;
  removeListeners(count: number): void;
}

const NativeMnnAsr: MnnAsrNativeModule | undefined = NativeModules.MnnAsr;

export interface AsrDownloadProgress {
  current: number;
  total: number;
  message: string;
}

export function isMnnAsrSupported(): boolean {
  return Platform.OS === 'android' && Boolean(NativeMnnAsr);
}

async function requestMicPermission(): Promise<boolean> {
  if (Platform.OS !== 'android') return false;
  const granted = await PermissionsAndroid.request(
    PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
    {
      title: '麦克风权限',
      message: '语音输入故事创意需要访问麦克风',
      buttonPositive: '允许',
      buttonNegative: '拒绝',
    }
  );
  return granted === PermissionsAndroid.RESULTS.GRANTED;
}

let emitter: NativeEventEmitter | null = null;

function getEmitter(): NativeEventEmitter | null {
  if (!NativeMnnAsr) return null;
  if (!emitter) {
    emitter = new NativeEventEmitter(NativeModules.MnnAsr);
  }
  return emitter;
}

export async function ensureMnnAsrReady(): Promise<void> {
  if (!NativeMnnAsr) {
    throw new Error('当前设备不支持 MNN 本地语音识别（仅 Android）');
  }

  const ok = await requestMicPermission();
  if (!ok) throw new Error('未获得麦克风权限');

  const ready = await NativeMnnAsr.isModelReady();
  if (!ready) {
    throw new Error('ASR 模型未内置，请安装完整版 APK');
  }

  await NativeMnnAsr.initialize();
}

export async function startMnnListening(
  onPartial?: (transcript: string) => void
): Promise<() => Promise<string>> {
  if (!NativeMnnAsr) {
    throw new Error('MNN ASR 不可用');
  }

  const partialSub = onPartial
    ? getEmitter()?.addListener('MnnAsrPartial', (e: { transcript: string }) => {
        onPartial(e.transcript ?? '');
      })
    : undefined;

  await NativeMnnAsr.startListening();

  return async () => {
    try {
      const result = await NativeMnnAsr.stopListening();
      return (result.transcript ?? '').trim();
    } finally {
      partialSub?.remove();
    }
  };
}

export async function transcribeWithMnnAsr(
  onPartial?: (transcript: string) => void
): Promise<string> {
  await ensureMnnAsrReady();
  const stop = await startMnnListening(onPartial);
  return stop();
}
