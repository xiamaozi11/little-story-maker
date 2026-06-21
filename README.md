# StoryCraft 📚

> AI-powered children's picture book generator for ages 3-5

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/cn-vhql/StoryCraft)
[![Python](https://img.shields.io/badge/python-3.11+-green)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red)](https://streamlit.io/)

**English** | [简体中文](README.zh.md) | [日本語](README.ja.md)

---

## 🌟 About

**This is a gift from Cloud Dad to his daughter, Cloud.**

Every child deserves their own unique story. StoryCraft harnesses the power of AI to weave imaginative worlds for children, making bedtime warm and special.

**May all children be surrounded by love and drift into sweet dreams accompanied by stories.**

---

## ✨ Features

- **AI Story Generation** - Enter a creative idea, AI crafts a complete story
- **Automatic Illustrations** - Beautiful images for every page
- **Bilingual Support** - Chinese and English for language learning
- **PDF Export** - Optimized for Kindle e-readers and tablets
- **8 Art Styles** - Manga, Anime, Chinese Traditional, Watercolor, and more
- **Customizable** - Edit stories, regenerate images, personalize content

**Perfect for**: Parents creating personalized books, educators making teaching materials, anyone crafting unique stories for children

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- **Python 3.11+** installed
- **API Key** from Tongyi Qianwen (Free tier available)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/cn-vhql/StoryCraft.git
cd StoryCraft

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env and add your API key

# 4. Run the application
streamlit run src/app.py
```

The application will open automatically in your browser at `http://localhost:8501`

---

## 📖 Detailed Setup Guide

### Step 1: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Install Python 3.11 or higher
3. **Important**: Check "Add Python to PATH" during installation

Verify installation:
```bash
python --version
```

### Step 2: Get API Keys

StoryCraft uses AI services to generate stories and images. You'll need API keys:

#### Option 1: Tongyi Qianwen (Recommended for Beginners)

1. Visit [Alibaba Cloud Bailian Platform](https://bailian.console.aliyun.com/)
2. Register/Login to your account
3. Enable "Tongyi Qianwen" service (Free tier for new users)
4. Create an API Key

#### Option 2: Doubao (Faster Image Generation)

1. Visit [Volcengine Console](https://console.volcengine.com/ark)
2. Create inference endpoint to get API Key
3. Add to `.env` file (see configuration below)

**💡 Tip**: Start with Tongyi Qianwen - simpler setup, beginner-friendly

### Step 3: Configure Environment

Edit `.env` file in the project root:

```env
# Tongyi Qianwen Configuration
API_KEY=sk-your-api-key-here
API_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
TEXT_MODEL=qwen-plus
IMAGE_SERVICE=tongyi

# Optional: Doubao Configuration
ARK_API_KEY=your-doubao-key-here
IMAGE_SERVICE=doubao

# Image Configuration
IMAGE_SIZE=1104x1472  # 3:4 portrait, suitable for picture books

# Application Settings
MAX_SCENES=30
MIN_SCENES=1
DEFAULT_SCENES=10
```

### Step 4: Launch Application

```bash
streamlit run src/app.py
```

Visit `http://localhost:8501` in your browser

---

## 🎨 Usage Tutorial

### Interface Overview

![StoryCraft Interface](assets/images/README/1769336295497.png)

**Left Sidebar - Configuration**:
- 📝 **Story Creation**: Input ideas, character name, story length
- 🎨 **Image Settings**: Select style and dimensions
- 🔄 **Regenerate**: Recreate unsatisfactory images

**Main Area - Operations**:
1. Generate story (Chinese)
2. Edit and confirm story
3. Generate illustrations (auto-translate + auto-generate images)
4. Preview and download PDF

### Creating Your First Picture Book

#### 1. Input Story Idea

```
Example: A little rabbit discovers a magical seed in the forest,
waters it every day, and it grows into a tree full of candies...
```

#### 2. Name Your Character

```
Examples: Little Rabbit, Little Bear, Doudou
```

#### 3. Select Story Length

```
Recommended: 3-10 scenes (each scene = one page)
```

#### 4. Click "Generate Story"

```
AI will automatically create a Chinese story
```

#### 5. Edit Story Content (Optional)

```
If not satisfied, modify any page's text
```

#### 6. Choose Image Style

| Style | Characteristics | Best For |
|-------|----------------|----------|
| **Manga** | Black & white lines, clean | Kindle e-readers |
| **Anime** | Colorful, vibrant | Color tablets |
| **Chinese** | Traditional ink painting | Cultural themes |
| **Watercolor** | Soft, artistic | Gentle stories |
| **Cartoon** | Cute, simple | Ages 3-5 |
| **Oil Painting** | Rich colors, 3D effect | Art appreciation |
| **Watercolor** | Light, airy | Warm stories |
| **Classical** | European oil painting | Fairy tales |

#### 7. Click "Generate Picture Book"

```
AI will automatically:
- Translate all scenes to English
- Generate illustrations for each page
```

#### 8. Preview and Download

```
Enter title and author name
Click "Generate and Download PDF"
```

![PDF Generation](assets/images/README/1769336380598.png)

---

## 📂 Output File Structure

Generated files are saved in `output/` directory with timestamp organization:

```
output/
└── 20260125_143000_LittleRabbit/
    ├── scene_1.png              # Page 1 illustration
    ├── scene_2.png              # Page 2 illustration
    ├── scene_3.png              # Page 3 illustration
    ├── story_draft.txt          # Story draft (text version)
    └── LittleRabbit_Story.pdf   # Final PDF picture book
```

---

## ⚙️ Advanced Configuration

### Reduce PDF File Size

```env
PDF_IMAGE_QUALITY=70           # Image compression (1-100, default 85)
PDF_MAX_IMAGE_DIMENSION=1024    # Max image size (default 1200)
```

### Adjust Font Size

```env
FONT_SIZE=20                   # Font size (default 24)
```

### Supported Image Sizes

**Tongyi Qianwen (wan2.6-t2i):**
- `1104x1472` (3:4 portrait, recommended)
- `1280x1280` (1:1 square)
- `960x1280` (3:4 portrait)
- `1472x1104` (4:3 landscape)
- `960x1696` (9:16 portrait tall)

**Doubao:**
- `1920x2560` (3:4 portrait, recommended)
- `2048x2730` (3:4 portrait, HD)
- `2048x2048` (1:1 square)
- `2560x1920` (4:3 landscape)
- `2048x1536` (4:3 landscape small)

---

## 🔧 Troubleshooting

### Error: `ModuleNotFoundError: No module named 'streamlit'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Error: `Invalid API Key`

**Solutions:**
- Check `.env` file for correct API_KEY
- Verify API key has required service enabled
- Check network connection

### Error: Image Generation Failed

**Solutions:**
- Confirm API key has image generation permissions
- Try reducing scene count
- Switch image generation service (Tongyi ⇄ Doubao)

### View Logs

```bash
# View recent logs
tail -f output/app.log
```

---

## 💡 Usage Tips

1. **Be Specific with Story Ideas**
   - ✅ "Little rabbit finds magical seed, waters it daily, grows into candy tree"
   - ❌ "Write a children's story"

2. **Keep Character Names Simple**
   - ✅ "Little Rabbit", "Doudou", "Mingming"
   - ❌ "Alexander Nicolaevich"

3. **Moderate Scene Count**
   - ✅ 3-10 scenes
   - ❌ 30 scenes (will take very long)

4. **Preview Before Download**
   Preview images before generating PDF

5. **Use Edit Feature**
   AI-generated stories can be freely modified to better suit your needs

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Thanks to the following open-source projects and services:

- [Streamlit](https://streamlit.io/) - Web framework
- [ReportLab](https://www.reportlab.com/) - PDF generation
- [Tongyi Qianwen](https://tongyi.aliyun.com/) - AI service
- [Doubao](https://www.doubao.com/) - AI service

---

## 📞 Contact

- 🐛 **Bug Reports**: [Submit Issue](https://github.com/cn-vhql/StoryCraft/issues)
- 💬 **Discussions**: [Share your creations](https://github.com/cn-vhql/StoryCraft/discussions)

---

## ⚠️ Disclaimer

Picture book content generated by this project is entirely AI-generated. Parents should review content for suitability before reading to children.

---

**Made with ❤️ for kids | Using AI to create beautiful stories for children**
