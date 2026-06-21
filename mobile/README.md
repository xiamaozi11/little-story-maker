# StoryCraft Android 移动端

纯手机端运行的儿童绘本生成器，**无需自建后端**。App 直接调用通义千问/豆包 AI API，绘本数据保存在手机本地。

## 架构

```
mobile/
├── app/                    # 页面
│   ├── index.tsx           # 创作首页
│   ├── settings.tsx        # API Key 设置
│   ├── history.tsx         # 本地历史记录
│   ├── edit/[id].tsx       # 编辑故事
│   ├── config/[id].tsx     # 图片配置
│   ├── preview/[id].tsx    # 绘本预览
│   └── export/[id].tsx     # 导出 PDF
└── src/
    ├── services/           # 业务逻辑（直连 AI API）
    ├── storage/            # 本地文件 + AsyncStorage
    └── config/             # 常量配置
```

## 快速开始

### 1. 安装依赖

```bash
cd mobile
npm install
```

### 2. 启动 App

```bash
npx expo start --android
```

### 3. 配置 API Key

首次使用请进入 **设置** 页填写：

| 配置项 | 用途 | 是否必需 |
|--------|------|----------|
| 通义千问 API Key | 故事生成、翻译、通义插画 | ✅ 必需 |
| 豆包 ARK API Key | 豆包插画（更快） | 可选 |

API Key 仅保存在本机 AsyncStorage，不会上传。

### 4. 创作绘本

1. 首页输入故事创意 → 生成故事
2. 编辑各场景文字
3. 选择图片风格和尺寸 → 生成插画
4. 预览翻页 → 导出 PDF → 分享

## 本地存储

| 数据 | 存储位置 |
|------|----------|
| 绘本元数据 | AsyncStorage |
| 插画图片 | `documentDirectory/books/{id}/` |
| PDF 文件 | `documentDirectory/books/{id}/` |

## 与 Python 后端的关系

- **移动端**：独立运行，不依赖 `api_server.py`
- **Python 后端**：仍可用于 Streamlit Web 版 (`streamlit run src/app.py`)，与 App 互不影响

## 构建 APK

```bash
npx expo prebuild --platform android
cd android && ./gradlew assembleRelease
```

或使用 EAS Build：`eas build --platform android`
