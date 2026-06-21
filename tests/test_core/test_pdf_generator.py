import pytest
from pathlib import Path
from PIL import Image
from storycraft.core.pdf_generator import PDFGenerator


@pytest.fixture
def sample_scenes(tmp_path):
    """Create sample scene data with temporary image files"""
    scenes = []
    for i in range(3):
        # Create a test image
        img_path = tmp_path / f"scene_{i+1}.png"
        img = Image.new('RGB', (800, 800), color=(255, 244, 181))  # Light cream color
        img.save(img_path)

        scenes.append({
            "text": f"这是第{i+1}个场景的故事内容",
            "image_path": str(img_path)
        })

    return scenes


@pytest.fixture
def pdf_generator(tmp_path):
    """Create PDFGenerator with temporary output directory"""
    output_dir = str(tmp_path / "output")
    return PDFGenerator(output_dir=output_dir)


class TestPDFGeneratorInit:
    """Test PDFGenerator initialization"""

    def test_creates_output_directory(self, tmp_path):
        """Test that output directory is created"""
        output_dir = tmp_path / "test_output"
        generator = PDFGenerator(output_dir=str(output_dir))

        assert output_dir.exists()
        assert generator.output_dir == output_dir

    def test_default_output_dir(self):
        """Test default output directory"""
        generator = PDFGenerator()
        assert generator.output_dir == Path("output")


class TestPDFGeneratorGenerate:
    """Test PDFGenerator.generate method"""

    def test_generate_creates_pdf_file(self, pdf_generator, sample_scenes):
        """Test that generate creates a PDF file"""
        pdf_path = pdf_generator.generate(sample_scenes, "测试故事")

        assert Path(pdf_path).exists()
        assert pdf_path.endswith(".pdf")

    def test_generate_with_chinese_title(self, pdf_generator, sample_scenes):
        """Test generating PDF with Chinese title"""
        pdf_path = pdf_generator.generate(sample_scenes, "小兔子的冒险")

        assert Path(pdf_path).exists()
        # Chinese characters are allowed in filenames on modern systems
        assert ".pdf" in pdf_path

    def test_generate_with_custom_author(self, pdf_generator, sample_scenes):
        """Test generating PDF with custom author"""
        pdf_path = pdf_generator.generate(sample_scenes, "Test Story", author="测试作者")

        assert Path(pdf_path).exists()

    def test_generate_returns_valid_path(self, pdf_generator, sample_scenes):
        """Test that generate returns a valid file path"""
        pdf_path = pdf_generator.generate(sample_scenes, "Test Story")

        # Verify it's an absolute path or valid relative path
        path = Path(pdf_path)
        assert path.name.endswith(".pdf")

    def test_generate_sanitizes_filename(self, pdf_generator, sample_scenes):
        """Test that special characters are removed from filename"""
        pdf_path = pdf_generator.generate(sample_scenes, "Test/Story:With*Special?Chars")

        # Should not contain special filesystem characters
        assert "/" not in Path(pdf_path).name
        assert "\\" not in Path(pdf_path).name
        assert ":" not in Path(pdf_path).name
        assert "*" not in Path(pdf_path).name
        assert "?" not in Path(pdf_path).name


class TestPDFGeneratorValidatePDF:
    """Test PDFGenerator.validate_pdf method"""

    def test_validate_pdf_with_valid_file(self, pdf_generator, sample_scenes):
        """Test validation of a valid PDF file"""
        pdf_path = pdf_generator.generate(sample_scenes, "Valid Story")

        assert pdf_generator.validate_pdf(pdf_path) is True

    def test_validate_pdf_with_nonexistent_file(self, pdf_generator):
        """Test validation fails for nonexistent file"""
        assert pdf_generator.validate_pdf("nonexistent.pdf") is False

    def test_validate_pdf_with_empty_file(self, pdf_generator, tmp_path):
        """Test validation fails for empty file"""
        empty_file = tmp_path / "empty.pdf"
        empty_file.write_text("")

        assert pdf_generator.validate_pdf(str(empty_file)) is False

    def test_validate_pdf_with_too_small_file(self, pdf_generator, tmp_path):
        """Test validation fails for files that are too small"""
        tiny_file = tmp_path / "tiny.pdf"
        tiny_file.write_bytes(b"PDF" * 100)  # Less than 1000 bytes

        assert pdf_generator.validate_pdf(str(tiny_file)) is False

    def test_validate_pdf_with_large_file(self, pdf_generator, tmp_path):
        """Test validation fails for files that are too large (>50MB)"""
        # Create a file larger than 50MB
        huge_file = tmp_path / "huge.pdf"
        huge_content = b"X" * (51 * 1024 * 1024)
        huge_file.write_bytes(huge_content)

        assert pdf_generator.validate_pdf(str(huge_file)) is False


class TestPDFGeneratorFontSetup:
    """Test font setup"""

    def test_chinese_font_set(self, pdf_generator):
        """Test that Chinese font is configured"""
        # Font should be set to either a Chinese font or fallback to Helvetica
        assert hasattr(pdf_generator, 'chinese_font')
        assert pdf_generator.chinese_font in ['Chinese', 'Helvetica']

    def test_styles_configured(self, pdf_generator):
        """Test that custom styles are configured"""
        assert 'CustomTitle' in pdf_generator.styles
        assert 'StoryText' in pdf_generator.styles


class TestPDFGeneratorIntegration:
    """Integration tests for PDF generation"""

    def test_generate_multiple_pdfs(self, pdf_generator, sample_scenes):
        """Test generating multiple PDFs with different titles"""
        titles = ["故事一", "故事二", "故事三"]

        for title in titles:
            pdf_path = pdf_generator.generate(sample_scenes, title)
            assert Path(pdf_path).exists()
            assert pdf_generator.validate_pdf(pdf_path)

        # Check that all PDFs were created
        pdf_files = list(pdf_generator.output_dir.glob("*.pdf"))
        assert len(pdf_files) >= len(titles)

    def test_generate_with_missing_image(self, pdf_generator, sample_scenes, tmp_path):
        """Test generating PDF when some images are missing"""
        # Add a scene with a non-existent image path
        scenes_with_missing = sample_scenes.copy()
        scenes_with_missing.append({
            "text": "这个场景没有图片",
            "image_path": str(tmp_path / "nonexistent.png")
        })

        # Should still generate PDF (PDF generation won't fail)
        pdf_path = pdf_generator.generate(scenes_with_missing, "Missing Image Test")
        assert Path(pdf_path).exists()
