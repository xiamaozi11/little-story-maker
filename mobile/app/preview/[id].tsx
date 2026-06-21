import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Dimensions,
  Image,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import {
  Book,
  getBook,
  retrySceneImage,
  updateSceneImagePrompt,
} from '../../src/services/bookService';
import { Button } from '../../src/components/Button';
import { Card } from '../../src/components/Card';
import { LoadingOverlay } from '../../src/components/LoadingOverlay';
import { colors, fontSize, radius, spacing } from '../../src/theme';

const { width } = Dimensions.get('window');

export default function PreviewScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [book, setBook] = useState<Book | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [promptModalVisible, setPromptModalVisible] = useState(false);
  const [promptDraft, setPromptDraft] = useState('');
  const [imageVersion, setImageVersion] = useState<Record<number, number>>({});

  const loadBook = useCallback(async () => {
    if (!id) return;
    try {
      const data = await getBook(id);
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

  const openRegenerateModal = () => {
    if (!book) return;
    setPromptDraft(book.scenes[currentIndex].image_prompt ?? '');
    setPromptModalVisible(true);
  };

  const handleRegenerate = async () => {
    if (!id || !book) return;
    const trimmedPrompt = promptDraft.trim();
    if (!trimmedPrompt) {
      Alert.alert('提示', '请输入图片提示词');
      return;
    }

    setPromptModalVisible(false);
    setRegenerating(true);
    try {
      if (trimmedPrompt !== book.scenes[currentIndex].image_prompt) {
        await updateSceneImagePrompt(id, currentIndex, trimmedPrompt);
      }
      const updated = await retrySceneImage(id, currentIndex, trimmedPrompt);
      setBook(updated);
      const scene = updated.scenes[currentIndex];
      if (scene.image_status === 'ok') {
        setImageVersion((v) => ({ ...v, [currentIndex]: Date.now() }));
        Alert.alert('成功', `场景 ${currentIndex + 1} 插画已重新生成`);
      } else {
        Alert.alert(
          '仍然失败',
          scene.image_error?.includes('inappropriate') ||
            scene.image_error?.includes('Green net')
            ? '内容可能仍不合规，请继续简化提示词（去掉激烈动作、恐怖元素等）后重试'
            : scene.image_error ?? '请稍后重试'
        );
      }
    } catch (e) {
      Alert.alert('重新生成失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setRegenerating(false);
    }
  };

  if (loading) {
    return <LoadingOverlay message="加载预览..." />;
  }

  if (!book || !book.has_images) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyText}>暂无插画，请先生成绘本</Text>
        <Button
          title="返回配置"
          onPress={() => router.back()}
          style={{ marginTop: spacing.lg }}
        />
      </View>
    );
  }

  const scene = book.scenes[currentIndex];
  const total = book.scenes.length;
  const failedCount = book.scenes.filter((s) => s.image_status === 'failed').length;
  const isFailed = scene.image_status === 'failed' || !scene.image_path;
  const imageUri = scene.image_path
    ? imageVersion[currentIndex]
      ? `${scene.image_path}?v=${imageVersion[currentIndex]}`
      : scene.image_path
    : undefined;

  return (
    <View style={styles.container}>
      {regenerating && <LoadingOverlay message="正在重新生成插画..." />}

      <ScrollView contentContainerStyle={styles.scroll}>
        {failedCount > 0 && (
          <View style={styles.warning}>
            <Text style={styles.warningText}>
              ⚠️ {failedCount} 个场景插画未生成，可点击重新生成并修改提示词后重试
            </Text>
          </View>
        )}

        <Text style={styles.pageIndicator}>
          第 {currentIndex + 1} / {total} 页
          {isFailed ? ' · ❌ 未生成' : ' · ✅'}
        </Text>

        <Card>
          {imageUri ? (
            <Image
              key={imageUri}
              source={{ uri: imageUri }}
              style={styles.image}
              resizeMode="cover"
            />
          ) : (
            <View style={styles.placeholder}>
              <Text style={styles.placeholderText}>插画未生成</Text>
              {scene.image_error && (
                <Text style={styles.errorText} numberOfLines={3}>
                  {scene.image_error.includes('inappropriate') ||
                  scene.image_error.includes('Green net')
                    ? '内容审核未通过，请点击重新生成并修改提示词后重试'
                    : scene.image_error.slice(0, 120)}
                </Text>
              )}
            </View>
          )}
          <Text style={styles.sceneTitle}>场景 {scene.scene_number}</Text>
          <Text style={styles.sceneText}>{scene.text}</Text>
          <Button
            title="🔄 重新生成此页插画"
            variant="secondary"
            onPress={openRegenerateModal}
            loading={regenerating}
            style={{ marginTop: spacing.md }}
          />
        </Card>

        <View style={styles.navRow}>
          <Button
            title="← 上一页"
            variant="outline"
            disabled={currentIndex === 0}
            onPress={() => setCurrentIndex((i) => Math.max(0, i - 1))}
            style={styles.navBtn}
          />
          <Button
            title="下一页 →"
            variant="outline"
            disabled={currentIndex >= total - 1}
            onPress={() => setCurrentIndex((i) => Math.min(total - 1, i + 1))}
            style={styles.navBtn}
          />
        </View>

        <Button
          title="📄 导出 PDF"
          onPress={() => router.push(`/export/${id}`)}
          style={{ marginTop: spacing.md }}
        />
      </ScrollView>

      <Modal
        visible={promptModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setPromptModalVisible(false)}
      >
        <Pressable
          style={styles.modalOverlay}
          onPress={() => setPromptModalVisible(false)}
        >
          <Pressable style={styles.modalContent} onPress={() => {}}>
            <Text style={styles.modalTitle}>修改场景 {currentIndex + 1} 图片提示词</Text>
            <Text style={styles.promptHint}>
              若绿网拦截，请改为更温和描述（可爱卡通、温馨明亮、无暴力恐怖）
            </Text>
            <TextInput
              style={styles.promptInput}
              value={promptDraft}
              onChangeText={setPromptDraft}
              multiline
              numberOfLines={6}
              placeholder="输入英文图片提示词..."
              autoFocus
            />
            <View style={styles.modalActions}>
              <Button
                title="取消"
                variant="outline"
                onPress={() => setPromptModalVisible(false)}
                style={styles.modalBtn}
              />
              <Button
                title="重新生成"
                onPress={handleRegenerate}
                loading={regenerating}
                style={styles.modalBtn}
              />
            </View>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  emptyText: { fontSize: fontSize.md, color: colors.textLight },
  warning: {
    backgroundColor: '#FFF3CD',
    padding: spacing.md,
    borderRadius: radius.md,
    marginBottom: spacing.md,
  },
  warningText: { color: '#856404', fontSize: fontSize.sm },
  pageIndicator: {
    textAlign: 'center',
    fontSize: fontSize.md,
    color: colors.primary,
    fontWeight: '700',
    marginBottom: spacing.md,
  },
  image: {
    width: width - spacing.lg * 4,
    height: (width - spacing.lg * 4) * 1.33,
    borderRadius: radius.md,
    marginBottom: spacing.md,
    alignSelf: 'center',
  },
  placeholder: {
    width: width - spacing.lg * 4,
    height: (width - spacing.lg * 4) * 0.8,
    borderRadius: radius.md,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginBottom: spacing.md,
    padding: spacing.md,
  },
  placeholderText: {
    fontSize: fontSize.md,
    color: colors.textLight,
    marginBottom: spacing.sm,
  },
  errorText: {
    fontSize: fontSize.sm,
    color: colors.error,
    textAlign: 'center',
  },
  sceneTitle: {
    fontSize: fontSize.lg,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  sceneText: {
    fontSize: fontSize.md,
    color: colors.text,
    lineHeight: 26,
  },
  promptHint: {
    fontSize: fontSize.sm,
    color: colors.textLight,
    marginBottom: spacing.sm,
    lineHeight: 20,
  },
  promptInput: {
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    fontSize: fontSize.sm,
    color: colors.text,
    minHeight: 100,
    textAlignVertical: 'top',
  },
  navRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.md,
  },
  navBtn: { flex: 1 },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  modalContent: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
  },
  modalTitle: {
    fontSize: fontSize.lg,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  modalActions: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.md,
  },
  modalBtn: { flex: 1 },
});
