import { useFocusEffect, useRouter } from 'expo-router';
import React, { useCallback, useState } from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { deleteBook, listBooks } from '../src/services/bookService';
import { deleteBookFiles } from '../src/storage/fileStore';
import { BookSummary } from '../src/types/book';
import { colors, fontSize, radius, spacing } from '../src/theme';

export default function HistoryScreen() {
  const router = useRouter();
  const [books, setBooks] = useState<BookSummary[]>([]);

  const load = useCallback(async () => {
    const items = await listBooks();
    setBooks(items);
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const handleOpen = (book: BookSummary) => {
    if (book.content_type === 'anime') {
      if (book.has_images) {
        router.push(`/anime/preview/${book.id}`);
      } else {
        router.push(`/anime/edit/${book.id}`);
      }
      return;
    }
    if (book.has_images) {
      router.push(`/preview/${book.id}`);
    } else {
      router.push(`/edit/${book.id}`);
    }
  };

  const handleDelete = (book: BookSummary) => {
    const label = book.content_type === 'anime' ? '动漫' : '绘本';
    Alert.alert(`删除${label}`, `确定删除「${book.character}的故事」吗？`, [
      { text: '取消', style: 'cancel' },
      {
        text: '删除',
        style: 'destructive',
        onPress: async () => {
          await deleteBookFiles(book.id);
          await deleteBook(book.id);
          load();
        },
      },
    ]);
  };

  return (
    <ScrollView contentContainerStyle={styles.scroll}>
      {books.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>还没有绘本记录</Text>
          <Text style={styles.emptyHint}>创作的故事会自动保存在这里</Text>
        </View>
      ) : (
        books.map((book) => (
          <Pressable
            key={book.id}
            style={styles.item}
            onPress={() => handleOpen(book)}
            onLongPress={() => handleDelete(book)}
          >
            <View style={styles.itemHeader}>
              <Text style={styles.itemTitle}>
                {book.title ?? `${book.character}的故事`}
              </Text>
              <Text style={styles.badge}>
                {book.content_type === 'anime' ? '🎬 ' : ''}
                {book.has_images ? '✅ 已完成' : '📝 草稿'}
              </Text>
            </View>
            <Text style={styles.itemIdea} numberOfLines={2}>
              {book.idea}
            </Text>
            <Text style={styles.itemMeta}>
              {book.content_type === 'anime' ? '动漫' : `${book.num_scenes} 个场景`} ·{' '}
              {new Date(book.created_at).toLocaleDateString('zh-CN')}
            </Text>
          </Pressable>
        ))
      )}
      {books.length > 0 && (
        <Text style={styles.tip}>长按可删除绘本</Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  empty: { alignItems: 'center', paddingTop: spacing.xl * 2 },
  emptyText: { fontSize: fontSize.lg, color: colors.text, fontWeight: '600' },
  emptyHint: {
    fontSize: fontSize.md,
    color: colors.textLight,
    marginTop: spacing.sm,
  },
  item: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  itemTitle: {
    fontSize: fontSize.lg,
    fontWeight: '700',
    color: colors.text,
    flex: 1,
  },
  badge: { fontSize: fontSize.sm, color: colors.primary },
  itemIdea: {
    fontSize: fontSize.md,
    color: colors.textLight,
    marginBottom: spacing.sm,
    lineHeight: 22,
  },
  itemMeta: { fontSize: fontSize.sm, color: colors.textLight },
  tip: {
    textAlign: 'center',
    fontSize: fontSize.sm,
    color: colors.textLight,
    marginTop: spacing.md,
  },
});
