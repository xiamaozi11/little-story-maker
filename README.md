# Little Story Maker (小小故事家) 📚

> AI-powered picture book and anime creation for children ages 3–8 — Android app, Streamlit web, and optional Python API

[![Version](https://img.shields.io/badge/version-1.0.4-blue)](https://github.com/xiamaozi11/storycraft_children)
[![Python](https://img.shields.io/badge/python-3.11+-green)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

**English** | [简体中文](README.zh.md) | [日本語](README.ja.md)

---

## 🌟 About

**Little Story Maker** (*小小故事家*) helps kids turn imagination into **their own** picture books or short anime clips — using **voice or text** to describe an idea, then AI writes the story, draws illustrations, and exports a shareable PDF or video.

Born from a real family project: dad builds the tech, mom reviews child-friendly content, big brother creates anime, little sister reads bedtime stories.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📖 **Picture book mode** | Idea → AI story → illustrations → in-app preview → PDF export |
| 🎬 **Anime mode** | Storyboard script, character art, 15–60s anime video clips |
| 🎤 **Voice input** | Local speech recognition — no typing required |
| 🌍 **Bilingual** | Chinese + English for family reading |
| 🎨 **Art styles** | Manga, anime, Chinese traditional, watercolor, cartoon, and more |
| 📱 **Standalone mobile** | App calls Tongyi / Doubao APIs directly; data stays on device |
| 🖥️ **Web UI** | Streamlit picture book generator for desktop |
| 🔌 **REST API** | Optional FastAPI backend (`src/api_server.py`) |

---

## 📁 Project Structure

```
storycraft_children/
├── mobile/                 # Expo / React Native Android app (primary)
├── src/
│   ├── app.py              # Streamlit web app
│   ├── api_server.py       # FastAPI REST API
│   └── storycraft/         # Core: text, images, PDF, anime
├── scripts/                # Start scripts, APK build, demos
└── docs/
```

---

## 🚀 Quick Start: Android App

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

More details: [mobile/README.md](mobile/README.md)

---

## 🖥️ Web App (Streamlit)

```bash
cd storycraft_children
pip install -r requirements.txt
cp .env.example .env   # add your API_KEY
streamlit run src/app.py
```

Open `http://localhost:8501`.

### Environment (`.env`)

```env
API_KEY=sk-your-api-key-here
API_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
TEXT_MODEL=qwen-plus
IMAGE_SERVICE=tongyi
ARK_API_KEY=your-doubao-key
IMAGE_SIZE=1104x1472
VOLC_SEEDANCE_API_KEY=...   # optional, for anime video
```

---

## 🔌 API Server (Optional)

```bash
scripts/start_api.bat      # Windows
scripts/start_api.sh       # Linux / macOS
```

Default: `http://localhost:8000`

---

## 📂 Output & Storage

| Client | Location |
|--------|----------|
| Web / API | `output/` (timestamped folders) |
| Mobile | Device `documentDirectory/books/{id}/` + AsyncStorage metadata |

---

## 💡 Tips

1. Be specific with story ideas — details help AI stay on track
2. Use simple character names
3. Keep scenes moderate (3–10 pages for books)
4. Preview before exporting PDF
5. Parents should review AI-generated content before kids read/watch

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

This project extends **[StoryCraft](https://github.com/cn-vhql/StoryCraft)**. We are grateful to [cn-vhql/StoryCraft](https://github.com/cn-vhql/StoryCraft) for open-sourcing the core children's picture book generator — it enabled us to build **Little Story Maker** with mobile voice input, anime mode, and a family-first experience on top.

Also thanks to:

- [Streamlit](https://streamlit.io/) — Web framework
- [Expo](https://expo.dev/) / [React Native](https://reactnative.dev/) — Mobile
- [ReportLab](https://www.reportlab.com/) — PDF generation
- [Tongyi Qianwen](https://tongyi.aliyun.com/) / [Doubao](https://www.doubao.com/) — AI services

---

**Made with ❤️ for kids — may every child drift into sweet dreams with stories.**
