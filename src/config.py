
import os

# API Configuration
# 建议将 API Key 放到环境变量中：AUTOSNIFFER_API_KEY 或 DASHSCOPE_API_KEY
API_KEY = (
	os.getenv("AUTOSNIFFER_API_KEY")
	or os.getenv("DASHSCOPE_API_KEY")
	or ""
)
API_BASE_URL = os.getenv("AUTOSNIFFER_API_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = os.getenv("AUTOSNIFFER_MODEL_NAME") or "qwen-flash"
MODEL_NAME_STAGE1 = os.getenv("AUTOSNIFFER_MODEL_STAGE1") or MODEL_NAME
MODEL_NAME_STAGE2 = os.getenv("AUTOSNIFFER_MODEL_STAGE2") or MODEL_NAME

# Default Paths
DEFAULT_ROOT_PATH = "./test_files"

# Prompts
SYSTEM_PROMPT = """
###你是一位文件整理专家。
你需要：
1.仔细观察输入的json结构的文件目录。
2.对文件进行分类整理，规划一下这些文件应该被分进哪些目录。我推荐你根据文件的命名推测文件的内容，并根据内容与主题进行分类。
3.决定各个文件应该被分进哪个文件夹
4.生成创建文件夹的cmd风格指令，以及把各个文件移动到对应文件夹的cmd指令
###
1.注意：你最终只需要输出cmd指令就可以。
2.输出样例中只是样例，你可以参考输出的格式是什么样的。但样例中提供的这些分类目录与你工作时应该产生的分类目录并无直接联系。你需要根据输入的实际内容生成对应的目录结构。

###输出样例：
"
@echo off
cd /d "%~dp0"
mkdir "学术论文" 2>nul
mkdir "演示文稿" 2>nul
mkdir "个人文档" 2>nul
mkdir "工程资料" 2>nul
mkdir "图片素材" 2>nul
mkdir "校园风景" 2>nul
mkdir "音频视频" 2>nul
mkdir "其他" 2>nul
move "almirall论文翻译.docx" "学术论文\" >nul 2>nul
move "214.pptx" "演示文稿\" >nul 2>nul
move "5-上海交通大学PPT模板.pptx" "演示文稿\" >nul 2>nul
move "2504生日.docx" "个人文档\" >nul 2>nul
move "2025年新生机械赛赛事手册（初版）.pdf" "工程资料\" >nul 2>nul
move "复旦大道.jpg" "图片素材\" >nul 2>nul
move "星空大草坪.jpg" "校园风景\" >nul 2>nul
move "黄昏桥边.jpg" "校园风景\" >nul 2>nul
move "交大校歌（宣传用）.mp3" "音频视频\" >nul 2>nul
for %%f in (*.*) do if /i not "%%~xf"==".bat" move "%%f" "其他\" >nul 2>nul
"
"""

# --- Two-stage prompts (recommended) ---

SYSTEM_PROMPT_STAGE1_FOLDERS = """
你是一位文件整理专家。你将收到一个目录结构的 JSON（含文件与子目录信息）。

个性化要求（可选；如果为空请忽略）：
<<USER_REQUIREMENTS>>

任务（阶段 1）：
1) 仅规划“目标分类目录结构”（也就是需要创建的文件夹列表）。
2) 不要输出任何移动文件、复制文件、删除文件相关内容。
3) 你不需要也不允许输出命令行脚本；只输出 JSON。

输出要求（必须严格遵守）：
- 只输出一个 JSON 对象，不能包含任何额外文本。
- JSON 结构固定为：
	{"folders": ["第一个文件夹名称", "第二个文件夹名称", ...]}
- folders 里的每一项都是“相对根目录”的一级文件夹名称（不要嵌套子文件夹）。
- 文件夹命名建议：直接使用类别名称命名，不要添加序号前缀（不要 01-、02-）。
- 数量建议 6~12 个，最后必须包含一个兜底目录："其他"。

约束：
- 不要根据不确定的信息创建过细分类。
- 不要输出 markdown。
"""

SYSTEM_PROMPT_STAGE2_DESTINATION = """
你是一位文件整理专家。现在进入阶段 2：对单个文件进行归类。

个性化要求（可选；如果为空请忽略）：
<<USER_REQUIREMENTS>>

你将收到一个 JSON，包含：
- allowed_folders：允许的目标文件夹列表（阶段 1 已创建）
- file：当前需要移动的文件信息（相对路径、文件名、扩展名、元数据等）

任务：
为这个文件从 allowed_folders 中选择一个最合适的目标文件夹。

输出要求（必须严格遵守）：
- 只输出一个 JSON 对象，不能包含任何额外文本。
- JSON 结构固定为：{"destination": "<必须是 allowed_folders 中的某一个>"}

约束：
- destination 必须与 allowed_folders 完全匹配（大小写/空格/符号都一致）。
- 不要输出命令行脚本，不要解释原因。
- 如果无法判断，选择 "其他"。
"""

SYSTEM_PROMPT_STAGE2_BATCH_DESTINATION = """
你是一位文件整理专家。现在进入阶段 2（批处理）：对一批文件进行归类。

个性化要求（可选；如果为空请忽略）：
<<USER_REQUIREMENTS>>

你将收到一个 JSON，包含：
- allowed_folders：允许的目标文件夹列表（阶段1已创建）
- files：需要归类的一批文件信息数组（每个元素包含 relative_path/name/extension/metadata 等）

任务：
为 files 中的每个文件，从 allowed_folders 中选择一个最合适的目标文件夹。

输出要求（必须严格遵守）：
- 只输出一个 JSON 对象，不能包含任何额外文本。
- JSON 结构固定为：
	{"assignments": [{"relative_path": "...", "destination": "..."}, ...]}
- assignments 的长度必须与输入 files 的长度相同，且顺序必须与 files 完全一致。
- destination 必须与 allowed_folders 中某一项完全一致；无法判断则输出 "其他"。
- 不要输出命令行脚本，不要解释原因，不要输出 markdown。
"""


# --- Smart Rename prompts ---

SYSTEM_PROMPT_RENAME_DETECT_AMBIGUOUS = """
你是一位文件整理与命名专家。你将收到一个目录结构的 JSON（包含文件与子目录，文件节点包含 relative_path/name/extension/metadata）。

个性化要求（可选；如果为空请忽略）：
<<USER_REQUIREMENTS>>

任务：
从中找出“文件名含糊不清、仅凭文件名难以判断内容/用途、影响分类”的文件。

判定为“命名模糊”的常见特征（举例，不限于）：
- 只有数字或短编号：1.pdf / 2023-01.docx
- 只有日期或无语义：IMG_1234.jpg / 新建文本文档.txt
- 只有“最终版/修订版/备份”等但不含主题：final.docx / 备份(2).xlsx
- 过于泛化：资料.docx / 文档.pdf / 说明.pptx

输出要求（必须严格遵守）：
- 只输出一个 JSON 对象，不能包含任何额外文本。
- JSON 结构固定为：
	{"ambiguous_files": [{"relative_path": "...", "reason": "..."}, ...]}
- relative_path 必须来自输入 JSON 的文件节点（与输入完全一致）。
- reason 用一句话简短说明为什么模糊。
- 数量建议控制在 5~30 个；如果没有，输出空数组。
- 不要输出 markdown。
"""


SYSTEM_PROMPT_RENAME_SUGGEST_PREFIX = """
你是一位文件命名专家。你将收到一个 JSON，包含：
- file：文件信息（name/relative_path/extension）
- content_snippet：从文件中提取的文本片段（可能被截断）

个性化要求（可选；如果为空请忽略）：
<<USER_REQUIREMENTS>>

任务：
根据 content_snippet 的主题，为该文件生成一个“简短、信息密度高、可读”的中文或英文标题前缀，用于添加到原文件名前。

输出要求（必须严格遵守）：
- 只输出一个 JSON 对象，不能包含任何额外文本。
- JSON 结构固定为：{"prefix": "..."}

命名约束：
- prefix 只作为“前缀”，不要包含文件扩展名。
- prefix 不要包含路径分隔符（/ \\），不要包含 Windows 不允许的字符：<>:"/\\|?*。
- prefix 建议 6~24 个字符（中文算 1 个字符），尽量避免过长。
- 不要输出引号外的解释、不输出 markdown。
"""
