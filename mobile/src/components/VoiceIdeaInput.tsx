import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { colors, fontSize, radius, spacing } from '../theme';
import {
  isMnnAsrSupported,
  startMnnListening,
  ensureMnnAsrReady,
} from '../services/mnnAsrService';
import { summarizeVoiceIdea } from '../services/textService';
import { loadSettings } from '../services/settings';

interface VoiceIdeaInputProps {
  character?: string;
  onIdeaReady: (idea: string) => void;
  disabled?: boolean;
}

type VoiceState = 'idle' | 'preparing' | 'listening' | 'summarizing';

export function VoiceIdeaInput({
  character,
  onIdeaReady,
  disabled,
}: VoiceIdeaInputProps) {
  const [state, setState] = useState<VoiceState>('idle');
  const [partial, setPartial] = useState('');
  const [statusMsg, setStatusMsg] = useState('');
  const stopRef = useRef<(() => Promise<string>) | null>(null);
  const supported = isMnnAsrSupported();

  useEffect(() => {
    return () => {
      stopRef.current?.().catch(() => {});
    };
  }, []);

  const handleStart = useCallback(async () => {
    if (!supported || disabled) return;

    setState('preparing');
    setPartial('');
    setStatusMsg('初始化本地语音识别…');

    try {
      await ensureMnnAsrReady();

      setState('listening');
      setStatusMsg('正在听，说完后点「结束并整理」');

      const stop = await startMnnListening((text) => setPartial(text));
      stopRef.current = stop;
    } catch (e) {
      setState('idle');
      setStatusMsg('');
      Alert.alert(
        '语音输入失败',
        e instanceof Error ? e.message : '未知错误'
      );
    }
  }, [supported, disabled]);

  const handleStopAndSummarize = useCallback(async () => {
    if (!stopRef.current) return;

    setState('summarizing');
    setStatusMsg('本地识别完成，百炼正在整理故事创意…');

    try {
      const transcript = await stopRef.current();
      stopRef.current = null;

      if (!transcript.trim()) {
        throw new Error('未识别到有效语音，请靠近麦克风重试');
      }

      const settings = await loadSettings();
      const idea = await summarizeVoiceIdea(settings, transcript, character);
      onIdeaReady(idea);
      setPartial('');
      setStatusMsg('');
      setState('idle');
    } catch (e) {
      setState('idle');
      setStatusMsg('');
      Alert.alert(
        '整理失败',
        e instanceof Error ? e.message : '未知错误'
      );
    }
  }, [character, onIdeaReady]);

  const handleCancel = useCallback(async () => {
    if (stopRef.current) {
      await stopRef.current().catch(() => {});
      stopRef.current = null;
    }
    setPartial('');
    setStatusMsg('');
    setState('idle');
  }, []);

  if (!supported) {
    return (
      <Text style={styles.unsupported}>
        语音输入需 Android 版（MNN 本地 ASR），当前环境请使用文字输入
      </Text>
    );
  }

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>🎤 语音输入（MNN 本地识别）</Text>
      <Text style={styles.hint}>
        模型已内置安装包，小朋友慢慢说，说完后由百炼 AI 整理成故事创意
      </Text>

      {statusMsg ? <Text style={styles.status}>{statusMsg}</Text> : null}

      {partial ? (
        <View style={styles.partialBox}>
          <Text style={styles.partialLabel}>实时转写</Text>
          <Text style={styles.partialText}>{partial}</Text>
        </View>
      ) : null}

      <View style={styles.row}>
        {state === 'idle' && (
          <Pressable
            style={[styles.micBtn, disabled && styles.micBtnDisabled]}
            onPress={handleStart}
            disabled={disabled}
          >
            <Text style={styles.micBtnText}>🎤 开始说话</Text>
          </Pressable>
        )}

        {state === 'preparing' && (
          <View style={[styles.micBtn, styles.micBtnBusy]}>
            <Text style={styles.micBtnText}>准备中…</Text>
          </View>
        )}

        {state === 'listening' && (
          <>
            <Pressable style={[styles.micBtn, styles.micBtnActive]} onPress={handleStopAndSummarize}>
              <Text style={styles.micBtnText}>✓ 结束并整理</Text>
            </Pressable>
            <Pressable style={styles.cancelBtn} onPress={handleCancel}>
              <Text style={styles.cancelText}>取消</Text>
            </Pressable>
          </>
        )}

        {state === 'summarizing' && (
          <View style={[styles.micBtn, styles.micBtnBusy]}>
            <Text style={styles.micBtnText}>AI 整理中…</Text>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    marginBottom: spacing.md,
    padding: spacing.md,
    backgroundColor: colors.background,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  label: {
    fontSize: fontSize.md,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  hint: {
    fontSize: fontSize.sm,
    color: colors.textLight,
    lineHeight: 20,
    marginBottom: spacing.sm,
  },
  unsupported: {
    fontSize: fontSize.sm,
    color: colors.textLight,
    marginBottom: spacing.md,
    lineHeight: 20,
  },
  status: {
    fontSize: fontSize.sm,
    color: colors.primary,
    marginBottom: spacing.sm,
  },
  partialBox: {
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    padding: spacing.sm,
    marginBottom: spacing.sm,
  },
  partialLabel: {
    fontSize: fontSize.sm,
    color: colors.textLight,
    marginBottom: 4,
  },
  partialText: {
    fontSize: fontSize.md,
    color: colors.text,
    lineHeight: 22,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    flexWrap: 'wrap',
  },
  micBtn: {
    flex: 1,
    minWidth: 140,
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
    borderRadius: radius.full,
    alignItems: 'center',
  },
  micBtnActive: {
    backgroundColor: '#2E9E5B',
  },
  micBtnBusy: {
    backgroundColor: colors.textLight,
  },
  micBtnDisabled: {
    opacity: 0.5,
  },
  micBtnText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: fontSize.md,
  },
  cancelBtn: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
  },
  cancelText: {
    color: colors.textLight,
    fontSize: fontSize.md,
  },
});
