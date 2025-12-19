
# AutoSniffer

[![English](https://img.shields.io/badge/Language-English-blue)](#english)
[![中文](https://img.shields.io/badge/语言-中文-brightgreen)](#中文)

---

## English

AutoSniffer is a **two-stage AI-powered file organizer** (OpenAI-compatible API, e.g. DashScope/Qwen) with a desktop GUI (Flet). It scans a folder, proposes categories, moves files in batches, and supports **Undo last run** (best-effort restore with conflict-safe renaming).

---

## Features

- Two-stage workflow
	- Stage 1: only plans folders, then creates folders
	- Stage 2: batch classification + move
- GUI (Flet) with progress + stop
- Best-effort Undo last run
	- Uses a journal under `.autosniffer_history/`
	- Conflict-safe renaming on restore
- Optional text extraction tool
	- Extract text from `pdf/docx/pptx/xlsx/txt/...` for inspection

---

## Project Structure

- `ui_app.py`: GUI entry (Flet)
- `src/workflow.py`: core workflow (scan/plan/move/undo)
- `src/ai_service.py`: AI calls (OpenAI SDK)
- `src/cmd_executor.py`: PowerShell runner (used by legacy CLI/batch scripts)
- `main.py`: CLI demo (two-stage batch)
- `extract.py`: text extraction utility

---

## Requirements

- Windows recommended
- Python 3.9+ recommended

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Quick Start (GUI)

Run the GUI:

```bash
flet run ui_app.py
```

Or:

```bash
python ui_app.py
```

In the GUI:

1. Go to **Settings / 设置** and fill `API Key` (and `API Base URL` if needed)
2. Go to **Workflow / 文件整理（整理流程）**
3. Click **选择目录** → **分析目录**
4. Stage 1: **阶段1：生成目录** → (optionally edit folder list) → **阶段1：创建文件夹**
5. Stage 2: **阶段2：批量移动**

Tip: for important folders, test on a copy first.

---

## Configuration

### Environment Variables

- `AUTOSNIFFER_API_KEY` (or `DASHSCOPE_API_KEY`)
- `AUTOSNIFFER_API_BASE_URL`
	- Default: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- `AUTOSNIFFER_MODEL_STAGE1` / `AUTOSNIFFER_MODEL_STAGE2`
- `AUTOSNIFFER_MODEL_NAME` (fallback model name)
- `AUTOSNIFFER_STAGE2_BATCH_SIZE` (CLI only; GUI uses the field)

### Model Suggestions

- Stage 1: better at planning + strict JSON output
- Stage 2: better at batch classification + strict JSON output

---

## Undo (Best-effort)

After Stage 2 finishes, AutoSniffer writes a journal:

- Folder: `.autosniffer_history/`
- File: `<run_id>.json` (e.g. `20251220_153012.json`)

Click **撤销上一次** to restore files based on the latest journal.

### Conflict Handling

If a file already exists at the restore target location, AutoSniffer will **rename** the restoring file to keep both copies (suffix like `__undo_conflict`, plus an index if needed).

### Limitations

- Undo is “best-effort”: if files were edited/renamed/moved manually after the run, some items may be skipped or fail.
- Only files recorded as successfully moved (`status = moved`) are reversed.
- Stage 1 folders created by the run will be removed only if they are still empty.

---

## CLI Usage

The CLI (`main.py`) is mainly a demo and uses `DEFAULT_ROOT_PATH` from `src/config.py`.

```bash
python main.py
```

For most users, the GUI is recommended.

---

## Text Extraction Utility

`extract.py` can extract text from common document formats.

Examples:

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

## Troubleshooting

### API Key missing

- Fill it in GUI Settings tab, or set `AUTOSNIFFER_API_KEY` / `DASHSCOPE_API_KEY`.

### Model returns invalid JSON

- Try a more stable model.
- Reduce batch size.

### Some files not moved

- Check file permissions / 文件权限
- Check if file is in use / 文件是否被占用
- See the journal and undo report in `.autosniffer_history/`

---

## Disclaimer

This tool performs real file operations. AI classification is heuristic and may be wrong. Always test on a copy or use Undo immediately if needed.

---

## 中文

AutoSniffer 是一个基于大模型（OpenAI 兼容接口，如阿里云 DashScope/Qwen）的**两阶段文件整理工具**，提供桌面 GUI（Flet）来扫描目录、生成分类目录、批量归类移动文件，并支持“撤销上一次整理”（尽量还原到执行前状态，遇到冲突会自动改名保留）。

---

## 功能

- 两阶段流程
	- 阶段1：仅规划分类目录并创建文件夹
	- 阶段2：按批调用模型归类并移动文件
- 图形界面（Flet）：进度展示、可停止
- “撤销上一次”（尽量还原）
	- 使用 `.autosniffer_history/` 日志
	- 冲突时自动改名保留两份
- 附带文本提取脚本
	- 支持从 `pdf/docx/pptx/xlsx/txt/...` 提取文本便于查看

---

## 项目结构

- `ui_app.py`：GUI 入口
- `src/workflow.py`：业务编排（扫描/规划/移动/撤销）
- `src/ai_service.py`：大模型调用封装
- `src/cmd_executor.py`：PowerShell 执行器（主要用于旧脚本/CLI）
- `main.py`：CLI 示例
- `extract.py`：文本提取工具

---

## 环境依赖

- 推荐 Windows（项目内的执行器与路径处理主要面向 Windows）
- 推荐 Python 3.9+

安装依赖：

```bash
pip install -r requirements.txt
```

---

## 快速开始（GUI）

运行 GUI：

```bash
flet run ui_app.py
```

或者：

```bash
python ui_app.py
```

GUI 内操作：

1. 打开 **设置**：填写 `API Key`（需要的话填写 `API Base URL`）
2. 打开 **文件整理（整理流程）**
3. 点击 **选择目录** → **分析目录**
4. 阶段1：**阶段1：生成目录** →（可编辑目录列表）→ **阶段1：创建文件夹**
5. 阶段2：**阶段2：批量移动**

建议：第一次对重要目录操作前，先备份或在测试目录试跑。

---

## 配置

### 环境变量

- `AUTOSNIFFER_API_KEY`（或 `DASHSCOPE_API_KEY`）
- `AUTOSNIFFER_API_BASE_URL`
	- 默认：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- `AUTOSNIFFER_MODEL_STAGE1` / `AUTOSNIFFER_MODEL_STAGE2`
- `AUTOSNIFFER_MODEL_NAME`（兜底模型名）
- `AUTOSNIFFER_STAGE2_BATCH_SIZE`（仅 CLI 使用；GUI 使用界面字段）

### 模型建议

- 阶段1：更偏“规划”与“稳定输出 JSON”
- 阶段2：更偏“批量分类”与“严格受控输出”

---

## 撤销（尽量还原）

阶段2完成后会写入历史记录：

- 目录：`.autosniffer_history/`
- 文件：`<run_id>.json`（例如 `20251220_153012.json`）

点击 **撤销上一次** 会基于最近一次记录尝试把已移动文件移回原位置。

### 冲突处理

如果原位置已存在同名文件，会自动重命名（例如添加 `__undo_conflict` 后缀并按需追加序号），以保留两份。

### 注意事项

- “撤销”是尽量还原：如果整理后文件被手动改名/移动/编辑，可能会跳过或失败。
- 仅会撤销日志中记录为成功移动（`status = moved`）的条目。
- 阶段1创建的文件夹仅在仍为空时才会自动删除。

---

## 命令行用法

CLI（`main.py`）主要用于演示，默认使用 `src/config.py` 中的 `DEFAULT_ROOT_PATH`。

```bash
python main.py
```

一般推荐直接使用 GUI。

---

## 文本提取工具

`extract.py` 支持从常见文档中提取文本。

示例：

```bash
# 单文件
python extract.py path\to\document.pdf

# 提取目录下所有支持的文件
python extract.py --dir path\to\folder

# 批量模式
python extract.py --batch a.docx b.pdf c.pptx
```

`--dir` 模式下默认输出到 `extracted_texts/`。

---

## 常见问题

### 未填写 API Key

- 在 GUI 的“设置”页填写，或设置环境变量 `AUTOSNIFFER_API_KEY` / `DASHSCOPE_API_KEY`。

### 模型输出不符合 JSON

- 换更稳定的模型。
- 调小批大小。

### 部分文件未移动

- 检查文件权限。
- 检查文件是否被占用。
- 查看 `.autosniffer_history/` 内的日志与撤销报告。

---

## 免责声明

本工具会执行真实的文件移动操作，模型分类可能出错。请先在副本/测试目录运行，必要时立即使用“撤销上一次”。
