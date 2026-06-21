import { Link, useRouter } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Button } from '../src/components/Button';
import { Card } from '../src/components/Card';
import { Input } from '../src/components/Input';
import { LoadingOverlay } from '../src/components/LoadingOverlay';
import { VoiceIdeaInput } from '../src/components/VoiceIdeaInput';
import { APP_CONFIG, createStory } from '../src/services/bookService';
import { createAnimeStory } from '../src/services/animeService';
import { isConfiguredForText } from '../src/services/settings';
import { colors, fontSize, spacing } from '../src/theme';

type CreateMode = 'book' | 'anime';

export default function HomeScreen() {
  const router = useRouter();
  const [mode, setMode] = useState<CreateMode>('book');
  const [idea, setIdea] = useState('');
  const [character, setCharacter] = useState('');
  const [numScenes, setNumScenes] = useState(APP_CONFIG.default_scenes);
  const [numSegments, setNumSegments] = useState(APP_CONFIG.default_anime_segments);
  const [loading, setLoading] = useState(false);
  const [configured, setConfigured] = useState<boolean | null>(null);

  useEffect(() => {
    isConfiguredForText().then(setConfigured);
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!idea.trim()) {
      Alert.alert('提示', '请输入故事创意');
      return;
    }
    if (!character.trim()) {
      Alert.alert('提示', '请输入主角名字');
      return;
    }

    const ok = await isConfiguredForText();
    if (!ok) {
      Alert.alert('请先配置 API', '请前往设置页填写百炼 API Key', [
        { text: '去设置', onPress: () => router.push('/settings') },
        { text: '取消', style: 'cancel' },
      ]);
      return;
    }

    setLoading(true);
    try {
      if (mode === 'anime') {
        const book = await createAnimeStory(idea.trim(), character.trim(), numSegments);
        router.push(`/anime/edit/${book.id}`);
      } else {
        const book = await createStory(idea.trim(), character.trim(), numScenes);
        router.push(`/edit/${book.id}`);
      }
    } catch (e) {
      Alert.alert('生成失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setLoading(false);
    }
  }, [idea, character, numScenes, numSegments, mode, router]);

  return (
    <View style={styles.container}>
      {loading && (
        <LoadingOverlay
          message={mode === 'anime' ? 'AI 正在创作动漫分镜...' : 'AI 正在创作故事...'}
        />
      )}

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.topBar}>
          <Link href="/history" asChild>
            <Pressable style={styles.linkBtn}>
              <Text style={styles.linkText}>📚 历史</Text>
            </Pressable>
          </Link>
          <Link href="/settings" asChild>
            <Pressable style={styles.linkBtn}>
              <Text style={styles.linkText}>⚙️ 设置</Text>
            </Pressable>
          </Link>
        </View>

        {configured === false && (
          <View style={styles.warning}>
            <Text style={styles.warningText}>
              ⚠️ 请先在设置中填写百炼 API Key，才能生成故事
            </Text>
          </View>
        )}

        <Text style={styles.hero}>为孩子创造专属故事</Text>
        <Text style={styles.subtitle}>纯本地运行，历史保存在手机</Text>

        <View style={styles.modeRow}>
          <Pressable
            onPress={() => setMode('book')}
            style={[styles.modeBtn, mode === 'book' && styles.modeBtnActive]}
          >
            <Text style={[styles.modeText, mode === 'book' && styles.modeTextActive]}>
              📚 绘本
            </Text>
          </Pressable>
          <Pressable
            onPress={() => setMode('anime')}
            style={[styles.modeBtn, mode === 'anime' && styles.modeBtnActive]}
          >
            <Text style={[styles.modeText, mode === 'anime' && styles.modeTextActive]}>
              🎬 动漫
            </Text>
          </Pressable>
        </View>

        <Card title={mode === 'anime' ? '🎬 动漫创作' : '📝 故事创作'}>
          <VoiceIdeaInput
            character={character}
            onIdeaReady={setIdea}
            disabled={loading}
          />
          <Input
            label="故事创意"
            hint="可文字输入，或用上方语音输入（本地 MNN 识别 + 百炼整理）"
            value={idea}
            onChangeText={setIdea}
            placeholder="例如：小兔子在森林里发现了一颗神奇的种子..."
            multiline
            numberOfLines={5}
            style={styles.textArea}
            maxLength={500}
          />
          <Input
            label="主角名字"
            value={character}
            onChangeText={setCharacter}
            placeholder="例如：小兔子、朵朵"
            maxLength={20}
          />

          {mode === 'book' && (
            <>
              <Text style={styles.label}>故事长度：{numScenes} 个场景</Text>
              <View style={styles.stepper}>
                <Button
                  title="−"
                  variant="outline"
                  onPress={() =>
                    setNumScenes((n) => Math.max(APP_CONFIG.min_scenes, n - 1))
                  }
                  style={styles.stepBtn}
                />
                <Text style={styles.stepValue}>{numScenes}</Text>
                <Button
                  title="+"
                  variant="outline"
                  onPress={() =>
                    setNumScenes((n) => Math.min(APP_CONFIG.max_scenes, n + 1))
                  }
                  style={styles.stepBtn}
                />
              </View>
            </>
          )}

          {mode === 'anime' && (
            <>
              <Text style={styles.label}>短视频段数（每段 15 秒）</Text>
              <View style={styles.chipRow}>
                {Array.from(
                  {
                    length:
                      APP_CONFIG.max_anime_segments - APP_CONFIG.min_anime_segments + 1,
                  },
                  (_, i) => APP_CONFIG.min_anime_segments + i
                ).map((n) => (
                  <Pressable
                    key={n}
                    onPress={() => setNumSegments(n)}
                    style={[styles.chip, numSegments === n && styles.chipActive]}
                  >
                    <Text
                      style={[
                        styles.chipText,
                        numSegments === n && styles.chipTextActive,
                      ]}
                    >
                      {n} 段 · {n * 15} 秒
                    </Text>
                  </Pressable>
                ))}
              </View>
            </>
          )}
        </Card>

        <Button
          title={mode === 'anime' ? '🎬 生成动漫分镜' : '📝 生成故事'}
          onPress={handleGenerate}
          loading={loading}
        />

        <Card title="💡 使用步骤" style={styles.helpCard}>
          {mode === 'anime' ? (
            <>
              <Text style={styles.helpText}>1. 配置百炼 API + Seedance API Key</Text>
              <Text style={styles.helpText}>2. 输入创意（语音/文字），生成分镜剧本</Text>
              <Text style={styles.helpText}>3. 生成主要角色参考立绘</Text>
              <Text style={styles.helpText}>4. 串行生成 15 秒视频段（可选 1~4 段，共 15~60 秒）</Text>
            </>
          ) : (
            <>
              <Text style={styles.helpText}>1. 在设置中填写 API Key</Text>
              <Text style={styles.helpText}>2. 输入创意（文字或语音），生成并编辑故事</Text>
              <Text style={styles.helpText}>3. 选择风格，生成插画</Text>
              <Text style={styles.helpText}>4. 预览后导出 PDF 绘本</Text>
            </>
          )}
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  linkBtn: { padding: spacing.sm },
  linkText: { fontSize: fontSize.md, color: colors.primary, fontWeight: '600' },
  hero: {
    fontSize: fontSize.xl,
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  subtitle: {
    fontSize: fontSize.md,
    color: colors.textLight,
    marginBottom: spacing.lg,
  },
  warning: {
    backgroundColor: '#FFF3CD',
    padding: spacing.md,
    borderRadius: 12,
    marginBottom: spacing.md,
  },
  warningText: { color: '#856404', fontSize: fontSize.sm },
  label: {
    fontSize: fontSize.md,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  stepper: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    marginBottom: spacing.sm,
  },
  stepBtn: { width: 56, minHeight: 44, paddingVertical: spacing.sm },
  stepValue: {
    fontSize: fontSize.xl,
    fontWeight: '700',
    color: colors.primary,
    minWidth: 48,
    textAlign: 'center',
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 12,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  chipText: { fontSize: fontSize.sm, color: colors.text },
  chipTextActive: { color: '#fff', fontWeight: '600' },
  textArea: { minHeight: 120, textAlignVertical: 'top' },
  modeRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.lg,
  },
  modeBtn: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: 12,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  modeBtnActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  modeText: { fontSize: fontSize.md, fontWeight: '600', color: colors.text },
  modeTextActive: { color: '#fff' },
  helpCard: { marginTop: spacing.lg },
  helpText: {
    fontSize: fontSize.md,
    color: colors.textLight,
    marginBottom: spacing.sm,
    lineHeight: 24,
  },
});
