# Little Story Maker (小小故事家) 📚

> Android AI picture book and anime creator for children ages 3–8

[![Version](https://img.shields.io/badge/version-1.0.4-blue)](https://github.com/xiamaozi11/storycraft_children)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

**English** | [简体中文](README.zh.md)

---

## 🌟 About

**Little Story Maker** (*小小故事家*) is an Android app that helps kids turn imagination into **their own** picture books or short anime clips — using **voice or text** to describe an idea, then AI writes the story, draws illustrations, and exports a shareable PDF or video.

Born from a real family project: dad builds the tech, mom reviews child-friendly content, big brother creates anime, little sister reads bedtime stories.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📖 **Picture book mode** | Idea → AI story → illustrations → in-app preview → PDF export |
| 🎬 **Anime mode** | Storyboard script, character art, 15–60s anime video clips |
| 🎤 **Voice input** | MNN on-device speech recognition — no typing required |
| 🌍 **Bilingual** | Chinese + English for family reading |
| 🎨 **Art styles** | Manga, anime, Chinese traditional, watercolor, cartoon, and more |
| 📱 **Standalone mobile** | App calls Tongyi / Doubao APIs directly; data stays on device |

---

## 📁 Project Structure

```
storycraft_children/
└── mobile/                 # Expo / React Native Android app
    ├── app/                # Screens: create, edit, preview, export, anime flow
    └── src/
        ├── services/       # AI API, PDF, ASR, anime video
        └── storage/        # Local files and history
```

More details: [mobile/README.md](mobile/README.md)

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Android toolchain (for APK builds — see `mobile/scripts/`)
- Tongyi Qianwen API key ([Alibaba Bailian](https://bailian.console.aliyun.com/))

### Run

```bash
git clone https://github.com/xiamaozi11/storycraft_children.git
cd storycraft_children/mobile
npm install
npx expo start --android
```

### Configure API keys

Open **Settings** in the app:

| Key | Purpose | Required |
|-----|---------|----------|
| Tongyi API Key | Story, translation, Tongyi images | ✅ |
| Doubao ARK Key | Faster Doubao images | Optional |
| Seedance API Key | Anime video generation | For anime mode |

Keys are stored locally only — never sent to our servers.

### Workflow

**Book:** Home → edit story → generate art → preview → export PDF

**Anime:** Switch to anime mode → storyboard → character & video config → preview & share

### Build APK

```bash
cd mobile
npm run build:apk:local
```

For voice input, download ASR models first: `npm run download:asr-models`

---

## 📂 Local Storage

| Data | Location |
|------|----------|
| Book metadata | AsyncStorage |
| Images & PDF | Device `documentDirectory/books/{id}/` |

---

## 💡 Tips

1. Be specific with story ideas — details help AI stay on track
2. Use simple character names
3. Keep scenes moderate (3–10 pages for books)
4. Preview before exporting PDF
5. Parents should review AI-generated content before kids read/watch

---

## 🛠️ FAQ

**Q: Does the API cost money?**  
A: Tongyi Qianwen and Doubao offer free tiers for new users — enough for occasional family use.

**Q: Does it need internet?**  
A: Story and image generation requires network access; speech recognition runs on-device on Android (MNN).

**Q: Image generation failed?**  
A: Check your API key, network, or try switching between Tongyi and Doubao image services.

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 📞 Contact

- 🐛 [Report issues](https://github.com/xiamaozi11/storycraft_children/issues)

---

## ⚠️ Disclaimer

All story, image, and video content is AI-generated. Parents should review suitability before sharing with children. Never commit API keys to public repositories.

---

## 🙏 Acknowledgments

Thanks to the open-source project **[StoryCraft](https://github.com/cn-vhql/StoryCraft)** for sharing and contributing — it enabled us to build **Little Story Maker** for mobile, with voice input, anime mode, and a family co-creation experience.

Also thanks to:

- [MNN](https://github.com/alibaba/MNN) — on-device inference (local ASR)
- [Tongyi Qianwen](https://tongyi.aliyun.com/) / [Doubao](https://www.doubao.com/) — AI services

---

**Made with ❤️ for kids — may every child drift into sweet dreams with stories.**
