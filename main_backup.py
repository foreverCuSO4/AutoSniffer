import sys
import os
import json
from src import config
from src import file_ops
from src import cmd_executor
from src import ai_service

def main():
    # 检查是否提供了目录路径参数，如果没有则使用默认配置
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        root_path = config.DEFAULT_ROOT_PATH

    # 验证路径是否存在且为目录
    if not os.path.isdir(root_path):
        print(f"错误: 提供的路径 '{root_path}' 不是一个有效的目录。")
        sys.exit(1)
        
    print(f"正在分析目录: {root_path} ...")

    # 获取目录结构
    directory_json_structure = file_ops.get_directory_structure(root_path)

    # 将字典转换为格式化的 JSON 字符串
    json_output = json.dumps(directory_json_structure, indent=4, ensure_ascii=False)
    print("目录结构分析完成。")
    # print(json_output) # 可选：打印目录结构

    try:
        print("正在请求 AI 生成整理方案...")
        ai = ai_service.AIService()
        cmd_instruction = ai.get_organization_plan(json_output)
        
        print("AI 方案生成成功，正在执行整理指令...")
        print("-" * 30)
        print(cmd_instruction)
        print("-" * 30)
        
        cmd_executor.execute_cmd_with_powershell(cmd_instruction, working_dir=root_path)
        
    except Exception as e:
        print(f"程序执行出错: {e}")

if __name__ == "__main__":
    main()
