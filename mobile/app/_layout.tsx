import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { colors } from '../src/theme';

export default function RootLayout() {
  return (
    <>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.background },
          headerTintColor: colors.text,
          headerTitleStyle: { fontWeight: '700' },
          contentStyle: { backgroundColor: colors.background },
          headerShadowVisible: false,
        }}
      >
        <Stack.Screen name="index" options={{ title: '📚 小小故事家' }} />
        <Stack.Screen name="settings" options={{ title: '⚙️ API 设置' }} />
        <Stack.Screen name="history" options={{ title: '📚 我的绘本' }} />
        <Stack.Screen name="edit/[id]" options={{ title: '✏️ 编辑故事' }} />
        <Stack.Screen name="config/[id]" options={{ title: '🎨 图片配置' }} />
        <Stack.Screen name="preview/[id]" options={{ title: '📖 绘本预览' }} />
        <Stack.Screen name="export/[id]" options={{ title: '📄 导出 PDF' }} />
        <Stack.Screen name="anime/edit/[id]" options={{ title: '✏️ 动漫分镜' }} />
        <Stack.Screen name="anime/config/[id]" options={{ title: '🎬 动漫生成' }} />
        <Stack.Screen name="anime/preview/[id]" options={{ title: '🎥 动漫预览' }} />
      </Stack>
    </>
  );
}
