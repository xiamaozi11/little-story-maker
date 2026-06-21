import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { APP_CONFIG, getBook } from '../../../src/services/bookService';
import {
  DEFAULT_ANIME_IMAGE_STYLE,
  generateAnimeCharacterAssets,
  generateAnimeVideos,
  regenerateFailedAnimeVideos,
} from '../../../src/services/animeService';
import { isConfiguredForImages, isConfiguredForSeedance } from '../../../src/services/settings';
import { Book } from '../../../src/types/book';
import { Button } from '../../../src/components/Button';
import { Card } from '../../../src/components/Card';
import { LoadingOverlay } from '../../../src/components/LoadingOverlay';
import { colors, fontSize, radius, spacing } from '../../../src/theme';

export default function AnimeConfigScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [book, setBook] = useState<Book | null>(null);
  const [imageService, setImageService] = useState<'doubao' | 'tongyi'>('tongyi');
  const [imageStyle] = useState(DEFAULT_ANIME_IMAGE_STYLE);
  const [imageSize, setImageSize] = useState(
    Object.values(APP_CONFIG.tongyi_sizes)[0]
  );
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [step, setStep] = useState<'characters' | 'videos' | 'done'>('characters');

  useEffect(() => {
    if (id) {
      getBook(id).then((b) => {
        setBook(b);
        const allCharsOk = b?.anime?.characters.every((c) => c.image_status === 'ok');
        if (allCharsOk) setStep('videos');
        if (b?.anime?.has_videos) setStep('done');
      });
    }
  }, [id]);

  const handleGenerateCharacters = useCallback(async () => {
    if (!id) return;
    const ok = await isConfiguredForImages(imageService);
    if (!ok) {
      Alert.alert('请先配置 API', '请在设置中填写生图 API Key');
      return;
    }

    setLoading(true);
    setProgressMsg('生成角色素材...');
    try {
      const updated = await generateAnimeCharacterAssets(
        id,
        imageService,
        imageStyle,
        imageSize,
        (msg) => setProgressMsg(msg)
      );
      setBook(updated);
      const failed = updated.anime?.characters.filter((c) => c.image_status === 'failed');
      if (failed?.length) {
        Alert.alert(
          '部分角色素材失败',
          `${failed.map((c) => c.name).join('、')} 生成失败，请重试`
        );
      } else {
        setStep('videos');
        Alert.alert('完成', '主要角色素材已生成，可以开始生成视频');
      }
    } catch (e) {
      Alert.alert('失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setLoading(false);
      setProgressMsg('');
    }
  }, [id, imageService, imageStyle, imageSize]);

  const handleGenerateVideos = useCallback(async () => {
    if (!id) return;
    const ok = await isConfiguredForSeedance();
    if (!ok) {
      Alert.alert('请先配置 Seedance', '请在设置中填写 Seedance API Key');
      return;
    }

    const charsOk = book?.anime?.characters.every((c) => c.image_status === 'ok');
    if (!charsOk) {
      Alert.alert('提示', '请先生成主要角色素材');
      return;
    }

    setLoading(true);
    setProgressMsg('准备生成视频...');
    try {
      const result = await generateAnimeVideos(id, (msg) => setProgressMsg(msg));
      setBook(result.book);
      if (result.failedSegments.length > 0) {
        const detail = result.failedDetails.slice(0, 3).join('\n');
        const more =
          result.failedDetails.length > 3
            ? `\n…共 ${result.failedDetails.length} 段失败`
            : '';
        Alert.alert(
          '部分视频失败',
          `${detail}${more}\n\n已完成 ${result.completedScripts} 个剧本`,
          [{ text: '去预览', onPress: () => router.push(`/anime/preview/${id}`) }]
        );
      } else {
        setStep('done');
        router.push(`/anime/preview/${id}`);
      }
    } catch (e) {
      Alert.alert('视频生成失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setLoading(false);
      setProgressMsg('');
    }
  }, [id, book, router]);

  const handleRegenerateFailed = useCallback(async () => {
    if (!id) return;
    const ok = await isConfiguredForSeedance();
    if (!ok) {
      Alert.alert('请先配置 Seedance', '请在设置中填写 Seedance API Key');
      return;
    }

    setLoading(true);
    setProgressMsg('重新生成失败段...');
    try {
      const result = await regenerateFailedAnimeVideos(id, (msg) => setProgressMsg(msg));
      setBook(result.book);
      if (result.failedSegments.length > 0) {
        const detail = result.failedDetails.slice(0, 3).join('\n');
        Alert.alert('仍有失败', detail);
      } else {
        Alert.alert('完成', '所有失败段已重新生成');
      }
    } catch (e) {
      Alert.alert('重新生成失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setLoading(false);
      setProgressMsg('');
    }
  }, [id]);

  const hasFailedSegments = book?.anime?.scripts.some((s) =>
    s.segments.some((seg) => seg.status === 'failed' || seg.status === 'pending')
  ) && book?.anime?.scripts.some((s) =>
    s.segments.some((seg) => seg.status === 'ok' || seg.status === 'failed')
  );

  const sizeOptions =
    imageService === 'tongyi'
      ? Object.entries(APP_CONFIG.tongyi_sizes)
      : Object.entries(APP_CONFIG.doubao_sizes);

  return (
    <View style={styles.container}>
      {loading && <LoadingOverlay message={progressMsg || '处理中...'} />}

      <ScrollView contentContainerStyle={styles.scroll}>
        <Card title="📋 生成流程">
          <Text style={styles.hint}>
            1. 先生成主要角色参考立绘（Seedance 每段视频都会引用）{'\n'}
            2. 按剧本串行生成 15 秒视频段（每 5 镜头一段，最多 60 秒/剧本）{'\n'}
            3. 上一段完成后，以其最后一帧衔接下一段
          </Text>
        </Card>

        {step === 'characters' && (
          <Card title="👤 步骤一：角色素材">
            <Text style={styles.pickerLabel}>生图服务</Text>
            <View style={styles.chipRow}>
              {APP_CONFIG.image_services.map((s) => (
                <Pressable
                  key={s.id}
                  onPress={() => {
                    setImageService(s.id as 'doubao' | 'tongyi');
                    const sizes =
                      s.id === 'tongyi'
                        ? APP_CONFIG.tongyi_sizes
                        : APP_CONFIG.doubao_sizes;
                    setImageSize(Object.values(sizes)[0]);
                  }}
                  style={[
                    styles.chip,
                    imageService === s.id && styles.chipActive,
                  ]}
                >
                  <Text
                    style={[
                      styles.chipText,
                      imageService === s.id && styles.chipTextActive,
                    ]}
                  >
                    {s.label}
                  </Text>
                </Pressable>
              ))}
            </View>

            {sizeOptions.map(([label, value]) => (
              <Pressable
                key={value}
                onPress={() => setImageSize(value)}
                style={[
                  styles.sizeOption,
                  imageSize === value && styles.sizeOptionActive,
                ]}
              >
                <Text
                  style={[
                    styles.sizeText,
                    imageSize === value && styles.sizeTextActive,
                  ]}
                >
                  {label}
                </Text>
              </Pressable>
            ))}

            {book?.anime?.characters.map((c) => (
              <View key={c.name} style={styles.charPreview}>
                <Text style={styles.charName}>
                  {c.name}{' '}
                  {c.image_status === 'ok'
                    ? '✅'
                    : c.image_status === 'failed'
                      ? '❌'
                      : '⏳'}
                </Text>
                {c.image_path && (
                  <Image source={{ uri: c.image_path }} style={styles.charImg} />
                )}
              </View>
            ))}

            <Button
              title="🎨 生成主要角色素材"
              onPress={handleGenerateCharacters}
              loading={loading}
              style={{ marginTop: spacing.md }}
            />
          </Card>
        )}

        {(step === 'videos' || step === 'done') && (
          <Card title="🎬 步骤二：动漫视频">
            <Text style={styles.hint}>
              每段 15 秒，共 {book?.anime?.scripts.length ?? 0} 个剧本。
              生成时间较长，请保持网络畅通。
            </Text>
            <Button
              title="🎥 开始生成动漫视频"
              onPress={handleGenerateVideos}
              loading={loading}
            />
            {step === 'done' && (
              <>
                <Button
                  title="查看预览"
                  variant="outline"
                  onPress={() => router.push(`/anime/preview/${id}`)}
                  style={{ marginTop: spacing.sm }}
                />
                {hasFailedSegments && (
                  <Button
                    title="🔄 重新生成失败段"
                    variant="outline"
                    onPress={handleRegenerateFailed}
                    loading={loading}
                    style={{ marginTop: spacing.sm }}
                  />
                )}
              </>
            )}
            {step === 'videos' && hasFailedSegments && (
              <Button
                title="🔄 重新生成失败段"
                variant="outline"
                onPress={handleRegenerateFailed}
                loading={loading}
                style={{ marginTop: spacing.sm }}
              />
            )}
          </Card>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  hint: {
    fontSize: fontSize.sm,
    color: colors.textLight,
    lineHeight: 22,
    marginBottom: spacing.sm,
  },
  pickerLabel: {
    fontSize: fontSize.md,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.md },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.full,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipText: { fontSize: fontSize.sm, color: colors.text },
  chipTextActive: { color: '#fff', fontWeight: '600' },
  sizeOption: {
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.sm,
  },
  sizeOptionActive: { borderColor: colors.primary, backgroundColor: '#FFF0E6' },
  sizeText: { fontSize: fontSize.sm, color: colors.text },
  sizeTextActive: { color: colors.primary, fontWeight: '600' },
  charPreview: { marginTop: spacing.md },
  charName: { fontWeight: '600', marginBottom: spacing.sm },
  charImg: { width: 120, height: 160, borderRadius: radius.md },
});
