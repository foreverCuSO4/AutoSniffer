# AutoSniffer / 智能文件整理

AutoSniffer 是一个基于大模型（OpenAI 兼容接口，如阿里云 DashScope/Qwen）的**两阶段文件整理工具**，提供桌面 GUI（Flet）来扫描目录、生成分类目录、批量归类移动文件，并支持“撤销上一次整理”（尽量还原到执行前状态，遇到冲突会自动改名保留）。

AutoSniffer is a **two-stage AI-powered file organizer** (OpenAI-compatible API, e.g. DashScope/Qwen) with a desktop GUI (Flet). It scans a folder, proposes categories, moves files in batches, and supports **Undo last run** (best-effort restore with conflict-safe renaming).

---

## Features / 功能

- Two-stage workflow / 两阶段流程
	- Stage 1: only plans folders, then creates folders / 阶段1：仅规划分类目录并创建文件夹
	- Stage 2: batch classification + move / 阶段2：按批调用模型归类并移动文件
- GUI (Flet) with progress + stop / 图形界面、进度展示、可停止
- Best-effort Undo last run / “撤销上一次”（尽量还原）
	- Uses a journal under `.autosniffer_history/` / 使用 `.autosniffer_history/` 日志
	- Conflict-safe renaming on restore / 冲突时自动改名保留两份
- Optional text extraction tool / 附带文本提取脚本
	- Extract text from `pdf/docx/pptx/xlsx/txt/...` for inspection / 支持多格式文本提取

---

## Project Structure / 项目结构

- `ui_app.py`: GUI entry (Flet) / GUI 入口
- `src/workflow.py`: core workflow (scan/plan/move/undo) / 业务编排（扫描/规划/移动/撤销）
- `src/ai_service.py`: AI calls (OpenAI SDK) / 大模型调用封装
- `src/cmd_executor.py`: PowerShell runner (used by legacy CLI/batch scripts) / PowerShell 执行器（主要用于旧脚本/CLI）
- `main.py`: CLI demo (two-stage batch) / CLI 示例
- `extract.py`: text extraction utility / 文本提取工具

---

## Requirements / 环境依赖

- Windows recommended / 推荐 Windows（项目内的执行器与路径处理主要面向 Windows）
- Python 3.9+ recommended / 推荐 Python 3.9+

Install dependencies / 安装依赖：

```bash
pip install -r requirements.txt
```

---

## Quick Start (GUI) / 快速开始（GUI）

Run the GUI / 运行 GUI：

```bash
flet run ui_app.py
```

Or / 或者：

```bash
python ui_app.py
```

In the GUI:

1. Go to **Settings / 设置** and fill `API Key` (and `API Base URL` if needed)
2. Go to **Workflow / 文件整理（整理流程）**
3. Click **选择目录** → **分析目录**
4. Stage 1: **阶段1：生成目录** → (optionally edit folder list) → **阶段1：创建文件夹**
5. Stage 2: **阶段2：批量移动**

建议：第一次对重要目录操作前，先备份或在测试目录试跑。

---

## Configuration / 配置

### Environment Variables / 环境变量

- `AUTOSNIFFER_API_KEY` (or `DASHSCOPE_API_KEY`)
- `AUTOSNIFFER_API_BASE_URL`
	- Default: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- `AUTOSNIFFER_MODEL_STAGE1` / `AUTOSNIFFER_MODEL_STAGE2`
- `AUTOSNIFFER_MODEL_NAME` (fallback model name)
- `AUTOSNIFFER_STAGE2_BATCH_SIZE` (CLI only; GUI uses the field) / 仅 CLI 使用

### Model Suggestions / 模型建议

- Stage 1 / 阶段1：更偏“规划”与“稳定输出 JSON”
- Stage 2 / 阶段2：更偏“批量分类”与“严格受控输出”

---

## Undo (Best-effort) / 撤销（尽量还原）

After Stage 2 finishes, AutoSniffer writes a journal:

- Folder: `.autosniffer_history/`
- File: `<run_id>.json` (e.g. `20251220_153012.json`)

Click **撤销上一次** to restore files based on the latest journal.

### Conflict Handling / 冲突处理

If a file already exists at the restore target location, AutoSniffer will **rename** the restoring file to keep both copies (suffix like `__undo_conflict`, plus an index if needed).

### Limitations / 注意事项

- Undo is “best-effort”: if files were edited/renamed/moved manually after the run, some items may be skipped or fail.
- Only files recorded as successfully moved (`status = moved`) are reversed.
- Stage 1 folders created by the run will be removed only if they are still empty.

---

## CLI Usage / 命令行用法

The CLI (`main.py`) is mainly a demo and uses `DEFAULT_ROOT_PATH` from `src/config.py`.

```bash
python main.py
```

For most users, the GUI is recommended.

---

## Text Extraction Utility / 文本提取工具

`extract.py` can extract text from common document formats.

Examples / 示例：

```bash
# single file
python extract.py path\to\document.pdf

# extract all supported files under a directory
python extract.py --dir path\to\folder

# batch mode
python extract.py --batch a.docx b.pdf c.pptx
```

Outputs are saved under `extracted_texts/` by default for `--dir` mode.

---

## Troubleshooting / 常见问题

### API Key missing / 未填写 API Key

- Fill it in GUI Settings tab, or set `AUTOSNIFFER_API_KEY` / `DASHSCOPE_API_KEY`.

### Model returns invalid JSON / 模型输出不符合 JSON

- Try a more stable model.
- Reduce batch size.

### Some files not moved / 部分文件未移动

- Check file permissions / 文件权限
- Check if file is in use / 文件是否被占用
- See the journal and undo report in `.autosniffer_history/`

---

## Disclaimer / 免责声明

This tool performs real file operations. AI classification is heuristic and may be wrong. Always test on a copy or use Undo immediately if needed.

本工具会执行真实的文件移动操作，模型分类可能出错。请先在副本/测试目录运行，必要时立即使用“撤销上一次”。
