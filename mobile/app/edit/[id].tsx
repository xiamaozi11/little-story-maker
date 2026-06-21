import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Book, getBook, updateSceneText } from '../../src/services/bookService';
import { Button } from '../../src/components/Button';
import { Card } from '../../src/components/Card';
import { LoadingOverlay } from '../../src/components/LoadingOverlay';
import { colors, fontSize, radius, spacing } from '../../src/theme';

export default function EditScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [book, setBook] = useState<Book | null>(null);
  const [editedTexts, setEditedTexts] = useState<Record<number, string>>({});
  const [saving, setSaving] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const loadBook = useCallback(async () => {
    if (!id) return;
    try {
      const data = await getBook(id);
      if (!data) {
        Alert.alert('错误', '绘本不存在');
        return;
      }
      setBook(data);
      const texts: Record<number, string> = {};
      data.scenes.forEach((s) => {
        texts[s.index] = s.text;
      });
      setEditedTexts(texts);
    } catch (e) {
      Alert.alert('加载失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadBook();
  }, [loadBook]);

  const saveScene = async (index: number) => {
    if (!id) return;
    setSaving(index);
    try {
      const updated = await updateSceneText(id, index, editedTexts[index]);
      setBook(updated);
      Alert.alert('已保存', `场景 ${index + 1} 已更新`);
    } catch (e) {
      Alert.alert('保存失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setSaving(null);
    }
  };

  if (loading) {
    return <LoadingOverlay message="加载故事中..." />;
  }

  if (!book) {
    return (
      <View style={styles.center}>
        <Text>绘本不存在</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.info}>
          ✅ 共 {book.scenes.length} 个场景，确认内容后可生成插画
        </Text>

        {book.scenes.map((scene) => (
          <Card key={scene.index} title={`📖 场景 ${scene.scene_number}`}>
            <TextInput
              style={styles.textArea}
              value={editedTexts[scene.index] ?? scene.text}
              onChangeText={(t) =>
                setEditedTexts((prev) => ({ ...prev, [scene.index]: t }))
              }
              multiline
              numberOfLines={4}
            />
            <Button
              title="💾 保存修改"
              variant="outline"
              loading={saving === scene.index}
              onPress={() => saveScene(scene.index)}
              style={styles.saveBtn}
            />
          </Card>
        ))}

        <Button
          title="下一步：配置图片 →"
          onPress={() => router.push(`/config/${id}`)}
        />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  info: {
    fontSize: fontSize.md,
    color: colors.success,
    marginBottom: spacing.md,
    fontWeight: '600',
  },
  textArea: {
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    fontSize: fontSize.md,
    color: colors.text,
    minHeight: 100,
    textAlignVertical: 'top',
    marginBottom: spacing.sm,
  },
  saveBtn: { marginTop: spacing.xs },
});
