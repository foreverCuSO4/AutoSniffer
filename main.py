import os
import sys
import json
from src import config
from src import file_ops
from src import cmd_executor
from src.workflow import OrganizerWorkflow

def main():
    # 检查是否提供了目录路径参数
    # if len(sys.argv) < 2:
    #     print("用法: python main.py <目录路径>")
    #     sys.exit(1)
    
    # 从命令行参数获取根目录，或者使用配置中的默认路径
    # root_path = sys.argv[1] if len(sys.argv) > 1 else config.DEFAULT_ROOT_PATH
    root_path = config.DEFAULT_ROOT_PATH

    # 验证路径是否存在且为目录
    if not os.path.isdir(root_path):
        print(f"错误: 提供的路径 '{root_path}' 不是一个有效的目录。")
        sys.exit(1)
        
    wf = OrganizerWorkflow()

    # 获取目录结构
    print(f"正在分析目录: {root_path} ...")
    directory_json_structure = file_ops.get_directory_structure(root_path)

    # 将字典转换为格式化的 JSON 字符串并打印
    json_output = json.dumps(directory_json_structure, indent=4, ensure_ascii=False)
    print("目录结构分析完成。")

    # 阶段1：生成并创建文件夹
    print("阶段1：请求 AI 生成目标分类目录...")
    folders = wf.stage1_plan_folders(json_output, model=getattr(config, "MODEL_NAME_STAGE1", None))
    mkdir_script = wf.build_mkdir_script(folders)
    print("阶段1：将创建以下文件夹：")
    for f in folders:
        print(f"- {f}")
    print("阶段1：正在创建文件夹...")
    cmd_executor.execute_cmd_with_powershell(mkdir_script, working_dir=root_path)

    # 阶段2：批量（每次 N 个文件）归类并移动
    batch_size = int(os.getenv("AUTOSNIFFER_STAGE2_BATCH_SIZE") or "5")
    if batch_size <= 0:
        batch_size = 1
    print(f"阶段2：开始批量归类并移动（每批 {batch_size} 个）...")
    decisions, batch_results = wf.stage2_process_files_batched(
        root_path=root_path,
        structure=directory_json_structure,
        allowed_folders=folders,
        batch_size=batch_size,
        timeout_seconds=300,
        model=getattr(config, "MODEL_NAME_STAGE2", None),
    )
    total_files = len(decisions)
    total_batches = len(batch_results)
    ok_batches = sum(1 for r in batch_results if r.return_code == 0)
    print(f"阶段2完成：文件 {total_files} 个，批次 {ok_batches}/{total_batches} 成功")

if __name__ == "__main__":
    main()
