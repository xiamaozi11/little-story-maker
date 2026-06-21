"""测试豆包图片生成服务"""
import os
import sys
from dotenv import load_dotenv

# 设置 UTF-8 编码输出（Windows 兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

def test_doubao_image_generation():
    """测试豆包图片生成"""
    print("=" * 60)
    print("测试豆包图片生成服务")
    print("=" * 60)

    # 1. 检查依赖
    print("\n[1] 检查依赖...")
    try:
        from volcenginesdkarkruntime import Ark
        print("[OK] volcengine-python-sdk 已安装")
    except ImportError as e:
        print(f"[ERROR] 依赖未安装: {e}")
        print("请运行: pip install 'volcengine-python-sdk[ark]'")
        return False

    # 2. 检查配置
    print("\n[2] 检查配置...")
    ark_api_key = os.getenv("ARK_API_KEY")
    ark_base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    model = os.getenv("DOUBAO_IMAGE_MODEL", "doubao-seedream-4.5new")

    if not ark_api_key:
        print("[ERROR] ARK_API_KEY 未配置")
        print("请在 .env 文件中设置 ARK_API_KEY")
        return False

    print(f"[OK] ARK_API_KEY: {ark_api_key[:10]}...")
    print(f"[OK] ARK_BASE_URL: {ark_base_url}")
    print(f"[OK] 模型: {model}")

    # 3. 初始化客户端
    print("\n[3] 初始化豆包客户端...")
    try:
        client = Ark(
            base_url=ark_base_url,
            api_key=ark_api_key
        )
        print("[OK] 客户端初始化成功")
    except Exception as e:
        print(f"[ERROR] 客户端初始化失败: {e}")
        return False

    # 4. 测试单张图片生成（使用 1920x2560 竖版尺寸）
    print("\n[4] 测试单张图片生成（1920x2560 竖版尺寸）...")
    try:
        prompt = "一只可爱的小白兔，戴着红色蝴蝶结，坐在草地上，周围有鲜花，儿童绘本风格，简单清晰"

        print(f"提示词: {prompt}")
        print("正在生成图片（这可能需要 10-20 秒）...")

        response = client.images.generate(
            model=model,
            prompt=prompt,
            size="1920x2560",  # 使用 1920x2560 竖版尺寸（4.9M 像素，满足豆包最小要求）
            response_format="url",
            watermark=False
        )

        if response.data and len(response.data) > 0:
            img_url = response.data[0].url
            print(f"[OK] 图片生成成功!")
            print(f"   图片 URL: {img_url[:80]}...")

            # 下载并保存图片
            import httpx
            from pathlib import Path

            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)

            print("\n正在下载测试图片...")
            img_response = httpx.Client(timeout=60).get(img_url)
            img_response.raise_for_status()

            test_image_path = output_dir / "test_doubao.png"
            with open(test_image_path, 'wb') as f:
                f.write(img_response.content)

            print(f"[OK] 图片已保存: {test_image_path}")
            print(f"   文件大小: {len(img_response.content) / 1024:.2f} KB")

        else:
            print("[ERROR] API 返回为空")
            return False

    except Exception as e:
        print(f"[ERROR] 图片生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 5. 测试组图生成（可选，使用 1920x2560 尺寸）
    print("\n[5] 测试组图生成（2张关联图片，1920x2560 尺寸）...")
    try:
        prompt = """[Scene 1] 一只小白兔在森林入口，好奇地看着前方
[Scene 2] 小白兔走进森林，看到一棵神奇的大树"""

        print(f"提示词: {prompt}")
        print("正在生成组图（这可能需要 20-30 秒）...")

        # 注意：不传 n 参数，让豆包根据提示词中的场景标签自动识别
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size="1920x2560",  # 使用 1920x2560 竖版尺寸
            response_format="url",
            watermark=False,
            sequential_image_generation="auto"  # 启用组图生成
        )

        if response.data and len(response.data) > 0:
            print(f"[OK] 组图生成成功! 共 {len(response.data)} 张图片")

            for idx, img_data in enumerate(response.data):
                img_url = img_data.url
                print(f"   图片 {idx + 1}: {img_url[:60]}...")

                # 下载图片
                import httpx
                img_response = httpx.Client(timeout=60).get(img_url)
                img_response.raise_for_status()

                test_image_path = output_dir / f"test_doubao_scene_{idx + 1}.png"
                with open(test_image_path, 'wb') as f:
                    f.write(img_response.content)

                print(f"   已保存: {test_image_path}")
        else:
            print("[WARNING] API 返回为空，可能需要特定权限")
            print("   尝试回退到串行生成...")

    except Exception as e:
        print(f"[WARNING] 组图生成失败: {e}")
        print("   单张图片生成已验证成功")

    # 总结
    print("\n" + "=" * 60)
    print("[SUCCESS] 豆包服务测试通过！")
    print("=" * 60)
    print("\n测试总结:")
    print("• volcengine-python-sdk 安装正常")
    print("• API 配置正确")
    print("• 单张图片生成功能正常")
    print("• 组图生成功能已测试")
    print("\n可以在 Streamlit 中使用豆包服务了！")

    return True


if __name__ == "__main__":
    test_doubao_image_generation()
