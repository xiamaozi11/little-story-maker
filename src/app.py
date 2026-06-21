import streamlit as st
from pathlib import Path
from storycraft.config import *
from storycraft.api.text_generator import TextGenerator
from storycraft.api.image_generator import ImageGenerator
from storycraft.core.story_builder import StoryBuilder
from storycraft.core.pdf_generator import PDFGenerator

# 页面配置
st.set_page_config(
    page_title="儿童绘本生成器",
    page_icon="📚",
    layout="wide"
)

# 初始化 session state
if 'scenes' not in st.session_state:
    st.session_state.scenes = []
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None
if 'session_dir' not in st.session_state:
    st.session_state.session_dir = ""
if 'original_params' not in st.session_state:
    st.session_state.original_params = {}
if 'character_description' not in st.session_state:
    st.session_state.character_description = ""
if 'story_generated' not in st.session_state:
    st.session_state.story_generated = False  # 新增：标记故事是否已生成
if 'story_confirmed' not in st.session_state:
    st.session_state.story_confirmed = False  # 新增：标记故事是否已确认

# 标题
st.title("📚 儿童绘本生成器")
st.markdown("---")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 绘本配置")

    # 第一阶段：故事创作（始终显示）
    st.subheader("📝 故事创作")

    # 故事点子输入（必填）
    idea = st.text_area(
        "故事创意/点子",
        value="",
        placeholder="例如：小兔子在森林里发现了一颗神奇的种子，它每天浇水，种子长成了一棵结满糖果的树...",
        height=150,
        help="输入你的故事创意，AI会根据这个点子创作完整绘本",
        max_chars=500
    )

    # 角色名字
    character = st.text_input(
        "主角名字",
        value="",
        help="给故事的主角起个名字",
        max_chars=20
    )

    # 故事长度
    num_scenes = st.slider(
        "故事长度（场景数）",
        min_value=MIN_SCENES,
        max_value=MAX_SCENES,
        value=DEFAULT_SCENES,
        help="场景越多，故事越长（最多30页）"
    )

    st.markdown("---")

    # 第一步：生成故事
    generate_story_btn = st.button("📝 生成故事", type="primary", use_container_width=True)

    # 第二阶段：图片配置（仅在故事生成后显示）
    if st.session_state.story_generated:
        st.subheader("🎨 图片配置")

        # 图片生成服务选择
        image_service = st.selectbox(
            "图片生成服务",
            options=["豆包", "通义千问"],
            index=0,
            help="豆包：支持组图生成，速度更快 | 通义千问：稳定可靠，wan2.6-t2i 模型质量高"
        )
        image_service_value = "doubao" if image_service == "豆包" else "tongyi"

        # 图片风格选择
        image_style = st.selectbox(
            "图片风格",
            options=list(IMAGE_STYLES.keys()),
            index=list(IMAGE_STYLES.keys()).index(DEFAULT_IMAGE_STYLE),
            help="选择插画风格，漫画风适合Kindle黑白屏"
        )

        # 图片尺寸选择（根据服务显示不同选项）
        if image_service_value == "tongyi":
            # 通义千问 wan2.6-t2i 兼容尺寸（1280×1280 到 1440×1440 之间）
            st.caption("💡 wan2.6-t2i 推荐尺寸：1280×1280 到 1440×1440 之间")
            image_size_options = {
                "1104x1472 (3:4 竖版，推荐)": "1104x1472",
                "1280x1280 (1:1 正方形)": "1280x1280",
                "960x1280 (3:4 竖版)": "960x1280",
                "1472x1104 (4:3 横版)": "1472x1104",
                "960x1696 (9:16 竖版长)": "960x1696"
            }
            size_help = "wan2.6-t2i 支持的尺寸范围：1280×1280 到 1440×1440 之间"
        else:
            # 豆包尺寸（要求至少 3,686,400 像素）
            st.caption("💡 豆包支持自定义尺寸，要求至少 3.7M 像素")
            image_size_options = {
                "1920x2560 (3:4 竖版，推荐)": "1920x2560",
                "2048x2730 (3:4 竖版，高清)": "2048x2730",
                "2048x2048 (1:1 正方形)": "2048x2048",
                "2560x1920 (4:3 横版)": "2560x1920",
                "2048x1536 (4:3 横版小)": "2048x1536"
            }
            size_help = "豆包要求至少 3.7M 像素，3:4 竖版适合绘本和Kindle阅读"

        image_size = st.selectbox(
            "图片尺寸",
            options=list(image_size_options.keys()),
            index=0,
            help=size_help
        )
        image_size_value = image_size_options[image_size]

        st.markdown("---")

        # 保存图片配置到session state
        st.session_state.original_params['image_service'] = image_service_value
        st.session_state.original_params['image_size'] = image_size_value
        st.session_state.image_style = image_style

        # 第三步：生成绘本
        has_images = st.session_state.scenes and 'image_path' in st.session_state.scenes[0]
        if not has_images:
            generate_picture_btn = st.button("🎨 生成绘本（翻译+图片）", type="primary", use_container_width=True)
        else:
            generate_picture_btn = None

        if st.session_state.story_generated:
            st.info(f"✅ 故事已生成，共 {len(st.session_state.scenes)} 个场景")
            if not has_images:
                st.caption('💡 在下方编辑和确认场景内容，确认后点击"生成绘本"')
            else:
                st.caption('✅ 图片已生成，可以在下方预览，确认后生成PDF')

    else:
        # 故事未生成时的提示
        st.info("👈 请先填写故事信息并生成故事")
        image_service_value = None
        image_size_value = None
        image_style = None
        generate_picture_btn = None

    # 重新生成场景图片（仅通义千问支持，且在图片生成后）
    if st.session_state.pdf_path and st.session_state.original_params.get('image_service') == 'tongyi':
        st.markdown("---")
        st.subheader("🔄 重新生成场景图片")

        # 场景选择
        scene_options = list(range(1, len(st.session_state.scenes) + 1))
        regenerate_scenes = st.multiselect(
            "选择要重新生成的场景",
            options=scene_options,
            help="选择需要重新生成图片的场景编号"
        )

        if regenerate_scenes:
            if st.button("🔄 重新生成选中的场景", type="secondary", use_container_width=True):
                try:
                    with st.spinner(f"正在重新生成 {len(regenerate_scenes)} 个场景的图片..."):
                        # 重新初始化图片生成器
                        img_gen = ImageGenerator(
                            API_KEY,
                            OUTPUT_DIR,
                            style=st.session_state.image_style,
                            service=st.session_state.original_params['image_service'],
                            image_size=st.session_state.original_params['image_size']
                        )

                        # 设置角色描述以保持风格一致
                        if st.session_state.character_description:
                            img_gen.character_description = st.session_state.character_description

                        # 重新生成选中的场景图片
                        for scene_num in regenerate_scenes:
                            idx = scene_num - 1  # 转换为索引
                            scene = st.session_state.scenes[idx]
                            prompt = scene.get('image_prompt', '')

                            # 设置正确的输出目录
                            img_gen.output_dir = Path(OUTPUT_DIR) / st.session_state.session_dir

                            # 重新生成图片
                            new_image_path = img_gen.generate(
                                prompt,
                                f"scene_{scene_num}"
                            )

                            # 更新场景的图片路径
                            st.session_state.scenes[idx]['image_path'] = new_image_path

                        st.success(f"✅ 成功重新生成 {len(regenerate_scenes)} 个场景的图片！")
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ 重新生成失败: {str(e)}")
                    st.exception(e)

# 主区域 - 第一步：生成故事
if generate_story_btn:
    if not idea:
        st.error("❌ 请输入故事创意/点子")
    elif not character:
        st.error("❌ 请输入主角名字")
    elif not API_KEY:
        st.error("❌ 请先配置 API_KEY（在 .env 文件中）")
    else:
        # 显示进度
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # 初始化文本生成器
            status_text.text("正在初始化...")
            progress_bar.progress(10)

            text_gen = TextGenerator(API_KEY, API_ENDPOINT, TEXT_MODEL)

            # 仅生成故事文本（仅中文，不生成图片）
            status_text.text(f"📝 正在根据你的创意生成故事（{num_scenes}个场景，仅中文）...")
            progress_bar.progress(30)

            story_data = text_gen.generate_story(idea, character, num_scenes, chinese_only=True)
            scenes = story_data["scenes"]
            session_dir = f"{character}_{num_scenes}scenes"

            # 创建临时会话目录
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_character = "".join(c for c in character if c.isalnum() or c in "_-")
            session_dir = f"{timestamp}_{safe_character}"
            full_session_dir = Path(OUTPUT_DIR) / session_dir
            full_session_dir.mkdir(parents=True, exist_ok=True)

            # 保存会话目录
            st.session_state.session_dir = session_dir

            # 保存到 session state
            st.session_state.scenes = scenes
            st.session_state.character_description = story_data.get("character_description", "")

            # 保存原始生成参数（包含图片配置）
            st.session_state.original_params = {
                'idea': idea,
                'character': character,
                'num_scenes': num_scenes,
                'image_service': st.session_state.original_params.get('image_service', 'doubao'),
                'image_size': st.session_state.original_params.get('image_size', '1024x1024')
            }

            status_text.text("✅ 故事生成完成！")
            progress_bar.progress(100)

            st.success(f"故事生成成功！共{len(scenes)}个场景")
            st.session_state.story_generated = True
            st.session_state.story_confirmed = False  # 重置确认状态

            # 保存故事到文件（不含图片路径和提示词）
            story_file = full_session_dir / "story_draft.txt"
            with open(story_file, 'w', encoding='utf-8') as f:
                f.write(f"""============================================================
Kindle 儿童绘本故事记录
============================================================

📝 故事信息
{'─'*60}
故事创意：{idea}
主角名字：{character}
场景数量：{len(scenes)}
生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

👤 角色描述
{'─'*60}
{st.session_state.character_description}

📖 故事场景
{'─'*60}
""")
                for idx, scene in enumerate(scenes, 1):
                    f.write(f"""
【场景 {idx}】
{scene['text']}
{'─'*40}
""")
                f.write("""
============================================================
文件结束
============================================================
""")

            st.info(f"故事已保存到: {story_file}")
            st.info("💡 下一步：在下方编辑和确认场景内容，然后选择图片配置并生成绘本")
            st.rerun()

        except Exception as e:
            st.error(f"❌ 故事生成失败: {str(e)}")
            st.exception(e)

# 主区域 - 第二步：生成绘本（翻译+图片）
if generate_picture_btn:
    if not st.session_state.scenes:
        st.error("❌ 请先生成故事")
    else:
        # 显示进度
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # 步骤1：批量翻译故事
            text_gen = TextGenerator(API_KEY, API_ENDPOINT, TEXT_MODEL)

            status_text.text(f"🌐 正在翻译故事（{len(st.session_state.scenes)}个场景）...")
            progress_bar.progress(10)

            # 检查是否需要翻译
            need_translate = any('text_en' not in scene or not scene.get('text_en') for scene in st.session_state.scenes)

            if need_translate:
                # 使用批量翻译
                translations = text_gen.translate_scenes_batch(st.session_state.scenes)
                # 更新所有场景的英文翻译
                for idx, scene in enumerate(st.session_state.scenes):
                    scene['text_en'] = translations[idx]

            progress_bar.progress(30)
            status_text.text("✅ 翻译完成！")

            # 步骤2：批量生成图片提示词
            status_text.text(f"🎨 正在生成图片提示词（{len(st.session_state.scenes)}个场景）...")
            progress_bar.progress(40)

            # 检查是否需要生成图片提示词
            need_prompts = any('image_prompt' not in scene or not scene.get('image_prompt') for scene in st.session_state.scenes)

            if need_prompts:
                # 使用批量生成图片提示词
                image_prompts = text_gen.generate_image_prompts_batch(
                    st.session_state.scenes,
                    st.session_state.character_description
                )
                # 更新所有场景的图片提示词
                for idx, scene in enumerate(st.session_state.scenes):
                    scene['image_prompt'] = image_prompts[idx]

            progress_bar.progress(50)
            status_text.text("✅ 图片提示词生成完成！")

            # 步骤4：初始化图片生成器
            status_text.text("正在初始化图片生成器...")
            progress_bar.progress(60)

            img_gen = ImageGenerator(
                API_KEY,
                OUTPUT_DIR,
                style=st.session_state.image_style,
                service=st.session_state.original_params['image_service'],
                image_size=st.session_state.original_params['image_size']
            )

            # 设置角色描述
            if st.session_state.character_description:
                img_gen.character_description = st.session_state.character_description

            # 设置输出目录
            session_dir_path = Path(OUTPUT_DIR) / st.session_state.session_dir
            session_dir_path.mkdir(parents=True, exist_ok=True)
            img_gen.output_dir = session_dir_path

            # 步骤5：批量生成图片
            status_text.text(f"🎨 正在生成插画（{len(st.session_state.scenes)}个场景）...")
            progress_bar.progress(70)

            prompts = [scene.get('image_prompt', '') for scene in st.session_state.scenes]
            image_paths = img_gen.generate_batch(prompts, st.session_state.character_description)

            # 更新场景的图片路径
            for idx, (scene, img_path) in enumerate(zip(st.session_state.scenes, image_paths)):
                scene['image_path'] = img_path

            progress_bar.progress(100)

            status_text.text("✅ 插画生成完成！")
            st.success(f"🎉 翻译和插画生成完成！共{len(st.session_state.scenes)}个场景")
            st.info("💡 请在下方预览效果，确认满意后生成PDF")

        except Exception as e:
            st.error(f"❌ 生成失败: {str(e)}")
            st.exception(e)

# 显示生成的绘本
if st.session_state.scenes:
    st.markdown("---")

    # 如果故事已生成但图片未生成，显示编辑界面
    if st.session_state.story_generated and 'image_path' not in st.session_state.scenes[0]:
        st.header("✏️ 编辑和确认故事内容")

        st.info("💡 提示：请确认每个场景的中文故事内容，确认后在左侧选择图片配置并点击\"生成绘本\"")

        # 编辑每个场景
        for idx, scene in enumerate(st.session_state.scenes):
            with st.expander(f"📖 场景 {idx + 1}", expanded=idx == 0):
                st.markdown("#### 📝 中文故事")
                text_cn = st.text_area(
                    f"text_cn_{idx}",
                    value=scene['text'],
                    height=100,
                    key=f"text_cn_edit_{idx}",
                    label_visibility="collapsed"
                )

                # 保存修改按钮
                if st.button(f"💾 保存场景 {idx+1} 的修改", key=f"save_{idx}"):
                    st.session_state.scenes[idx]['text'] = text_cn
                    st.session_state.scenes[idx].pop('text_en', None)
                    st.success(f"✅ 场景 {idx+1} 已保存")

        st.markdown("---")

    # 显示预览（如果有图片）
    has_images = st.session_state.scenes and 'image_path' in st.session_state.scenes[0]

    if has_images:
        st.header("📖 绘本预览")

        # 显示每个场景
        for idx, scene in enumerate(st.session_state.scenes):
            if 'image_path' in scene and scene['image_path']:
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.image(scene['image_path'], use_container_width=True)

                with col2:
                    st.markdown(f"### 场景 {idx + 1}")
                    st.write(scene['text'])

                st.markdown("---")

        st.markdown("---")

        # PDF生成区域（仅在有图片时显示）
        st.header("📄 导出 PDF")

        col1, col2 = st.columns([2, 1])

        with col1:
            title = st.text_input("绘本标题", value=f"{st.session_state.original_params.get('character', '主角')}的故事")

        with col2:
            author = st.text_input("作者", value="云朵爸爸")

        generate_pdf_btn = st.button("📄 生成并下载 PDF", type="primary", use_container_width=True)

        if generate_pdf_btn:
            with st.spinner("正在生成 PDF..."):
                try:
                    # 使用会话目录
                    session_dir = st.session_state.get("session_dir", "")
                    output_path = Path(OUTPUT_DIR) / session_dir if session_dir else Path(OUTPUT_DIR)

                    pdf_gen = PDFGenerator(str(output_path))
                    pdf_path = pdf_gen.generate(
                        st.session_state.scenes,
                        title,
                        author
                    )

                    st.session_state.pdf_path = pdf_path

                    # 显示文件大小
                    file_size = Path(pdf_path).stat().st_size / (1024 * 1024)
                    st.success(f"✅ PDF 生成成功！")
                    st.info(f"📄 文件：{pdf_path}\n📊 大小：{file_size:.2f} MB")

                    # 提供下载
                    with open(pdf_path, 'rb') as f:
                        st.download_button(
                            label="⬇️ 点击下载 PDF",
                            data=f,
                            file_name=Path(pdf_path).name,
                            mime="application/pdf",
                            type="primary"
                        )

                except Exception as e:
                    st.error(f"PDF 生成失败: {str(e)}")
                    st.exception(e)

# 使用说明
with st.expander("💡 使用说明"):
    st.markdown("""
    ### 三步创建绘本：

    1. **📝 生成故事**
       - 在左侧输入故事创意和主角名字
       - 选择故事长度（场景数）
       - 点击"生成故事"，AI 会创作中文故事
       - 可以编辑每页的故事文本内容

    2. **🎨 生成插画**
       - 在左侧选择图片服务（豆包/通义千问）
       - 选择图片风格和尺寸
       - 点击"生成绘本"，AI 会自动：
         * 批量翻译所有场景（1次API调用）
         * 批量生成图片提示词（1次API调用，用户无感知）
         * 生成所有场景的插画
       - 预览效果，确认满意

    3. **📄 生成 PDF**
       - 输入绘本标题和作者
       - 点击"生成并下载 PDF"
       - 下载 PDF 文件

    ### 图片风格说明：

    - **漫画风**: 黑白线条，适合Kindle电子墨水屏
    - **动漫**: 彩色鲜艳，日本动画风格
    - **中国风**: 传统中国画风格，优雅古典
    - **水墨画**: 淡雅水彩，艺术感强
    - **古典**: 欧洲古典油画风格，博物馆品质
    - **油画**: 浓厚色彩，立体感强
    - **水彩画**: 轻盈透气，柔和清新
    - **卡通**: 可爱简单，适合低幼儿童
    """)

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    Made with ❤️ for kids | 使用 AI 为孩子创造美好故事
    </div>
    """,
    unsafe_allow_html=True
)
