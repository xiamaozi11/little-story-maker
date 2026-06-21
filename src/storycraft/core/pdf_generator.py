from pathlib import Path
from typing import Dict, List
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage, Table
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas
from PIL import Image as PILImage
import os
import random
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter

class PDFGenerator:
    """生成适合 Kindle 阅读的美化 PDF"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self._setup_fonts()
        self.styles = getSampleStyleSheet()
        self._setup_styles()

        # 导入压缩配置
        from storycraft.config import PDF_IMAGE_QUALITY, PDF_MAX_IMAGE_DIMENSION
        self.image_quality = PDF_IMAGE_QUALITY
        self.max_dimension = PDF_MAX_IMAGE_DIMENSION

    def _setup_fonts(self):
        """设置中文字体"""
        try:
            font_paths = [
                "C:/Windows/Fonts/simhei.ttf",
                "C:/Windows/Fonts/simsun.ttc",
                "/System/Library/Fonts/PingFang.ttc",
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Chinese', font_path))
                    self.chinese_font = 'Chinese'
                    return
            self.chinese_font = 'Helvetica'
        except Exception:
            self.chinese_font = 'Helvetica'

    def _setup_styles(self):
        """设置文档样式"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.chinese_font,
            fontSize=42,  # 从 48 改为 42，避免两行标题重叠
            spaceAfter=30,
            leading=56,  # 增加行距，避免两行重叠
            alignment=TA_CENTER,
            textColor=HexColor('#2C3E50')
        ))
        self.styles.add(ParagraphStyle(
            name='Author',
            parent=self.styles['BodyText'],
            fontName=self.chinese_font,
            fontSize=20,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=HexColor('#7F8C8D')
        ))
        self.styles.add(ParagraphStyle(
            name='StoryText',
            parent=self.styles['BodyText'],
            fontName=self.chinese_font,
            fontSize=20,  # 从24改为20，避免超出边界
            spaceAfter=12,
            leading=32,  # 从36改为32，调整行距
            alignment=TA_LEFT,  # 改为左对齐
            leftIndent=0,
            rightIndent=0,
            wordWrap='CJK'  # 优化中文换行
        ))
        self.styles.add(ParagraphStyle(
            name='StoryTextEN',
            parent=self.styles['BodyText'],
            fontName='Helvetica',  # 使用标准英文字体
            fontSize=16,  # 英文稍小
            spaceAfter=18,
            leading=24,
            alignment=TA_LEFT,  # 左对齐
            leftIndent=0,
            rightIndent=0,
            textColor=HexColor('#666666')  # 灰色区分中英文
        ))
        self.styles.add(ParagraphStyle(
            name='PageNumber',
            parent=self.styles['BodyText'],
            fontName=self.chinese_font,
            fontSize=12,
            alignment=TA_CENTER,
            textColor=HexColor('#95A5A6')
        ))

    def _compress_image(self, image_path: str) -> str:
        """压缩图片以减少PDF文件大小"""
        try:
            if not Path(image_path).exists():
                print(f"图片文件不存在: {image_path}")
                return image_path

            with PILImage.open(image_path) as img:
                width, height = img.size

                if width > self.max_dimension or height > self.max_dimension:
                    if width > height:
                        new_width = self.max_dimension
                        new_height = int(height * (self.max_dimension / width))
                    else:
                        new_height = self.max_dimension
                        new_width = int(width * (self.max_dimension / height))
                else:
                    new_width, new_height = width, height

                img_resized = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)

                if img_resized.mode != 'RGB':
                    img_resized = img_resized.convert('RGB')

                path_obj = Path(image_path)
                compressed_path = str(path_obj.parent / f"{path_obj.stem}_compressed.jpg")
                img_resized.save(compressed_path, 'JPEG', quality=self.image_quality, optimize=True)

                if Path(compressed_path).exists() and Path(compressed_path).stat().st_size > 0:
                    return compressed_path
                else:
                    return image_path

        except Exception as e:
            print(f"压缩图片失败 {image_path}: {e}")
            return image_path

    def _create_cover_page(self, title: str, author: str, cover_image_path: str = None) -> List:
        """创建封面页（不带页码）"""
        story = []

        # 添加装饰性边框
        story.append(Spacer(1, 0.5*inch))

        # 创建标题
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))

        # 添加作者信息
        story.append(Paragraph(f"作者：{author}", self.styles['Author']))
        story.append(Spacer(1, 1*inch))

        # 如果有封面图片，添加到封面
        if cover_image_path and Path(cover_image_path).exists():
            try:
                compressed_path = self._compress_image(cover_image_path)
                with PILImage.open(compressed_path) as test_img:
                    img_width, img_height = test_img.size

                # 封面图片大一点
                aspect_ratio = img_height / img_width
                target_width = 5 * inch
                target_height = target_width * aspect_ratio

                max_height = 5 * inch  # 从 6 inch 改为 5 inch 以适应 A4 页面
                if target_height > max_height:
                    target_height = max_height
                    target_width = target_height / aspect_ratio

                img = RLImage(compressed_path, width=target_width, height=target_height)
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 0.5*inch))
            except Exception as e:
                print(f"添加封面图片失败: {e}")

        return story

    def generate(self, scenes: List[Dict], title: str, author: str = "AI 绘本生成器") -> str:
        """生成美化的 PDF 文件 - 分别生成封面和内容，然后合并"""
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        filename = f"{safe_title}.pdf"
        pdf_path = self.output_dir / filename

        # 临时文件路径
        cover_pdf_path = self.output_dir / f"{safe_title}_cover_temp.pdf"
        content_pdf_path = self.output_dir / f"{safe_title}_content_temp.pdf"

        # 随机选择一张场景图片作为封面
        cover_image = None
        if scenes:
            cover_scene = random.choice(scenes)
            cover_image = cover_scene['image_path']

        # 步骤1: 生成封面PDF（只包含一页封面）
        self._generate_cover_pdf(str(cover_pdf_path), title, author, cover_image)

        # 步骤2: 生成内容PDF（从第一页开始包含所有场景）
        self._generate_content_pdf(str(content_pdf_path), scenes)

        # 步骤3: 合并封面和内容PDF
        self._merge_pdfs([str(cover_pdf_path), str(content_pdf_path)], str(pdf_path))

        # 步骤4: 删除所有空白页
        self._remove_blank_pages(str(pdf_path))

        # 清理临时文件
        cover_pdf_path.unlink(missing_ok=True)
        content_pdf_path.unlink(missing_ok=True)

        return str(pdf_path)

    def _generate_cover_pdf(self, pdf_path: str, title: str, author: str, cover_image_path: str) -> None:
        """生成封面PDF（只有一页）"""
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=1*inch,
            rightMargin=1*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )

        story_content = []

        # 封面装饰函数（无页码）
        def on_cover_page(canvas, doc):
            canvas.saveState()
            page_width, page_height = A4
            margin = 50

            # 外边框
            canvas.setStrokeColorRGB(0.8, 0.8, 0.8)
            canvas.setLineWidth(2)
            canvas.rect(margin, margin, page_width - 2*margin, page_height - 2*margin)

            # 内边框
            canvas.setStrokeColorRGB(0.6, 0.6, 0.6)
            canvas.setLineWidth(1)
            canvas.rect(margin + 10, margin + 10, page_width - 2*margin - 20, page_height - 2*margin - 20)

            # 装饰性角落
            corner_size = 30
            canvas.setStrokeColorRGB(0.4, 0.6, 0.8)
            canvas.setLineWidth(3)

            canvas.line(margin, margin + corner_size, margin, margin)
            canvas.line(margin, margin, margin + corner_size, margin)
            canvas.line(page_width - margin - corner_size, margin, page_width - margin, margin)
            canvas.line(page_width - margin, margin, page_width - margin, margin + corner_size)
            canvas.line(margin, page_height - margin - corner_size, margin, page_height - margin)
            canvas.line(margin, page_height - margin, margin + corner_size, page_height - margin)
            canvas.line(page_width - margin - corner_size, page_height - margin, page_width - margin, page_height - margin)
            canvas.line(page_width - margin, page_height - margin, page_width - margin, page_height - margin - corner_size)

            canvas.restoreState()

        # 添加封面内容
        cover_content = self._create_cover_page(title, author, cover_image_path)
        for item in cover_content:
            story_content.append(item)

        # 生成封面PDF（只有一页）
        doc.build(story_content, onFirstPage=on_cover_page, onLaterPages=on_cover_page)

    def _generate_content_pdf(self, pdf_path: str, scenes: List[Dict]) -> None:
        """生成内容PDF（从第一页开始包含所有场景）"""
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=1*inch,
            rightMargin=1*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )

        story_content = []
        page_counter = [0]

        # 内容页装饰函数（带页码）
        def on_content_page(canvas, doc):
            canvas.saveState()
            page_counter[0] += 1
            current_page = page_counter[0]

            page_width, page_height = A4
            margin = 50

            # 绘制边框
            canvas.setStrokeColorRGB(0.7, 0.7, 0.7)
            canvas.setLineWidth(1.5)
            canvas.rect(margin, margin, page_width - 2*margin, page_height - 2*margin)

            # 内细线
            canvas.setStrokeColorRGB(0.85, 0.85, 0.85)
            canvas.setLineWidth(0.5)
            canvas.rect(margin + 5, margin + 5, page_width - 2*margin - 10, page_height - 2*margin - 10)

            # 添加页码（使用固定坐标，距离底部 85 点）
            page_num_y = 85
            page_num_text = f"- {current_page} -"

            # 页码文本（使用英文字体，确保可提取）
            canvas.setFont('Helvetica', 14)
            canvas.setFillColorRGB(0.3, 0.3, 0.3)
            canvas.drawCentredString(page_width / 2, page_num_y, page_num_text)

            canvas.restoreState()

        # 添加所有场景内容
        for idx, scene in enumerate(scenes, 1):
            print(f"\n处理场景 {idx}/{len(scenes)}")
            print(f"  场景文本: {scene.get('text', '')[:50]}...")
            print(f"  英文文本: {scene.get('text_en', '')[:50]}...")

            img_path = scene['image_path']
            print(f"  图片路径: {img_path}")

            # 从第二个场景开始，每个都从新页开始
            if idx > 1:
                print(f"  添加分页符")
                story_content.append(PageBreak())

            if Path(img_path).exists():
                try:
                    compressed_img_path = self._compress_image(img_path)
                    with PILImage.open(compressed_img_path) as test_img:
                        img_width, img_height = test_img.size

                    target_width = 5.5 * inch
                    aspect_ratio = img_height / img_width
                    target_height = target_width * aspect_ratio

                    max_height = 6.5 * inch
                    if target_height > max_height:
                        target_height = max_height
                        target_width = target_height / aspect_ratio

                    img = RLImage(compressed_img_path, width=target_width, height=target_height)
                    img.hAlign = 'CENTER'
                    story_content.append(img)
                    story_content.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    print(f"图片验证失败，仅跳过图片: {img_path}, 错误: {e}")

            # 添加文本（中英文双语）
            text = scene['text']
            story_content.append(Paragraph(text, self.styles['StoryText']))

            # 如果有英文文本，添加英文版本
            text_en = scene.get('text_en', '')
            print(f"  检查英文翻译: text_en='{text_en}' (长度: {len(text_en)})")
            if text_en:
                print(f"  添加英文翻译到 PDF")
                story_content.append(Paragraph(text_en, self.styles['StoryTextEN']))
                story_content.append(Spacer(1, 0.3*inch))
            else:
                print(f"  警告: 英文翻译为空，跳过")
                story_content.append(Spacer(1, 0.3*inch))

        print(f"内容PDF总共包含 {len(story_content)} 个flowables")
        # 生成内容PDF
        doc.build(story_content, onFirstPage=on_content_page, onLaterPages=on_content_page)

    def _merge_pdfs(self, pdf_paths: List[str], output_path: str) -> None:
        """合并多个PDF文件"""
        writer = PdfWriter()

        for pdf_path in pdf_paths:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                writer.add_page(page)

        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

    def _delete_page(self, pdf_path: str, page_index: int) -> None:
        """删除PDF文件的指定页（0-based索引）

        Args:
            pdf_path: PDF文件路径
            page_index: 要删除的页码索引（0-based，例如第2页是index=1）
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # 添加除了指定页之外的所有页
        for i, page in enumerate(reader.pages):
            if i != page_index:
                writer.add_page(page)

        # 覆盖原文件
        with open(pdf_path, 'wb') as output_file:
            writer.write(output_file)

    def _remove_blank_pages(self, pdf_path: str) -> None:
        """删除PDF中的所有空白页

        Args:
            pdf_path: PDF文件路径
        """
        BLANK_PAGE_THRESHOLD = 80  # 增加阈值，捕获只包含少量字符的页面

        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        blank_pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text().strip()

            # 检查是否为空白页（文本长度小于阈值，或者只包含空格/控制字符）
            if len(page_text) < BLANK_PAGE_THRESHOLD:
                # 进一步检查：如果包含中文或实质性英文内容，不算空白页
                has_content = False
                if any('\u4e00' <= c <= '\u9fff' for c in page_text):  # 包含中文
                    has_content = True
                elif any(c.isalpha() and len([ch for ch in page_text if ch.isalpha()]) > 10 for c in page_text):  # 包含足够的字母
                    has_content = True

                if not has_content:
                    blank_pages.append((i + 1, i, len(page_text)))
                    continue

            writer.add_page(page)

        if blank_pages:
            for page_num, page_idx, text_len in blank_pages:
                print(f"发现空白页: 第{page_num}页（索引{page_idx}），文本长度: {text_len}")
            print(f"总共删除了 {len(blank_pages)} 个空白页")
            with open(pdf_path, 'wb') as output_file:
                writer.write(output_file)
        else:
            print("没有发现空白页")

    def validate_pdf(self, pdf_path: str) -> bool:
        """验证 PDF 文件有效性"""
        if not Path(pdf_path).exists():
            return False
        file_size = Path(pdf_path).stat().st_size
        return 1000 < file_size < 50 * 1024 * 1024


# 辅助类：用于切换页面模板
from reportlab.platypus.flowables import Flowable

class NextPageTemplate(Flowable):
    """切换到下一个页面模板"""
    def __init__(self, template_name):
        self.template_name = template_name
        self.width = 0
        self.height = 0

    def draw(self):
        # 切换页面模板
        if self.template_name and hasattr(self.canv._doc, 'pageTemplate'):
            # 找到目标模板
            templates = self.canv._doc.pageTemplates
            for template in templates:
                if template.id == self.template_name:
                    self.canv._doc.pageTemplate = template
                    break
