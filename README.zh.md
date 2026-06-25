# Little Story Maker 📚

面向 3–8 岁儿童的 **Android AI 绘本与动漫创作 App**。孩子用 **语音或文字** 说出故事想法，AI 帮他们把想象变成专属绘本 PDF，或分镜动漫短视频。

![Version](https://img.shields.io/badge/version-1.0.4-blue)
![License](https://img.shields.io/badge/license-MIT-orange)

**[English](README.md)** | **简体中文**

---

## ❤️ 关于本项目

**Little Story Maker** 是一个真实家庭共创的项目：爸爸负责开发与 AI 实现，妈妈把关内容适龄性，哥哥右右抢先创作动漫，妹妹绵绵睡前翻绘本阅读。

每个孩子都值得拥有 **属于自己的故事**——不是看别人的绘本，而是创造自己喜欢的冒险、动物朋友和魔法世界。

---

## 🎯 能做什么

| 能力 | 说明 |
|------|------|
| 📖 **绘本模式** | 输入创意 → AI 写故事 → 生成插画 → 手机翻页预览 → 导出 PDF |
| 🎬 **动漫模式** | 生成分镜剧本、角色立绘，并合成 15–60 秒动漫短视频 |
| 🎤 **语音输入** | MNN 本地语音识别，不会打字也能讲故事 |
| 🌍 **中英双语** | 故事自动翻译，方便亲子共读与启蒙 |
| 🎨 **多种画风** | 漫画、动漫、中国风、水彩、卡通等 |
| 📱 **纯手机运行** | App 直连通义千问 / 豆包 API，绘本数据保存在本机 |

---

## 📁 项目结构

```
little-story-maker/
└── mobile/                 # Expo / React Native Android App
    ├── app/                # 页面：创作、编辑、预览、导出、动漫流程
    └── src/
        ├── services/       # 直连 AI API、PDF、语音 ASR、动漫视频
        └── storage/        # 本地文件与历史记录
```

更多细节见 [mobile/README.md](mobile/README.md)。

---

## 🚀 快速开始

### 1. 环境要求

- Node.js 18+
- Android 开发环境（构建 APK 时需要，见 `mobile/scripts/`）
- 通义千问 API Key（[阿里云百炼](https://bailian.console.aliyun.com/)）

### 2. 安装与运行

```bash
git clone https://github.com/xiamaozi11/little-story-maker.git
cd little-story-maker/mobile
npm install
npx expo start --android
```

### 3. 配置 API Key

首次打开 App，进入 **设置** 填写：

| 配置项 | 用途 | 必需 |
|--------|------|------|
| 通义千问 API Key | 故事生成、翻译、通义插画 | ✅ |
| 豆包 ARK API Key | 豆包插画（更快） | 可选 |
| Seedance API Key | 动漫视频生成 | 动漫模式需要 |

密钥仅保存在本机，不会上传到我们的服务器。

### 4. 创作流程

**绘本：** 首页输入创意 → 编辑故事 → 选择画风生成插画 → 预览 → 导出 PDF 分享

**动漫：** 切换「动漫模式」→ 生成分镜 → 配置角色与视频 → 本地预览播放

### 5. 构建 APK

```bash
cd mobile
npm run build:apk:local
# 或：npx expo prebuild --platform android && cd android && ./gradlew assembleRelease
```

语音功能需先下载 ASR 模型：`npm run download:asr-models`

---

## 📂 本地存储

| 数据 | 位置 |
|------|------|
| 绘本元数据 | AsyncStorage |
| 插画与 PDF | 本机 `documentDirectory/books/{id}/` |

---

## 🎨 图片风格

| 风格 | 特点 | 推荐场景 |
|------|------|----------|
| 漫画风 | 黑白线条，清晰简洁 | 电子阅读 |
| 动漫 | 彩色鲜艳 | 手机、平板 |
| 中国风 | 传统国画 | 国学主题 |
| 卡通 | 可爱简单 | 3–5 岁 |
| 水彩 / 油画 / 古典 | 艺术感强 | 温馨或经典童话 |

---

## 💡 使用技巧

1. **创意要具体**：「小兔子每天浇水，种子长成糖果树」比「写个儿童故事」效果好得多
2. **主角名字简单**：朵朵、右右、小兔子——方便 AI 保持一致
3. **场景数量适中**：绘本建议 3–10 页，动漫按段数控制时长
4. **先预览再导出**：插画满意后再生成 PDF，节省时间
5. **家长审阅**：AI 内容生成后请家长确认是否适合孩子阅读

---

## 🛠️ 常见问题

**Q: API 要花钱吗？**  
A: 通义千问、豆包新用户有免费额度，家庭偶尔创作一般够用。

**Q: 需要联网吗？**  
A: 故事与插画生成需联网调用 AI；语音识别在 Android 上可本地运行（MNN）。

**Q: 图片生成失败？**  
A: 检查 API Key、网络，或切换通义 / 豆包插画服务。

---

## 📄 开源协议

本项目采用 MIT 许可证 — 详见 [LICENSE](LICENSE)。

---

## 📞 反馈与交流

- 🐛 [提交 Issue](https://github.com/xiamaozi11/little-story-maker/issues)
- 💬 欢迎在 Issues 中分享你用 Little Story Maker 创作的作品

---

## ⚠️ 说明

本项目生成的故事、插画与视频均由 AI 生成，使用前请家长审核内容是否适合儿童阅读。API 密钥请自行保管，切勿提交到公开仓库。

---

## 🙏 致谢

感谢开源项目 **[StoryCraft](https://github.com/cn-vhql/StoryCraft)** 的分享与贡献，让我们得以在此基础上打造 **Little Story Maker**，加入语音输入、动漫模式与家庭共创体验。

同时也感谢：

- [MNN](https://github.com/alibaba/MNN) — 本地推理框架（语音 ASR 等）
- [通义千问](https://tongyi.aliyun.com/) / [豆包](https://www.doubao.com/) — AI 服务

---

**愿所有的孩子都被爱意包围，在故事的陪伴下甜甜入睡。**
