import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {
  APP_CONFIG,
  Book,
  generatePictures,
  getBook,
} from '../../src/services/bookService';
import { isConfiguredForImages } from '../../src/services/settings';
import { Button } from '../../src/components/Button';
import { Card } from '../../src/components/Card';
import { LoadingOverlay } from '../../src/components/LoadingOverlay';
import { colors, fontSize, radius, spacing } from '../../src/theme';

function OptionPicker<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { label: string; value: T }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <View style={styles.pickerGroup}>
      <Text style={styles.pickerLabel}>{label}</Text>
      <View style={styles.chipRow}>
        {options.map((opt) => (
          <Pressable
            key={opt.value}
            onPress={() => onChange(opt.value)}
            style={[styles.chip, value === opt.value && styles.chipActive]}
          >
            <Text
              style={[
                styles.chipText,
                value === opt.value && styles.chipTextActive,
              ]}
            >
              {opt.label}
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

export default function ConfigScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [book, setBook] = useState<Book | null>(null);
  const [imageService, setImageService] = useState<'doubao' | 'tongyi'>('tongyi');
  const [imageStyle, setImageStyle] = useState(APP_CONFIG.default_image_style);
  const [imageSize, setImageSize] = useState(
    Object.values(APP_CONFIG.tongyi_sizes)[0]
  );
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');

  useEffect(() => {
    if (id) {
      getBook(id).then(setBook).catch(() => {});
    }
  }, [id]);

  const sizeOptions =
    imageService === 'tongyi'
      ? Object.entries(APP_CONFIG.tongyi_sizes)
      : Object.entries(APP_CONFIG.doubao_sizes);

  const handleServiceChange = (service: 'doubao' | 'tongyi') => {
    setImageService(service);
    const sizes =
      service === 'tongyi'
        ? APP_CONFIG.tongyi_sizes
        : APP_CONFIG.doubao_sizes;
    setImageSize(Object.values(sizes)[0]);
  };

  const handleGenerate = useCallback(async () => {
    if (!id) return;

    const ok = await isConfiguredForImages(imageService);
    if (!ok) {
      const keyName =
        imageService === 'doubao' ? '豆包 ARK API Key' : '百炼 API Key';
      Alert.alert('请先配置 API', `请在设置中填写 ${keyName}`);
      return;
    }

    setLoading(true);
    setProgressMsg('准备中...');
    try {
      const result = await generatePictures(
        id,
        imageService,
        imageStyle,
        imageSize,
        (msg) => setProgressMsg(msg)
      );

      if (result.failedCount > 0) {
        Alert.alert(
          '部分场景生成失败',
          `成功 ${result.successCount} 张，失败 ${result.failedCount} 张（场景 ${result.failedScenes.join('、')}）。\n\n可在预览页修改提示词后单独重新生成。`,
          [{ text: '去预览', onPress: () => router.push(`/preview/${id}`) }]
        );
      } else {
        router.push(`/preview/${id}`);
      }
    } catch (e) {
      Alert.alert('生成失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setLoading(false);
      setProgressMsg('');
    }
  }, [id, imageService, imageStyle, imageSize, router]);

  return (
    <View style={styles.container}>
      {loading && <LoadingOverlay message={progressMsg || '正在生成绘本...'} />}

      <ScrollView contentContainerStyle={styles.scroll}>
        {book && (
          <Text style={styles.info}>
            📖 {book.character} 的故事 · {book.scenes.length} 个场景
          </Text>
        )}

        <Card title="🎨 图片配置">
          <Text style={styles.hint}>
            提示词已加入儿童绘本安全约束。若某张图被绿网拦截，可在预览页单独修改提示词后重试。
          </Text>

          <OptionPicker
            label="图片生成服务"
            options={APP_CONFIG.image_services.map((s) => ({
              label: s.label,
              value: s.id as 'doubao' | 'tongyi',
            }))}
            value={imageService}
            onChange={handleServiceChange}
          />

          <OptionPicker
            label="图片风格"
            options={APP_CONFIG.image_styles.map((s) => ({
              label: s,
              value: s,
            }))}
            value={imageStyle}
            onChange={setImageStyle}
          />

          <View style={styles.pickerGroup}>
            <Text style={styles.pickerLabel}>图片尺寸</Text>
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
          </View>
        </Card>

        <Button
          title="🎨 生成绘本（翻译+插画）"
          onPress={handleGenerate}
          loading={loading}
        />
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
  hint: {
    fontSize: fontSize.sm,
    color: colors.textLight,
    marginBottom: spacing.md,
    lineHeight: 20,
  },
  pickerGroup: { marginBottom: spacing.lg },
  pickerLabel: {
    fontSize: fontSize.md,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.full,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
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
  sizeOptionActive: {
    borderColor: colors.primary,
    backgroundColor: '#FFF0E6',
  },
  sizeText: { fontSize: fontSize.sm, color: colors.text },
  sizeTextActive: { color: colors.primary, fontWeight: '600' },
});
