import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { getBook } from '../../../src/services/bookService';
import { Book } from '../../../src/types/book';
import { Button } from '../../../src/components/Button';
import { Card } from '../../../src/components/Card';
import { LoadingOverlay } from '../../../src/components/LoadingOverlay';
import { colors, fontSize, radius, spacing } from '../../../src/theme';

export default function AnimeEditScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [book, setBook] = useState<Book | null>(null);
  const [loading, setLoading] = useState(true);

  const loadBook = useCallback(async () => {
    if (!id) return;
    try {
      const data = await getBook(id);
      if (!data?.anime) {
        Alert.alert('错误', '动漫项目不存在');
        return;
      }
      setBook(data);
    } catch (e) {
      Alert.alert('加载失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadBook();
  }, [loadBook]);

  if (loading) {
    return <LoadingOverlay message="加载分镜..." />;
  }

  if (!book?.anime) {
    return (
      <View style={styles.center}>
        <Text>动漫项目不存在</Text>
      </View>
    );
  }

  const { anime } = book;

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.synopsis}>{anime.synopsis}</Text>

        <Card title="👤 主要角色">
          {anime.characters.map((c) => (
            <View key={c.name} style={styles.charRow}>
              <Text style={styles.charName}>{c.name}</Text>
              <Text style={styles.charDesc}>{c.description}</Text>
            </View>
          ))}
        </Card>

        {anime.scripts.map((script) => (
          <Card key={script.index} title={`🎬 ${script.title}`}>
            <Text style={styles.scriptSynopsis}>{script.synopsis}</Text>
            <Text style={styles.meta}>
              {script.shots.length} 个镜头 · {script.segments.length} 段视频（每段 15 秒）
            </Text>
            {script.shots.map((shot, i) => (
              <View key={shot.index} style={styles.shotRow}>
                <Text style={styles.shotLabel}>镜头 {i + 1}</Text>
                <Text style={styles.shotText}>{shot.text}</Text>
                {shot.dialogue ? (
                  <Text style={styles.dialogueText}>💬 {shot.dialogue}</Text>
                ) : null}
              </View>
            ))}
          </Card>
        ))}

        <Button
          title="下一步：生成角色素材 →"
          onPress={() => router.push(`/anime/config/${id}`)}
        />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  synopsis: {
    fontSize: fontSize.md,
    color: colors.text,
    lineHeight: 24,
    marginBottom: spacing.md,
  },
  charRow: { marginBottom: spacing.sm },
  charName: { fontWeight: '700', color: colors.text, fontSize: fontSize.md },
  charDesc: { color: colors.textLight, fontSize: fontSize.sm, marginTop: 2 },
  scriptSynopsis: {
    fontSize: fontSize.sm,
    color: colors.textLight,
    marginBottom: spacing.sm,
    lineHeight: 20,
  },
  meta: {
    fontSize: fontSize.sm,
    color: colors.primary,
    marginBottom: spacing.md,
    fontWeight: '600',
  },
  shotRow: {
    backgroundColor: colors.background,
    borderRadius: radius.md,
    padding: spacing.sm,
    marginBottom: spacing.sm,
  },
  shotLabel: { fontWeight: '600', color: colors.primary, fontSize: fontSize.sm },
  shotText: { color: colors.text, fontSize: fontSize.sm, marginTop: 4, lineHeight: 20 },
  dialogueText: {
    color: colors.text,
    fontSize: fontSize.sm,
    marginTop: 6,
    fontStyle: 'italic',
    lineHeight: 20,
  },
});
