import React, { useCallback, useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';
import {
  AppSettings,
  loadSettings,
  saveSettings,
} from '../src/services/settings';
import { Button } from '../src/components/Button';
import { Card } from '../src/components/Card';
import { Input } from '../src/components/Input';
import { colors, fontSize, spacing } from '../src/theme';

export default function SettingsScreen() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings().then(setSettings);
  }, []);

  const update = (patch: Partial<AppSettings>) => {
    setSettings((prev) => (prev ? { ...prev, ...patch } : prev));
  };

  const handleSave = useCallback(async () => {
    if (!settings) return;
    setSaving(true);
    try {
      await saveSettings(settings);
      Alert.alert('已保存', 'API 配置已保存到本机');
    } catch (e) {
      Alert.alert('保存失败', e instanceof Error ? e.message : '未知错误');
    } finally {
      setSaving(false);
    }
  }, [settings]);

  if (!settings) {
    return (
      <View style={styles.center}>
        <Text>加载中...</Text>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.scroll}>
      <Text style={styles.hint}>
        已预填默认 Key，可直接使用；修改后点保存，将覆盖本机配置
      </Text>

      <Card title="☁️ 阿里云百炼（故事 + 插画）">
        <Input
          label="API Key"
          value={settings.apiKey}
          onChangeText={(v) => update({ apiKey: v })}
          placeholder="sk-..."
          secureTextEntry
        />
        <Input
          label="API 地址"
          value={settings.apiEndpoint}
          onChangeText={(v) => update({ apiEndpoint: v })}
        />
        <Input
          label="文本模型（绘本故事）"
          value={settings.textModel}
          onChangeText={(v) => update({ textModel: v })}
          placeholder="qwen-plus"
        />
        <Input
          label="生图模型（万象）"
          value={settings.imageModel}
          onChangeText={(v) => update({ imageModel: v })}
          placeholder="wan2.6-t2i"
        />
      </Card>

      <Card title="🎨 豆包（可选，备用出图）">
        <Input
          label="ARK API Key"
          value={settings.arkApiKey}
          onChangeText={(v) => update({ arkApiKey: v })}
          placeholder="ark-..."
          secureTextEntry
        />
        <Input
          label="ARK 地址"
          value={settings.arkBaseUrl}
          onChangeText={(v) => update({ arkBaseUrl: v })}
        />
        <Input
          label="豆包图片模型"
          value={settings.doubaoModel}
          onChangeText={(v) => update({ doubaoModel: v })}
        />
      </Card>

      <Card title="🎥 Seedance 2.0（动漫视频）">
        <Input
          label="Seedance API Key"
          value={settings.seedanceApiKey}
          onChangeText={(v) => update({ seedanceApiKey: v })}
          placeholder="Zeelin 网关 sk-...（非百炼 Key）"
          secureTextEntry
        />
        <Input
          label="提交地址"
          value={settings.seedanceUrl}
          onChangeText={(v) => update({ seedanceUrl: v })}
        />
        <Input
          label="查询结果地址"
          value={settings.seedanceResultUrl}
          onChangeText={(v) => update({ seedanceResultUrl: v })}
        />
      </Card>

      <Text style={styles.note}>
        💡 百炼 Key 用于故事与插画（qwen-plus + wan2.6-t2i）。动漫视频需单独配置
        Seedance 2.0 的 Zeelin 网关 Key，与百炼 Key 不同，不能混用。
      </Text>

      <Button title="💾 保存设置" onPress={handleSave} loading={saving} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  hint: {
    fontSize: fontSize.sm,
    color: colors.textLight,
    marginBottom: spacing.md,
    lineHeight: 20,
  },
  note: {
    fontSize: fontSize.sm,
    color: colors.textLight,
    marginBottom: spacing.lg,
    lineHeight: 22,
  },
});
