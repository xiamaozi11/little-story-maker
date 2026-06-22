# 小小故事家（リトル・ストーリー・メーカー）📚

> 3〜8歳向け AI 絵本・アニメ制作 — Android アプリ、Streamlit Web、オプションの Python API

[![Version](https://img.shields.io/badge/version-1.0.4-blue)](https://github.com/xiamaozi11/storycraft_children)
[![Python](https://img.shields.io/badge/python-3.11+-green)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

[English](README.md) | [简体中文](README.zh.md) | **日本語**

---

## 🌟 このプロジェクトについて

**小小故事家** は、子どもが **自分だけの** 絵本や短いアニメを作れる Android アプリです。**音声または文字** でアイデアを伝えると、AI が物語を書き、イラストを描き、PDF や動画として残せます。

実際の家族プロジェクトとして生まれました：パパが開発、ママが内容をチェック、兄がアニメを作り、妹が寝る前に絵本を読みます。

---

## ✨ 機能

| 機能 | 説明 |
|------|------|
| 📖 **絵本モード** | アイデア → AI 物語 → イラスト → アプリ内プレビュー → PDF 出力 |
| 🎬 **アニメモード** | 絵コンテ、キャラクター立ち絵、15〜60秒のアニメ動画 |
| 🎤 **音声入力** | ローカル音声認識 — タイピング不要 |
| 🌍 **バイリンガル** | 中国語と英語 |
| 🎨 **複数のアートスタイル** | 漫画、アニメ、中国風、水彩、カートゥーンなど |
| 📱 **スタンドアロン** | 通義千問 / 豆包 API に直接接続、データは端末内に保存 |
| 🖥️ **Web UI** | Streamlit 絵本ジェネレーター |
| 🔌 **REST API** | オプションの FastAPI バックエンド |

---

## 📁 プロジェクト構造

```
storycraft_children/
├── mobile/                 # Expo / React Native Android アプリ
├── src/
│   ├── app.py              # Streamlit Web
│   ├── api_server.py       # FastAPI REST API
│   └── storycraft/         # コアロジック
├── scripts/
└── docs/
```

---

## 🚀 クイックスタート：Android アプリ

### 前提条件

- Node.js 18+
- Android 開発環境（APK ビルド時）
- 通義千問 API キー（[Alibaba 百錬](https://bailian.console.aliyun.com/)）

### 実行

```bash
git clone https://github.com/xiamaozi11/storycraft_children.git
cd storycraft_children/mobile
npm install
npx expo start --android
```

### API キー設定

アプリの **設定** で入力：

| キー | 用途 | 必須 |
|------|------|------|
| 通義千問 API Key | 物語、翻訳、通義イラスト | ✅ |
| 豆包 ARK Key | 高速豆包イラスト | 任意 |
| Seedance API Key | アニメ動画生成 | アニメモード用 |

キーは端末内のみに保存されます。

### 制作フロー

**絵本：** ホーム → 編集 → イラスト生成 → プレビュー → PDF 出力

**アニメ：** アニメモード → 絵コンテ → 動画設定 → プレビュー・共有

### APK ビルド

```bash
cd mobile
npm run build:apk:local
```

音声入力には先に ASR モデルを取得：`npm run download:asr-models`

詳細：[mobile/README.md](mobile/README.md)

---

## 🖥️ Web アプリ（Streamlit）

```bash
cd storycraft_children
pip install -r requirements.txt
cp .env.example .env
streamlit run src/app.py
```

`http://localhost:8501` で開きます。

### 環境変数（`.env`）

```env
API_KEY=sk-your-api-key-here
API_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
TEXT_MODEL=qwen-plus
IMAGE_SERVICE=tongyi
ARK_API_KEY=your-doubao-key
IMAGE_SIZE=1104x1472
VOLC_SEEDANCE_API_KEY=...
```

---

## 🔌 API サーバー（任意）

```bash
scripts/start_api.bat      # Windows
scripts/start_api.sh       # Linux / macOS
```

デフォルト：`http://localhost:8000`

---

## 📂 出力と保存

| クライアント | 場所 |
|-------------|------|
| Web / API | `output/`（タイムスタンプ付きフォルダ） |
| モバイル | 端末内 `documentDirectory/books/{id}/` + AsyncStorage |

---

## 💡 ヒント

1. 物語のアイデアは具体的に
2. キャラクター名はシンプルに
3. シーン数は 3〜10 ページ程度がおすすめ
4. PDF 出力前にプレビュー
5. 保護者が AI 生成コンテンツを確認してから子どもに見せる

---

## 📄 ライセンス

MIT — [LICENSE](LICENSE) を参照。

---

## 📞 お問い合わせ

- 🐛 [Issue を提出](https://github.com/xiamaozi11/storycraft_children/issues)

---

## ⚠️ 免責事項

物語・画像・動画はすべて AI が生成します。子どもに読み聞かせる前に、保護者が内容の適切性を確認してください。API キーを公開リポジトリにコミットしないでください。

---

## 🙏 謝辞

本プロジェクトは **[StoryCraft](https://github.com/cn-vhql/StoryCraft)** をベースに拡張しています。[cn-vhql/StoryCraft](https://github.com/cn-vhql/StoryCraft) がオープンソースで公開してくれた子供向け絵本生成のコアに感謝します。それを土台に、モバイル向け音声入力・アニメモード・家族向け体験を備えた **小小故事家** を作りました。

また以下にも感謝します：

- [Streamlit](https://streamlit.io/) — Web フレームワーク
- [Expo](https://expo.dev/) / [React Native](https://reactnative.dev/) — モバイル
- [ReportLab](https://www.reportlab.com/) — PDF 生成
- [通義千問](https://tongyi.aliyun.com/) / [豆包](https://www.doubao.com/) — AI サービス

---

**子どもたちへの愛を込めて ❤️ — すべての子が物語とともに甘い夢を見られることを。**
