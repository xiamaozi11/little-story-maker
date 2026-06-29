import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import React, { useCallback, useRef, useState } from 'react';
import {
  Alert,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {
  hydrateAnimeVideoFiles,
  loadAnimeBook,
  mergeAnimeScriptVideo,
  regenerateAnimeSegment,
} from '../../../src/services/animeService';
import { isConfiguredForSeedance } from '../../../src/services/settings';
import { openVideoUri } from '../../../src/services/videoPlayerService';
import { AnimeScript } from '../../../src/types/anime';
import { Book } from '../../../src/types/book';
import { Button } from '../../../src/components/Button';
import { Card } from '../../../src/components/Card';
import { LoadingOverlay } from '../../../src/components/LoadingOverlay';
import { colors, fontSize, radius, spacing } from '../../../src/theme';

function segmentStatusLabel(status: string): string {
  if (status === 'ok') return '✅ 已完成';
  if (status === 'failed') return '❌ 失败';
  if (status === 'generating') return '⏳ 生成中';
  return '⏸ 待生成';
}

function canMergeScript(script: AnimeScript): boolean {
  const playable = script.segments.filter(
    (s) => s.status === 'ok' || Boolean(s.video_path || s.video_url)
  );
  return playable.length >= 2 && playable.length === script.segments.length;
}

function hasMergedVideo(script: AnimeScript): boolean {
  return Boolean(
    script.merged_video_path &&
      (script.merged_video_status === 'ok' || !script.merged_video_status)
  );
}

export default function AnimePreviewScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [book, setBook] = useState<Book | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [merging, setMerging] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [selectedScript, setSelectedScript] = useState(0);
  const [selectedSegment, setSelectedSegment] = useState(0);

  const firstLoad = useRef(true);

  const loadBook = useCallback(async (showSpinner = false) => {
    if (!id) return;
    if (showSpinner) setInitialLoading(true);
    try {
      const data = await loadAnimeBook(id);
      setBook(data);
    } catch (e) {
      Alert.alert('加载失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      if (showSpinner) setInitialLoading(false);
    }
  }, [id]);

  useFocusEffect(
    useCallback(() => {
      loadBook(firstLoad.current);
      firstLoad.current = false;
    }, [loadBook])
  );

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
      const refreshed = await hydrateAnimeVideoFiles(result.book);
      setBook(refreshed);
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

  const handleMergeScript = useCallback(async () => {
    if (!id || !book?.anime) return;
    setMerging(true);
    setProgressMsg('合成完整视频中...');
    try {
      await mergeAnimeScriptVideo(id, selectedScript, (msg) => setProgressMsg(msg));
      await loadBook(false);
      Alert.alert('合成完成', '完整视频已保存，可在下方播放');
    } catch (e) {
      await loadBook(false);
      Alert.alert('合成失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setMerging(false);
      setProgressMsg('');
    }
  }, [id, book, selectedScript, loadBook]);

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

  const hasAnySegment = book?.anime?.scripts.some((s) =>
    s.segments.some((seg) => seg.status === 'ok' || seg.video_path || seg.video_url)
  );

  if (!book?.anime || (!book.anime.has_videos && !hasAnySegment)) {
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

  const anime = book.anime;
  const script = anime.scripts[selectedScript];
  const segment = script?.segments[selectedSegment];
  const mergeReady = script ? canMergeScript(script) : false;
  const mergedReady = script ? hasMergedVideo(script) : false;
  const totalSeconds = (script?.segments.length ?? 0) * 15;

  return (
    <View style={styles.container}>
      {(regenerating || merging) && (
        <LoadingOverlay message={progressMsg || '处理中...'} />
      )}
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
                style={[styles.tabText, selectedScript === i && styles.tabTextActive]}
              >
                {s.title}
              </Text>
            </Pressable>
          ))}
        </View>

        {script && (
          <Card title="🎬 视频">
            {mergedReady && (
              <View style={styles.mergedRow}>
                <View style={styles.mergedInfo}>
                  <Text style={styles.mergedTitle}>完整视频</Text>
                  <Text style={styles.mergedMeta}>
                    共 {script.segments.length} 段 · {totalSeconds} 秒
                  </Text>
                </View>
                <Pressable
                  style={styles.playChip}
                  onPress={() => openVideo(script.merged_video_path)}
                >
                  <Text style={styles.playChipText}>▶️ 播放</Text>
                </Pressable>
              </View>
            )}

            <Text style={styles.sectionLabel}>分段视频（每段 15 秒）</Text>
            {script.segments.map((seg, i) => {
              const playable =
                seg.status === 'ok' || Boolean(seg.video_path || seg.video_url);
              return (
                <Pressable
                  key={seg.segment_index}
                  onPress={() => setSelectedSegment(i)}
                  style={[
                    styles.segItem,
                    selectedSegment === i && styles.segItemActive,
                  ]}
                >
                  <View style={styles.segRow}>
                    <View style={styles.segInfo}>
                      <Text style={styles.segLabel}>
                        第 {i + 1} 段 · {segmentStatusLabel(seg.status)}
                      </Text>
                      {seg.error && (
                        <Text style={styles.errorText} numberOfLines={2}>
                          {seg.error}
                        </Text>
                      )}
                    </View>
                    {playable && (
                      <Pressable
                        style={styles.playChipSmall}
                        onPress={(e) => {
                          e.stopPropagation?.();
                          openVideo(seg.video_path ?? seg.video_url);
                        }}
                      >
                        <Text style={styles.playChipText}>▶️</Text>
                      </Pressable>
                    )}
                  </View>
                </Pressable>
              );
            })}

            {mergeReady && (
              <>
                {script.merged_video_error && (
                  <Text style={styles.errorText}>{script.merged_video_error}</Text>
                )}
                <Button
                  title={
                    mergedReady
                      ? '🔄 重新合成完整视频'
                      : '🎬 合成完整视频（合并多段）'
                  }
                  onPress={handleMergeScript}
                  loading={merging}
                  style={{ marginTop: spacing.md }}
                />
                {!mergedReady && (
                  <Text style={styles.mergeHint}>
                    可将 {script.segments.length} 段历史视频合并为一条完整动漫短片
                  </Text>
                )}
              </>
            )}
          </Card>
        )}

        {segment && (
          <Card title={`镜头列表（第 ${selectedSegment + 1} 段）`}>
            {segment.shots.map((shot, i) => (
              <View key={shot.index} style={styles.shotRow}>
                <Text style={styles.shotLabel}>镜头 {i + 1}</Text>
                <Text style={styles.shotText}>{shot.text}</Text>
                {shot.dialogue ? (
                  <Text style={styles.dialogueText}>💬 {shot.dialogue}</Text>
                ) : null}
              </View>
            ))}

            <Button
              title="▶️ 播放本段视频"
              onPress={() => openVideo(segment.video_path ?? segment.video_url)}
              disabled={!segmentIsPlayable(segment)}
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

function segmentIsPlayable(seg: {
  status: string;
  video_path?: string;
  video_url?: string;
}): boolean {
  return seg.status === 'ok' || Boolean(seg.video_path || seg.video_url);
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
  sectionLabel: {
    fontSize: fontSize.sm,
    color: colors.textLight,
    marginBottom: spacing.sm,
    marginTop: spacing.xs,
  },
  mergedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: '#E8F5E9',
    borderWidth: 1,
    borderColor: '#A5D6A7',
    marginBottom: spacing.md,
  },
  mergedInfo: { flex: 1, marginRight: spacing.sm },
  mergedTitle: { fontWeight: '700', fontSize: fontSize.md, color: colors.text },
  mergedMeta: { fontSize: fontSize.sm, color: colors.textLight, marginTop: 2 },
  playChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.full,
    backgroundColor: colors.primary,
  },
  playChipSmall: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radius.full,
    backgroundColor: colors.primary,
    minWidth: 40,
    alignItems: 'center',
  },
  playChipText: { color: '#fff', fontWeight: '600', fontSize: fontSize.sm },
  segItem: {
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.background,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  segItemActive: { borderColor: colors.primary, backgroundColor: '#FFF0E6' },
  segRow: { flexDirection: 'row', alignItems: 'center' },
  segInfo: { flex: 1 },
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
  dialogueText: {
    color: colors.text,
    fontSize: fontSize.sm,
    marginTop: 6,
    fontStyle: 'italic',
    lineHeight: 20,
  },
  mergeHint: {
    fontSize: fontSize.sm,
    color: colors.textLight,
    lineHeight: 20,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
  charRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  charThumb: { width: 48, height: 64, borderRadius: radius.sm },
  charName: { fontSize: fontSize.md, color: colors.text },
});
