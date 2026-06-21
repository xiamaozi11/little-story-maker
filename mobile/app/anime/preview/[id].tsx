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
import { getBook } from '../../../src/services/bookService';
import { regenerateAnimeSegment } from '../../../src/services/animeService';
import { isConfiguredForSeedance } from '../../../src/services/settings';
import { openVideoUri } from '../../../src/services/videoPlayerService';
import { Book } from '../../../src/types/book';
import { Button } from '../../../src/components/Button';
import { Card } from '../../../src/components/Card';
import { LoadingOverlay } from '../../../src/components/LoadingOverlay';
import { colors, fontSize, radius, spacing } from '../../../src/theme';

export default function AnimePreviewScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [book, setBook] = useState<Book | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [selectedScript, setSelectedScript] = useState(0);
  const [selectedSegment, setSelectedSegment] = useState(0);

  const loadBook = useCallback(async () => {
    if (!id) return;
    try {
      const data = await getBook(id);
      setBook(data);
    } catch (e) {
      Alert.alert('加载失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setInitialLoading(false);
    }
  }, [id]);

  const handleRegenerateSegment = useCallback(async () => {
    if (!id || !book?.anime) return;
    const ok = await isConfiguredForSeedance();
    if (!ok) {
      Alert.alert('请先配置 Seedance', '请在设置中填写 Seedance API Key');
      return;
    }

    setRegenerating(true);
    setProgressMsg('重新生成视频段...');
    try {
      const result = await regenerateAnimeSegment(
        id,
        selectedScript,
        selectedSegment,
        (msg) => setProgressMsg(msg)
      );
      setBook(result.book);
      if (result.failedSegments.length > 0) {
        Alert.alert('生成失败', result.failedDetails[0] ?? '未知错误');
      } else {
        Alert.alert('完成', '本段及后续段已重新生成');
      }
    } catch (e) {
      Alert.alert('重新生成失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setRegenerating(false);
      setProgressMsg('');
    }
  }, [id, book, selectedScript, selectedSegment]);

  useEffect(() => {
    loadBook();
  }, [loadBook]);

  const openVideo = async (uri?: string) => {
    if (!uri) {
      Alert.alert('提示', '视频尚未生成');
      return;
    }
    try {
      await openVideoUri(uri);
    } catch (e) {
      Alert.alert('打开失败', e instanceof Error ? e.message : '未知错误');
    }
  };

  if (initialLoading) {
    return <LoadingOverlay message="加载预览..." />;
  }

  if (!book?.anime?.has_videos) {
    const hasSegments = book?.anime?.scripts.some((s) =>
      s.segments.some((seg) => seg.status === 'ok')
    );
    if (!hasSegments) {
      return (
        <View style={styles.center}>
          <Text style={styles.emptyText}>暂无视频，请先生成动漫</Text>
          <Button
            title="返回配置"
            onPress={() => router.push(`/anime/config/${id}`)}
            style={{ marginTop: spacing.lg }}
          />
        </View>
      );
    }
  }

  const anime = book!.anime!;
  const script = anime.scripts[selectedScript];
  const segment = script?.segments[selectedSegment];

  return (
    <View style={styles.container}>
      {regenerating && <LoadingOverlay message={progressMsg || '处理中...'} />}
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>{script?.title ?? '动漫预览'}</Text>
        <Text style={styles.synopsis}>{script?.synopsis}</Text>

        <View style={styles.tabRow}>
          {anime.scripts.map((s, i) => (
            <Pressable
              key={s.index}
              onPress={() => {
                setSelectedScript(i);
                setSelectedSegment(0);
              }}
              style={[styles.tab, selectedScript === i && styles.tabActive]}
            >
              <Text
                style={[
                  styles.tabText,
                  selectedScript === i && styles.tabTextActive,
                ]}
              >
                {s.title}
              </Text>
            </Pressable>
          ))}
        </View>

        {script && (
          <Card title="🎞️ 视频段（每段 15 秒）">
            {script.segments.map((seg, i) => (
              <Pressable
                key={seg.segment_index}
                onPress={() => setSelectedSegment(i)}
                style={[
                  styles.segItem,
                  selectedSegment === i && styles.segItemActive,
                ]}
              >
                <Text style={styles.segLabel}>
                  第 {i + 1} 段 ·{' '}
                  {seg.status === 'ok'
                    ? '✅ 已完成'
                    : seg.status === 'failed'
                      ? '❌ 失败'
                      : seg.status === 'generating'
                        ? '⏳ 生成中'
                        : '⏸ 待生成'}
                </Text>
                {seg.error && (
                  <Text style={styles.errorText} numberOfLines={2}>
                    {seg.error}
                  </Text>
                )}
              </Pressable>
            ))}
          </Card>
        )}

        {segment && (
          <Card title={`镜头列表（第 ${selectedSegment + 1} 段）`}>
            {segment.shots.map((shot, i) => (
              <View key={shot.index} style={styles.shotRow}>
                <Text style={styles.shotLabel}>镜头 {i + 1}</Text>
                <Text style={styles.shotText}>{shot.text}</Text>
              </View>
            ))}

            <Button
              title="▶️ 播放本段视频"
              onPress={() => openVideo(segment.video_path ?? segment.video_url)}
              disabled={segment.status !== 'ok'}
              style={{ marginTop: spacing.md }}
            />
            {(segment.status === 'failed' || segment.status === 'pending') && (
              <Button
                title="🔄 重新生成本段"
                variant="outline"
                onPress={handleRegenerateSegment}
                loading={regenerating}
                style={{ marginTop: spacing.sm }}
              />
            )}
          </Card>
        )}

        <Card title="👤 角色参考">
          {anime.characters.map((c) => (
            <View key={c.name} style={styles.charRow}>
              {c.image_path ? (
                <Image source={{ uri: c.image_path }} style={styles.charThumb} />
              ) : null}
              <Text style={styles.charName}>{c.name}</Text>
            </View>
          ))}
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  emptyText: { fontSize: fontSize.md, color: colors.textLight },
  title: {
    fontSize: fontSize.xl,
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  synopsis: {
    fontSize: fontSize.md,
    color: colors.textLight,
    marginBottom: spacing.md,
    lineHeight: 22,
  },
  tabRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.md },
  tab: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.full,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
  },
  tabActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  tabText: { fontSize: fontSize.sm, color: colors.text },
  tabTextActive: { color: '#fff', fontWeight: '600' },
  segItem: {
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.background,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  segItemActive: { borderColor: colors.primary, backgroundColor: '#FFF0E6' },
  segLabel: { fontWeight: '600', color: colors.text },
  errorText: { fontSize: fontSize.sm, color: colors.error, marginTop: 4 },
  shotRow: {
    backgroundColor: colors.background,
    borderRadius: radius.md,
    padding: spacing.sm,
    marginBottom: spacing.sm,
  },
  shotLabel: { fontWeight: '600', color: colors.primary, fontSize: fontSize.sm },
  shotText: { color: colors.text, fontSize: fontSize.sm, marginTop: 4 },
  charRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  charThumb: { width: 48, height: 64, borderRadius: radius.sm },
  charName: { fontSize: fontSize.md, color: colors.text },
});
