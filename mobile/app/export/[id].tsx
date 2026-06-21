import * as Sharing from 'expo-sharing';
import { useLocalSearchParams } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Book, exportPdf, getBook } from '../../src/services/bookService';
import { Button } from '../../src/components/Button';
import { Card } from '../../src/components/Card';
import { Input } from '../../src/components/Input';
import { LoadingOverlay } from '../../src/components/LoadingOverlay';
import { colors, fontSize, spacing } from '../../src/theme';

export default function ExportScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [book, setBook] = useState<Book | null>(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('云朵爸爸');
  const [loading, setLoading] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [pdfPath, setPdfPath] = useState<string | null>(null);
  const [pdfSizeMb, setPdfSizeMb] = useState(0);

  useEffect(() => {
    if (id) {
      getBook(id).then((b) => {
        if (!b) return;
        setBook(b);
        setTitle(b.title ?? `${b.character}的故事`);
        setAuthor(b.author ?? '云朵爸爸');
        if (b.pdf_path) {
          setPdfPath(b.pdf_path);
        }
      });
    }
  }, [id]);

  const handleGenerate = useCallback(async () => {
    if (!id || !title.trim()) {
      Alert.alert('提示', '请输入绘本标题');
      return;
    }
    setLoading(true);
    try {
      const { book: updated, sizeMb } = await exportPdf(
        id,
        title.trim(),
        author.trim()
      );
      setBook(updated);
      setPdfPath(updated.pdf_path ?? null);
      setPdfSizeMb(sizeMb);
      Alert.alert('成功', 'PDF 已生成并保存在本地！');
    } catch (e) {
      Alert.alert('生成失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setLoading(false);
    }
  }, [id, title, author]);

  const handleShare = useCallback(async () => {
    if (!pdfPath) return;
    setSharing(true);
    try {
      const canShare = await Sharing.isAvailableAsync();
      if (canShare) {
        await Sharing.shareAsync(pdfPath, {
          mimeType: 'application/pdf',
          dialogTitle: '分享绘本 PDF',
        });
      } else {
        Alert.alert('已保存', `PDF 路径：\n${pdfPath}`);
      }
    } catch (e) {
      Alert.alert('分享失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setSharing(false);
    }
  }, [pdfPath]);

  return (
    <View style={styles.container}>
      {loading && <LoadingOverlay message="正在生成 PDF..." />}

      <ScrollView contentContainerStyle={styles.scroll}>
        {book && (
          <Text style={styles.info}>
            📖 {book.scenes.length} 个场景已就绪，填写信息后导出
          </Text>
        )}

        <Card title="📄 PDF 信息">
          <Input label="绘本标题" value={title} onChangeText={setTitle} />
          <Input label="作者" value={author} onChangeText={setAuthor} />
        </Card>

        <Button title="📄 生成 PDF" onPress={handleGenerate} loading={loading} />

        {pdfPath && (
          <Card title="✅ PDF 已就绪" style={styles.resultCard}>
            {pdfSizeMb > 0 && (
              <Text style={styles.resultText}>文件大小：约 {pdfSizeMb} MB</Text>
            )}
            <Button
              title="📤 分享 PDF"
              variant="secondary"
              onPress={handleShare}
              loading={sharing}
              style={{ marginTop: spacing.md }}
            />
          </Card>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  info: {
    fontSize: fontSize.md,
    color: colors.textLight,
    marginBottom: spacing.md,
  },
  resultCard: { marginTop: spacing.lg },
  resultText: {
    fontSize: fontSize.md,
    color: colors.success,
    fontWeight: '600',
  },
});
