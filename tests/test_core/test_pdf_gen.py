#!/usr/bin/env python3
"""
PDF 生成测试脚本
用于验证页码、英文翻译和空白页问题的修复
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from storycraft.core.pdf_generator import PDFGenerator

def test_pdf_generation():
    """测试 PDF 生成"""

    # 测试输出目录
    output_dir = Path("/vol1/app/StoryCraft/output/20260125_205358_熊妈妈和小熊宝宝")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 构造测试场景数据（包含英文翻译）
    test_scenes = []

    # 场景数据（从 story_draft.txt 提取）
    scenes_data = [
        {
            "text": "太阳打着哈欠，微笑着和大家说了再见，就慢慢下山去了。",
            "text_en": "The sun yawned, smiled and said goodbye to everyone, and slowly went down the mountain.",
            "image_path": str(output_dir / "scene_1.png")
        },
        {
            "text": "天渐渐变暗了，树林里亮起一点点、一点点的小光点——是萤火虫在快乐地飞来飞去！",
            "text_en": "It gradually got darker, and little spots of light lit up in the forest - fireflies were flying happily!",
            "image_path": str(output_dir / "scene_2.png")
        },
        {
            "text": "'该回家睡觉了，我最特别的小熊。'熊妈妈轻声呼唤着。",
            "text_en": "'Time to go home to sleep, my very special little bear.' Mama Bear called softly.",
            "image_path": str(output_dir / "scene_3.png")
        },
        {
            "text": "'我是只很特别的小熊吗？'小熊一边扑向妈妈的怀抱，一边问。",
            "text_en": "'Am I a very special little bear?' Little Bear asked as he jumped into his mother's arms.",
            "image_path": str(output_dir / "scene_4.png")
        },
        {
            "text": "'是呀，你非常特别。'熊妈妈笑着点点头，轻轻牵起小熊的手。",
            "text_en": "'Yes, you are very special.' Mama Bear smiled and nodded, gently taking Little Bear's hand.",
            "image_path": str(output_dir / "scene_5.png")
        },
        {
            "text": "他们手牵手，穿过随风摇摆的树林，树叶沙沙响，像在唱摇篮曲。",
            "text_en": "They walked hand in hand through the swaying forest, leaves rustling like singing a lullaby.",
            "image_path": str(output_dir / "scene_6.png")
        },
        {
            "text": "路过狐狸家时，看见小狐狸正躺在大泡泡里，咯咯笑着洗泡泡澡。",
            "text_en": "When passing the fox's house, they saw Little Fox lying in a big bubble, giggling while taking a bubble bath.",
            "image_path": str(output_dir / "scene_7.png")
        },
        {
            "text": "路过兔子家时，看见小兔子抱着胡萝卜枕头，正打最后一个哈欠。",
            "text_en": "When passing the rabbit's house, they saw Little Rabbit hugging a carrot pillow, yawning for the last time.",
            "image_path": str(output_dir / "scene_8.png")
        },
        {
            "text": "路过猫头鹰家时，看见猫头鹰爸爸用翅膀轻轻盖好熟睡的小猫头鹰。",
            "text_en": "When passing the owl's house, they saw Papa Owl gently covering the sleeping baby owl with his wings.",
            "image_path": str(output_dir / "scene_9.png")
        },
        {
            "text": "回到温暖的小熊家，熊妈妈把小熊抱上床，盖好软软的星星毯子：'晚安，我最特别的小熊。'",
            "text_en": "Back in the warm bear home, Mama Bear tucked Little Bear into bed and covered him with the soft star blanket: 'Goodnight, my very special little bear.'",
            "image_path": str(output_dir / "scene_10.png")
        }
    ]

    # 验证所有图片文件存在
    print("=" * 60)
    print("验证测试数据")
    print("=" * 60)
    for i, scene in enumerate(scenes_data, 1):
        img_path = Path(scene["image_path"])
        if img_path.exists():
            print(f"✅ 场景 {i}: 图片存在 - {img_path.name}")
            print(f"   中文: {scene['text'][:30]}...")
            print(f"   英文: {scene['text_en'][:40]}...")
            test_scenes.append(scene)
        else:
            print(f"❌ 场景 {i}: 图片不存在 - {scene['image_path']}")

    print()
    print("=" * 60)
    print(f"共 {len(test_scenes)} 个场景准备生成 PDF")
    print("=" * 60)
    print()

    # 初始化 PDF 生成器
    print("初始化 PDF 生成器...")
    pdf_gen = PDFGenerator(str(output_dir))

    # 生成 PDF
    print("开始生成 PDF（包含页码和英文翻译）...")
    print()

    try:
        pdf_path = pdf_gen.generate(
            test_scenes,
            title="熊妈妈和小熊宝宝的故事",
            author="云朵爸爸"
        )

        print()
        print("=" * 60)
        print("✅ PDF 生成成功！")
        print("=" * 60)
        print(f"文件路径: {pdf_path}")

        # 检查 PDF 信息
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        print(f"总页数: {len(reader.pages)}")
        print()

        # 检查每页内容
        print("PDF 页面内容检查:")
        print("-" * 60)
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            print(f"第 {i} 页: {len(text)} 字符")

            # 检查是否包含英文
            has_english = any(ord(c) < 128 and c.isalpha() for c in text)
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)

            if has_chinese:
                print("  ✅ 包含中文")
            if has_english:
                print("  ✅ 包含英文")

            # 检查是否为空白页
            if len(text.strip()) < 20:
                print("  ⚠️ 可能是空白页")

            # 检查页码
            if f"- {i} -" in text or f"第{i}" in text:
                print(f"  ✅ 包含页码")

            print()

        print("=" * 60)
        print("测试完成！请检查生成的 PDF:")
        print(f"📄 {pdf_path}")
        print()
        print("验证要点:")
        print("1. 总页数应该是 11 页（1 封面 + 10 场景）")
        print("2. 每个场景页面应该显示中文和英文双语")
        print("3. 场景页面底部应该显示页码（如 '- 2 -'）")
        print("4. 最后一页应该是第 10 个场景，不是空白页")
        print("=" * 60)

        return pdf_path

    except Exception as e:
        print(f"❌ PDF 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_pdf_generation()
