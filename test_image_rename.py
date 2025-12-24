"""
测试图片重命名功能
该脚本演示如何使用多模态AI识别图片内容并生成重命名前缀
"""
import os
from src.workflow import OrganizerWorkflow
from src.ai_service import AIService

def test_image_processing():
    # 初始化服务
    api_key = os.getenv("AUTOSNIFFER_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("错误：未设置 API Key。请设置环境变量 AUTOSNIFFER_API_KEY 或 DASHSCOPE_API_KEY")
        return
    
    ai_service = AIService(api_key=api_key)
    workflow = OrganizerWorkflow(ai_service=ai_service)
    
    # 测试图片检测
    test_files = [
        "test.jpg",
        "document.docx",
        "photo.png",
        "image.JPEG",
        "data.xlsx"
    ]
    
    print("=== 测试图片文件检测 ===")
    for file in test_files:
        is_image = workflow._is_image_file(file)
        print(f"{file}: {'✓ 图片' if is_image else '✗ 非图片'}")
    
    print("\n=== 图片处理功能 ===")
    print("功能说明：")
    print("1. 自动检测图片文件（.jpg, .jpeg, .png, .gif, .bmp, .webp, .tiff）")
    print("2. 如果图片超过 1920x1080 像素，自动 resize 到该范围内")
    print("3. 将图片转换为 base64 编码")
    print("4. 调用 qwen-vl-max 多模态模型识别图片内容")
    print("5. AI 生成简洁的中文描述作为文件名前缀")
    print("\n注意：实际调用需要：")
    print("- 有效的图片文件路径")
    print("- 配置好的 API Key")
    print("- 使用支持多模态的模型（如 qwen-vl-max）")
    
    # 如果有测试图片，可以取消下面的注释进行实际测试
    """
    test_image_path = "./test_files/02-图片素材/test.jpg"
    if os.path.exists(test_image_path):
        print(f"\n=== 测试图片: {test_image_path} ===")
        file_item = {
            "name": "test.jpg",
            "relative_path": "02-图片素材/test.jpg",
            "extension": ".jpg"
        }
        try:
            prefix = workflow.rename_suggest_prefix_for_image(
                "./test_files",
                file_item,
                model="qwen-vl-max"
            )
            print(f"AI 生成的重命名前缀: {prefix}")
            print(f"建议新文件名: {prefix}_test.jpg")
        except Exception as e:
            print(f"处理失败: {e}")
    """

if __name__ == "__main__":
    test_image_processing()
