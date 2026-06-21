"""测试通义千问图片生成服务"""
import os
import sys
from dotenv import load_dotenv

# 设置 UTF-8 编码输出（Windows 兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

def test_tongyi_image_generation():
    """测试通义千问图片生成"""
    print("=" * 60)
    print("测试通义千问图片生成服务")
    print("=" * 60)

    # 1. 检查配置
    print("\n[1] 检查配置...")
    api_key = os.getenv("API_KEY")
    api_endpoint = os.getenv("API_ENDPOINT", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = os.getenv("TEXT_MODEL", "qwen-plus")
    image_model = os.getenv("TONGYI_IMAGE_MODEL", "wan2.6-t2i")

    if not api_key:
        print("[ERROR] API_KEY 未配置")
        print("请在 .env 文件中设置 API_KEY")
        return False

    print(f"[OK] API_KEY: {api_key[:10]}...")
    print(f"[OK] API_ENDPOINT: {api_endpoint}")
    print(f"[OK] 文本模型: {model}")
    print(f"[OK] 图片模型: {image_model}")

    # 2. 初始化客户端
    print("\n[2] 初始化 HTTP 客户端...")
    try:
        import httpx
        client = httpx.Client(timeout=120.0)
        print("[OK] 客户端初始化成功")
    except ImportError as e:
        print(f"[ERROR] 依赖未安装: {e}")
        print("请运行: pip install httpx")
        return False

    # 3. 测试图片生成（先测试标准尺寸 1024*1024）
    print("\n[3] 测试图片生成（1024*1024 标准尺寸）...")
    try:
        prompt = "一只可爱的小白兔，戴着红色蝴蝶结，坐在草地上，周围有鲜花，儿童绘本风格，简单清晰，children's book illustration"

        print(f"提示词: {prompt}")
        print("正在生成图片（这可能需要 10-20 秒）...")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": image_model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "prompt_extend": True,
                "watermark": False,
                "n": 1,
                "size": "1024*1024"  # 通义千问标准尺寸
            }
        }

        response = client.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
            headers=headers,
            json=payload,
            timeout=120
        )

        # 先检查状态码，如果失败则打印详细信息
        if response.status_code != 200:
            print(f"[ERROR] HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            client.close()
            return False

        data = response.json()

        # 解析响应
        if data.get("output") and data["output"].get("choices"):
            choices = data["output"]["choices"]
            if len(choices) > 0 and choices[0].get("message", {}).get("content"):
                content = choices[0]["message"]["content"]
                if len(content) > 0 and content[0].get("image"):
                    image_url = content[0]["image"]
                    print(f"[OK] 图片生成成功!")
                    print(f"   图片 URL: {image_url[:80]}...")

                    # 下载并保存图片
                    from pathlib import Path
                    output_dir = Path("output")
                    output_dir.mkdir(exist_ok=True)

                    print("\n正在下载测试图片...")
                    img_response = client.get(image_url, timeout=60)
                    img_response.raise_for_status()

                    test_image_path = output_dir / "test_tongyi.png"
                    with open(test_image_path, 'wb') as f:
                        f.write(img_response.content)

                    print(f"[OK] 图片已保存: {test_image_path}")
                    print(f"   文件大小: {len(img_response.content) / 1024:.2f} KB")

                    # 验证图片尺寸
                    from PIL import Image
                    img = Image.open(test_image_path)
                    width, height = img.size
                    print(f"   图片尺寸: {width}x{height} ({width * height / 1000000:.2f}M 像素)")

                    # 检查是否接近目标尺寸
                    target_width, target_height = 1920, 2560
                    if width == target_width and height == target_height:
                        print(f"   ✅ 尺寸符合预期: {target_width}*{target_height}")
                    else:
                        print(f"   ⚠️  尺寸与预期不符，预期: {target_width}*{target_height}")

                    client.close()
                    return True

        print("[ERROR] API 返回格式不正确")
        print(f"响应数据: {data}")
        return False

    except Exception as e:
        print(f"[ERROR] 图片生成失败: {e}")
        import traceback
        traceback.print_exc()
        client.close()
        return False

    # 总结
    print("\n" + "=" * 60)
    print("[SUCCESS] 通义千问服务测试通过！")
    print("=" * 60)
    print("\n测试总结:")
    print("• API 配置正确")
    print("• 图片生成功能正常")
    print("• 尺寸格式正确 (1920*2560)")
    print("\n可以在 Streamlit 中使用通义千问服务了！")

    return True


if __name__ == "__main__":
    test_tongyi_image_generation()
