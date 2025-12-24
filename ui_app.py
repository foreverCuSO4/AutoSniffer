import threading
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import flet as ft

from src.workflow import OrganizerWorkflow
from src.ai_service import AIService
from src import config


def main(page: ft.Page):
    page.title = "AutoSniffer - 智能文件整理"
    page.window_width = 1100
    page.window_height = 740
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 16

    workflow: Optional[OrganizerWorkflow] = None
    workflow_key: str = ""
    workflow_base_url: str = ""
    workflow_stage1_model: str = ""
    workflow_stage2_model: str = ""
    structure_obj: Optional[Dict[str, Any]] = None
    directory_json_text: str = ""
    folders: List[str] = []
    files: List[Dict[str, Any]] = []
    stop_event: Optional[threading.Event] = None
    last_created_folders: List[str] = []

    ambiguous_files: List[Dict[str, Any]] = []
    rename_preview_items: List[Dict[str, Any]] = []

    is_busy_flag: bool = False

    def log(message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        logs.controls.append(ft.Text(f"[{ts}] {message}", selectable=True))
        page.update()

    def _ui_call(fn):
        try:
            call_from_thread = getattr(page, "call_from_thread", None)
            if callable(call_from_thread):
                call_from_thread(fn)
            else:
                fn()
        except Exception:
            # If UI dispatch fails for any reason, fall back silently.
            try:
                fn()
            except Exception:
                pass

    def show_error(message: str, title: str = "发生错误"):
        msg = (message or "").strip() or "未知错误"

        def _open():
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(title),
                content=ft.Text(msg, selectable=True),
                actions=[ft.FilledButton("知道了", on_click=lambda e: page.close(dialog))],
            )
            page.open(dialog)

        _ui_call(_open)

    def show_dialog(message: str, title: str = "提示"):
        msg = (message or "").strip() or ""

        def _open():
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(title),
                content=ft.Text(msg, selectable=True),
                actions=[ft.FilledButton("知道了", on_click=lambda e: page.close(dialog))],
            )
            page.open(dialog)

        _ui_call(_open)

    def show_info(message: str):
        msg = (message or "").strip()
        if not msg:
            return

        def _open():
            page.snack_bar = ft.SnackBar(content=ft.Text(msg), open=True)
            page.update()

        _ui_call(_open)

    def require_api_key():
        api_key = (api_key_field.value or "").strip()
        if not api_key:
            raise ValueError("API Key 为空：请在“设置”页中填写后再执行 AI 阶段。")

    def _api_key_present() -> bool:
        return bool((api_key_field.value or "").strip())

    def _root_path_for_workflow() -> str:
        return (root_path_field.value or "").strip()

    def _root_path_for_rename() -> str:
        return (root_path_field_rename.value or root_path_field.value or "").strip()

    def _has_scan_results() -> bool:
        return bool(structure_obj is not None and (directory_json_text or "").strip())

    def _folders_exist_on_disk(root_path: str, folder_names: List[str]) -> bool:
        if not root_path or not folder_names:
            return False
        for name in folder_names:
            if not os.path.isdir(os.path.join(root_path, name)):
                return False
        return True

    def refresh_action_states():
        """Enable/disable buttons based on user progress to reduce confusion."""
        busy = bool(is_busy_flag)

        workflow_root = _root_path_for_workflow()
        rename_root = _root_path_for_rename()
        scanned = _has_scan_results()
        api_ok = _api_key_present()
        current_folders = _folders_from_field()
        folders_ok = bool(current_folders)
        folders_exist = _folders_exist_on_disk(workflow_root, current_folders)

        # --- File organizing tab (4 main buttons) ---
        scan_btn.disabled = busy or (not workflow_root)
        scan_btn.tooltip = "请先选择目标目录" if (not workflow_root) else "分析目标目录结构"

        plan_folders_btn.disabled = busy or (not scanned) or (not api_ok)
        if not scanned:
            plan_folders_btn.tooltip = "请先点击“分析目录”"
        elif not api_ok:
            plan_folders_btn.tooltip = "请先在“设置”页填写 API Key"
        else:
            plan_folders_btn.tooltip = "根据目录结构生成分类文件夹列表"

        create_folders_btn.disabled = busy or (not scanned) or (not folders_ok) or (not workflow_root)
        if not scanned:
            create_folders_btn.tooltip = "请先点击“分析目录”"
        elif not folders_ok:
            create_folders_btn.tooltip = "请先生成/填写分类文件夹列表"
        else:
            create_folders_btn.tooltip = "在目标目录中创建分类文件夹（不移动文件）"

        stage2_ready = scanned and api_ok and folders_ok and bool(workflow_root) and folders_exist
        start_stage2_btn.disabled = busy or (not stage2_ready)
        if not scanned:
            start_stage2_btn.tooltip = "请先点击“分析目录”"
        elif not api_ok:
            start_stage2_btn.tooltip = "请先在“设置”页填写 API Key"
        elif not folders_ok:
            start_stage2_btn.tooltip = "请先生成/填写分类文件夹列表"
        elif not folders_exist:
            start_stage2_btn.tooltip = "请先点击“创建文件夹”，或确保目标分类文件夹已存在"
        else:
            start_stage2_btn.tooltip = "按批调用 AI 并实际移动文件"

        # --- Rename tab actions ---
        scan_btn_rename.disabled = busy or (not rename_root)
        scan_btn_rename.tooltip = "请先选择目标目录" if (not rename_root) else "分析目标目录结构"

        detect_ambiguous_btn.disabled = busy or (not scanned) or (not api_ok)
        if not scanned:
            detect_ambiguous_btn.tooltip = "请先点击“分析目录”"
        elif not api_ok:
            detect_ambiguous_btn.tooltip = "请先在“设置”页填写 API Key"
        else:
            detect_ambiguous_btn.tooltip = "让 AI 找出命名模糊的文件"

        build_rename_preview_btn.disabled = busy or (not scanned) or (not api_ok) or (not ambiguous_files)
        if not scanned:
            build_rename_preview_btn.tooltip = "请先点击“分析目录”"
        elif not api_ok:
            build_rename_preview_btn.tooltip = "请先在“设置”页填写 API Key"
        elif not ambiguous_files:
            build_rename_preview_btn.tooltip = "请先点击“识别命名模糊文件”"
        else:
            build_rename_preview_btn.tooltip = "提取内容并生成新名前缀预览"

        apply_rename_btn.disabled = busy or (not rename_preview_items)
        apply_rename_btn.tooltip = "请先生成重命名预览" if (not rename_preview_items) else "执行重命名（会实际修改文件名）"

        stop_btn.disabled = not busy
        page.update()

    def set_busy(is_busy: bool):
        nonlocal is_busy_flag
        is_busy_flag = bool(is_busy)

        pick_dir_btn.disabled = is_busy_flag
        pick_dir_btn_rename.disabled = is_busy_flag

        timeout_field.disabled = is_busy_flag
        folders_field.disabled = is_busy_flag
        api_key_field.disabled = is_busy_flag
        base_url_field.disabled = is_busy_flag
        stage1_model_field.disabled = is_busy_flag
        stage2_model_field.disabled = is_busy_flag
        image_model_field.disabled = is_busy_flag
        batch_size_field.disabled = is_busy_flag
        progress.visible = is_busy_flag
        # Indeterminate header progress bar + ring = a small, elegant busy animation.
        progress.value = None if is_busy_flag else 0
        busy_ring.visible = is_busy_flag

        refresh_action_states()

    def ensure_workflow() -> OrganizerWorkflow:
        nonlocal workflow
        nonlocal workflow_key, workflow_base_url, workflow_stage1_model, workflow_stage2_model

        api_key = (api_key_field.value or "").strip()
        base_url = (base_url_field.value or "").strip()
        stage1_model = (stage1_model_field.value or "").strip()
        stage2_model = (stage2_model_field.value or "").strip()

        if (
            workflow is None
            or workflow_key != api_key
            or workflow_base_url != base_url
            or workflow_stage1_model != stage1_model
            or workflow_stage2_model != stage2_model
        ):
            ai = AIService(api_key=api_key, base_url=base_url)
            workflow = OrganizerWorkflow(ai_service=ai)
            workflow_key = api_key
            workflow_base_url = base_url
            workflow_stage1_model = stage1_model
            workflow_stage2_model = stage2_model
        return workflow

    def new_stop_event() -> threading.Event:
        nonlocal stop_event
        stop_event = threading.Event()
        return stop_event

    def should_stop() -> bool:
        return bool(stop_event and stop_event.is_set())

    def on_stop_click(_):
        if stop_event:
            stop_event.set()
            log("已请求停止：将尽快在安全点中断")
        stop_btn.disabled = True
        page.update()

    def _set_root_path(path: str):
        root_path_field.value = path
        root_path_field_rename.value = path
        refresh_action_states()

    def on_pick_directory_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        _set_root_path(e.path)
        log(f"已选择目录: {e.path}")

    picker = ft.FilePicker(on_result=on_pick_directory_result)
    page.overlay.append(picker)

    root_path_field = ft.TextField(
        label="目标目录",
        hint_text="请选择要整理的文件夹",
        read_only=True,
        expand=True,
    )

    root_path_field_rename = ft.TextField(
        label="目标目录",
        hint_text="请选择要处理的文件夹",
        read_only=True,
        expand=True,
    )

    pick_dir_btn = ft.ElevatedButton(
        "选择目录",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: picker.get_directory_path(dialog_title="选择要整理的目录"),
    )

    pick_dir_btn_rename = ft.ElevatedButton(
        "选择目录",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: picker.get_directory_path(dialog_title="选择要重命名的目录"),
    )

    structure_preview = ft.TextField(
        label="目录结构（JSON预览）",
        multiline=True,
        min_lines=6,
        max_lines=8,
        read_only=True,
    )

    structure_preview_rename = ft.TextField(
        label="目录结构（JSON预览）",
        multiline=True,
        min_lines=6,
        max_lines=8,
        read_only=True,
    )

    folders_field = ft.TextField(
        label="阶段1：目标分类文件夹（每行一个，可编辑）",
        multiline=True,
        min_lines=8,
        max_lines=10,
        value="",
    )

    mkdir_script_preview = ft.TextField(
        label="将要执行的“创建文件夹”脚本预览",
        multiline=True,
        min_lines=6,
        max_lines=8,
        read_only=True,
        value="",
    )

    timeout_field = ft.TextField(
        label="执行超时（秒）",
        value="300",
        width=160,
        input_filter=ft.NumbersOnlyInputFilter(),
    )

    progress = ft.ProgressBar(visible=False)
    busy_ring = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=3)

    logs = ft.ListView(expand=True, spacing=6, auto_scroll=True)

    stage2_current = ft.TextField(
        label="阶段2：当前处理命令（只读）",
        read_only=True,
        value="",
    )

    stage2_progress = ft.ProgressBar(value=0)
    stage2_progress_text = ft.Text("等待开始")

    api_key_field = ft.TextField(
        label="API Key",
        hint_text="填入 AUTOSNIFFER_API_KEY",
        value=os.getenv("AUTOSNIFFER_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or "",
        password=True,
        can_reveal_password=True,
        expand=True,
    )

    base_url_field = ft.TextField(
        label="API Base URL",
        hint_text="可选：AUTOSNIFFER_API_BASE_URL（OpenAI 兼容接口）",
        value=getattr(config, "API_BASE_URL", "") or os.getenv("AUTOSNIFFER_API_BASE_URL") or "",
        expand=True,
    )

    stage1_model_field = ft.TextField(
        label="阶段1模型",
        value=getattr(config, "MODEL_NAME_STAGE1", "") or "qwen-flash",
        width=200,
    )

    stage2_model_field = ft.TextField(
        label="阶段2模型",
        value=getattr(config, "MODEL_NAME_STAGE2", "") or "qwen-flash",
        width=200,
    )

    image_model_field = ft.TextField(
        label="图片处理模型",
        value=getattr(config, "MODEL_NAME_IMAGE", "") or "qwen-vl-max",
        width=200,
    )

    batch_size_field = ft.TextField(
        label="阶段2批大小 n",
        value="5",
        width=160,
        input_filter=ft.NumbersOnlyInputFilter(),
    )

    organize_requirements_field = ft.TextField(
        label="个性化要求（可选）",
        hint_text="例如：优先按项目/客户分类；图片按拍摄地点；不要创建过多分类等",
        multiline=True,
        min_lines=2,
        max_lines=3,
        value="",
    )

    rename_requirements_field = ft.TextField(
        label="个性化要求（可选）",
        hint_text="例如：前缀用英文；尽量短；包含日期；避免敏感词等",
        multiline=True,
        min_lines=2,
        max_lines=3,
        value="",
    )

    def do_scan():
        nonlocal directory_json_text, structure_obj, files
        try:
            root_path = root_path_field.value or root_path_field_rename.value or ""
            wf = ensure_workflow()
            if should_stop():
                log("已停止")
                return
            log("开始扫描目录结构...")
            structure = wf.scan_directory(root_path)
            if should_stop():
                log("已停止")
                return
            structure_obj = structure
            directory_json_text = wf.format_structure_json(structure)
            structure_preview.value = directory_json_text
            structure_preview_rename.value = directory_json_text
            files = wf.flatten_files(structure)
            stage2_progress.value = 0
            stage2_progress_text.value = f"待处理文件数：{len(files)}"
            log("目录结构分析完成")
        except Exception as ex:
            log(f"扫描失败: {ex}")
            show_error(str(ex), title="扫描失败")
        finally:
            set_busy(False)

    def on_scan_click(_):
        if not (root_path_field.value or root_path_field_rename.value):
            log("请先选择目录")
            return
        set_busy(True)
        new_stop_event()
        threading.Thread(target=do_scan, daemon=True).start()

    def on_scan_click_rename(_):
        on_scan_click(_)

    def _folders_from_field() -> List[str]:
        lines = (folders_field.value or "").splitlines()
        cleaned: List[str] = []
        seen = set()
        for line in lines:
            name = line.strip().strip("\\/")
            if not name or name in seen:
                continue
            seen.add(name)
            cleaned.append(name)
        if cleaned and "其他" not in cleaned:
            cleaned.append("其他")
        return cleaned

    def _update_mkdir_preview():
        wf = ensure_workflow()
        current_folders = _folders_from_field()
        mkdir_script_preview.value = wf.build_mkdir_script(current_folders) if current_folders else ""
        refresh_action_states()

    def do_plan_folders():
        nonlocal folders
        try:
            wf = ensure_workflow()
            if not directory_json_text.strip():
                raise ValueError("请先点击“分析目录”")
            require_api_key()
            if should_stop():
                log("已停止")
                return
            log("阶段1：请求 AI 生成目标分类目录...")
            folders = wf.stage1_plan_folders(
                directory_json_text,
                model=(stage1_model_field.value or "").strip(),
                user_requirements=(organize_requirements_field.value or "").strip() or None,
            )
            if should_stop():
                log("已停止")
                return
            folders_field.value = "\n".join(folders)
            _update_mkdir_preview()
            log(f"阶段1：已生成 {len(folders)} 个目录")
        except Exception as ex:
            log(f"阶段1失败: {ex}")
            show_error(str(ex), title="阶段1失败")
        finally:
            set_busy(False)

    def on_plan_folders_click(_):
        set_busy(True)
        new_stop_event()
        threading.Thread(target=do_plan_folders, daemon=True).start()

    def do_create_folders():
        nonlocal last_created_folders
        try:
            wf = ensure_workflow()
            root_path = root_path_field.value or ""
            current_folders = _folders_from_field()
            if not current_folders:
                raise ValueError("目录列表为空，请先生成或手动填写")
            if should_stop():
                log("已停止")
                return
            log("阶段1：开始创建文件夹...")
            # Use Python mkdir so we can precisely record what was newly created for Undo.
            created = wf.create_folders_python(root_path, current_folders)
            last_created_folders = created
            script = wf.build_mkdir_script(current_folders)
            mkdir_script_preview.value = script
            if should_stop():
                log("已停止")
                return
            log(f"阶段1：创建完成（新增 {len(created)} 个文件夹）")
        except Exception as ex:
            log(f"阶段1执行失败: {ex}")
            show_error(str(ex), title="创建文件夹失败")
        finally:
            set_busy(False)

    def on_create_folders_click(_):
        if not root_path_field.value:
            log("请先选择目录")
            return

        def close_dialog(e):
            confirm_dialog.open = False
            page.update()

        def run_after_confirm(e):
            confirm_dialog.open = False
            page.update()
            set_busy(True)
            new_stop_event()
            threading.Thread(target=do_create_folders, daemon=True).start()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认创建文件夹"),
            content=ft.Text("即将在目标目录创建分类文件夹（不会移动文件）。"),
            actions=[
                ft.TextButton("取消", on_click=close_dialog),
                ft.FilledButton("继续", on_click=run_after_confirm),
            ],
        )
        page.open(confirm_dialog)

    def do_stage2_process():
        try:
            nonlocal last_created_folders
            wf = ensure_workflow()
            root_path = root_path_field.value or ""
            current_folders = _folders_from_field()
            if not current_folders:
                raise ValueError("请先完成阶段1并确认目录列表")
            if structure_obj is None:
                raise ValueError("请先分析目录")
            require_api_key()
            local_files = wf.flatten_files(structure_obj)
            if not local_files:
                log("未找到可处理的文件")
                show_info("未找到可处理的文件")
                return

            batch_size = int(batch_size_field.value or "5")
            if batch_size <= 0:
                batch_size = 1

            total = len(local_files)
            done = 0
            stage2_progress.value = 0
            stage2_progress_text.value = f"准备开始：0/{total}"
            page.update()

            run_id = wf._now_id()
            journal_moves: List[Dict[str, Any]] = []
            log(f"阶段2：开始批处理归类并移动（共 {total} 个文件，每批 {batch_size} 个）...")
            for batch in wf.chunk_list(local_files, batch_size):
                if should_stop():
                    log("阶段2：已停止")
                    return

                # AI decide destinations for this batch
                stage2_current.value = f"AI 批处理规划中（{done}/{total}）"
                stage2_progress_text.value = f"AI 规划中：{done}/{total}"
                page.update()

                destinations = wf.stage2_choose_destinations_batch(
                    batch,
                    current_folders,
                    model=(stage2_model_field.value or "").strip(),
                    user_requirements=(organize_requirements_field.value or "").strip() or None,
                )

                if should_stop():
                    log("阶段2：已停止")
                    return

                stage2_current.value = f"执行批处理：移动 {len(batch)} 个文件"
                stage2_progress_text.value = f"执行中：{done}/{total}"
                page.update()

                # Use Python move for per-file journaling and conflict handling.
                move_records = wf.move_files_python(root_path, batch, destinations, on_conflict="rename")
                journal_moves.extend(move_records)

                # Count progress by attempted items
                done = min(total, done + len(batch))
                stage2_progress.value = done / total if total else 0
                stage2_progress_text.value = f"已处理：{done}/{total}"
                page.update()

            # Cleanup empty folders and persist journal for Undo.
            deleted_empty_folders = wf.cleanup_empty_folders(root_path)
            if deleted_empty_folders:
                log(f"阶段2：已清理空文件夹 {len(deleted_empty_folders)} 个")

            journal = {
                "id": run_id,
                "created_folders": list(last_created_folders or []),
                "moves": journal_moves,
                "deleted_empty_folders": deleted_empty_folders,
            }
            journal_path = wf.write_journal(root_path, journal)
            log(f"阶段2：已写入历史记录：{journal_path}")

            log("阶段2：全部处理完成")
            show_info("阶段2：全部处理完成")
        except Exception as ex:
            log(f"阶段2失败: {ex}")
            show_error(str(ex), title="阶段2失败")
        finally:
            stage2_current.value = ""
            stage2_progress_text.value = stage2_progress_text.value or ""
            set_busy(False)

    def on_start_stage2_click(_):
        if not root_path_field.value:
            log("请先选择目录")
            return
        if not (folders_field.value or "").strip():
            log("请先完成阶段1（生成目录列表）")
            return
        if structure_obj is None:
            log("请先分析目录")
            return

        def close_dialog(e):
            confirm_dialog.open = False
            page.update()

        def run_after_confirm(e):
            confirm_dialog.open = False
            page.update()
            set_busy(True)
            new_stop_event()
            threading.Thread(target=do_stage2_process, daemon=True).start()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认开始阶段2"),
            content=ft.Text("即将按批调用 AI 并执行 move 命令，会实际移动文件。"),
            actions=[
                ft.TextButton("取消", on_click=close_dialog),
                ft.FilledButton("开始", on_click=run_after_confirm),
            ],
        )
        page.open(confirm_dialog)

    scan_btn = ft.FilledButton("分析目录", icon=ft.Icons.SEARCH, on_click=on_scan_click)
    scan_btn_rename = ft.FilledButton("分析目录", icon=ft.Icons.SEARCH, on_click=on_scan_click_rename)
    plan_folders_btn = ft.FilledButton("生成目录", icon=ft.Icons.AUTO_AWESOME, on_click=on_plan_folders_click)
    create_folders_btn = ft.FilledButton("创建文件夹", icon=ft.Icons.CREATE_NEW_FOLDER, on_click=on_create_folders_click)
    start_stage2_btn = ft.FilledButton("批量移动", icon=ft.Icons.DRIVE_FILE_MOVE, on_click=on_start_stage2_click)

    # --- Smart Rename UI actions ---

    ambiguous_list = ft.TextField(
        label="AI 判定为“命名模糊”的文件（relative_path）",
        multiline=True,
        min_lines=6,
        max_lines=10,
        read_only=True,
        value="",
    )

    rename_preview = ft.TextField(
        label="重命名预览（new_prefix_original）",
        multiline=True,
        min_lines=6,
        max_lines=12,
        read_only=True,
        value="",
    )

    rename_progress = ft.ProgressBar(value=0)
    rename_progress_text = ft.Text("等待开始")

    def do_detect_ambiguous():
        nonlocal ambiguous_files
        try:
            wf = ensure_workflow()
            if not directory_json_text.strip():
                raise ValueError("请先点击“分析目录”")
            require_api_key()
            if should_stop():
                log("已停止")
                return
            log("智能重命名：请求 AI 判断命名模糊的文件...")
            items = wf.rename_detect_ambiguous(
                directory_json_text,
                model=(stage2_model_field.value or "").strip(),
                user_requirements=(rename_requirements_field.value or "").strip() or None,
            )
            ambiguous_files = items
            lines: List[str] = []
            for it in items:
                rp = str(it.get("relative_path") or "")
                reason = str(it.get("reason") or "")
                if reason:
                    lines.append(f"{rp}  # {reason}")
                else:
                    lines.append(rp)
            ambiguous_list.value = "\n".join(lines)
            log(f"智能重命名：已识别 {len(items)} 个命名模糊文件")
            if not items:
                show_info("未发现需要智能重命名的文件")
        except Exception as ex:
            log(f"智能重命名：识别失败: {ex}")
            show_error(str(ex), title="智能重命名：识别失败")
        finally:
            set_busy(False)

    def on_detect_ambiguous_click(_):
        set_busy(True)
        new_stop_event()
        threading.Thread(target=do_detect_ambiguous, daemon=True).start()

    def do_build_rename_preview():
        nonlocal rename_preview_items
        try:
            wf = ensure_workflow()
            root_path = root_path_field_rename.value or root_path_field.value or ""
            if not root_path:
                raise ValueError("请先选择目录")
            if structure_obj is None or not directory_json_text.strip():
                raise ValueError("请先分析目录")
            require_api_key()
            if not ambiguous_files:
                raise ValueError("请先点击“识别命名模糊文件”")

            # Map relative_path -> file_item
            all_files = wf.flatten_files(structure_obj)
            by_rel = {str(f.get("relative_path") or ""): f for f in all_files}

            targets: List[Dict[str, Any]] = []
            for it in ambiguous_files:
                rp = str(it.get("relative_path") or "")
                fi = by_rel.get(rp)
                if fi:
                    targets.append(fi)

            if not targets:
                raise ValueError("未找到可处理的目标文件（relative_path 不匹配）")

            rename_preview_items = []
            rename_progress.value = 0
            rename_progress_text.value = f"准备开始：0/{len(targets)}"
            page.update()

            lines: List[str] = []
            total = len(targets)
            done = 0
            log(f"智能重命名：开始提取内容并生成新名前缀（共 {total} 个文件）...")
            for fi in targets:
                if should_stop():
                    log("智能重命名：已停止")
                    return

                rp = str(fi.get("relative_path") or "")
                name = str(fi.get("name") or "")
                ext = str(fi.get("extension") or "").lower()
                rename_progress_text.value = f"处理中：{done}/{total}"
                page.update()

                # Check if it's an image file
                image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
                is_image = ext in image_extensions

                if is_image:
                    # Use multimodal AI for image files
                    try:
                        log(f"智能重命名：使用多模态AI识别图片 {name}")
                        prefix = wf.rename_suggest_prefix_for_image(
                            root_path,
                            fi,
                            model=(image_model_field.value or stage2_model_field.value or "").strip(),
                            user_requirements=(rename_requirements_field.value or "").strip() or None,
                        )
                        if not prefix:
                            prefix = "未识别"
                    except Exception as img_ex:
                        err = str(img_ex)
                        log(f"图片识别失败 {name}: {err}")
                        # Keep prefix short, but show reason in preview line for debugging.
                        prefix = "识别失败"
                else:
                    # Use text extraction for non-image files
                    snippet = wf.rename_extract_content(root_path, rp)
                    if not snippet.strip():
                        prefix = "内容为空"
                    else:
                        prefix = wf.rename_suggest_prefix(
                            fi,
                            snippet,
                            model=(stage2_model_field.value or "").strip(),
                            user_requirements=(rename_requirements_field.value or "").strip() or None,
                        )
                        if not prefix:
                            prefix = "未命名"

                new_name = f"{prefix}_{name}"
                if is_image and prefix == "识别失败":
                    reason = (str(img_ex) if 'img_ex' in locals() else '').strip()
                    if reason:
                        reason = reason.replace('\n', ' ')
                        if len(reason) > 120:
                            reason = reason[:120] + "..."
                        lines.append(f"{rp}  ->  {new_name}  # {reason}")
                    else:
                        lines.append(f"{rp}  ->  {new_name}")
                else:
                    lines.append(f"{rp}  ->  {new_name}")
                rename_preview_items.append({"relative_path": rp, "prefix": prefix, "old_name": name, "new_name": new_name})

                done += 1
                rename_progress.value = done / total if total else 0
                rename_progress_text.value = f"已生成预览：{done}/{total}"
                page.update()

            rename_preview.value = "\n".join(lines)
            log("智能重命名：预览生成完成")
            show_info("智能重命名：已生成重命名预览")
        except Exception as ex:
            log(f"智能重命名：预览失败: {ex}")
            show_error(str(ex), title="智能重命名：预览失败")
        finally:
            set_busy(False)

    def on_build_rename_preview_click(_):
        set_busy(True)
        new_stop_event()
        threading.Thread(target=do_build_rename_preview, daemon=True).start()

    def do_apply_rename():
        try:
            wf = ensure_workflow()
            root_path = root_path_field_rename.value or root_path_field.value or ""
            if not root_path:
                raise ValueError("请先选择目录")
            if not rename_preview_items:
                raise ValueError("请先生成重命名预览")

            total = len(rename_preview_items)
            done = 0
            ok = 0
            failed = 0
            conflict = 0
            rename_progress.value = 0
            rename_progress_text.value = f"准备开始：0/{total}"
            page.update()

            log(f"智能重命名：开始执行重命名（共 {total} 个文件）...")
            for it in rename_preview_items:
                if should_stop():
                    log("智能重命名：已停止")
                    return
                rp = str(it.get("relative_path") or "")
                prefix = str(it.get("prefix") or "")
                res = wf.rename_apply_prefix(root_path, rp, prefix)
                if res.get("status") == "renamed":
                    ok += 1
                    if res.get("conflict"):
                        conflict += 1
                elif res.get("status") == "failed":
                    failed += 1
                    logs.controls.append(ft.Text(f"[重命名失败] {rp}: {res.get('error')}", selectable=True, color=ft.Colors.RED))
                done += 1
                rename_progress.value = done / total if total else 0
                rename_progress_text.value = f"已处理：{done}/{total}"
                page.update()

            log(f"智能重命名：完成。成功 {ok}，失败 {failed}，冲突改名 {conflict}")
            show_info("智能重命名：执行完成（详情见日志）")
        except Exception as ex:
            log(f"智能重命名：执行失败: {ex}")
            show_error(str(ex), title="智能重命名：执行失败")
        finally:
            set_busy(False)

    def on_apply_rename_click(_):
        if not rename_preview_items:
            log("请先生成重命名预览")
            return

        def close_dialog(e):
            confirm_dialog.open = False
            page.update()

        def run_after_confirm(e):
            confirm_dialog.open = False
            page.update()
            set_busy(True)
            new_stop_event()
            threading.Thread(target=do_apply_rename, daemon=True).start()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认执行智能重命名"),
            content=ft.Text("将把 AI 生成的新名前缀添加到原文件名前（prefix_original）。会实际重命名文件。"),
            actions=[
                ft.TextButton("取消", on_click=close_dialog),
                ft.FilledButton("开始重命名", on_click=run_after_confirm),
            ],
        )
        page.open(confirm_dialog)

    detect_ambiguous_btn = ft.FilledButton("识别命名模糊文件", icon=ft.Icons.PSYCHOLOGY, on_click=on_detect_ambiguous_click)
    build_rename_preview_btn = ft.FilledButton("生成重命名预览", icon=ft.Icons.FIND_REPLACE, on_click=on_build_rename_preview_click)
    apply_rename_btn = ft.FilledButton("执行重命名", icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE, on_click=on_apply_rename_click)

    def do_undo_last():
        try:
            wf = ensure_workflow()
            root_path = root_path_field.value or ""
            if not root_path:
                raise ValueError("请先选择目录")
            if should_stop():
                log("已停止")
                return
            log("撤销：开始尝试还原到执行前状态...")
            report = wf.undo_last(root_path, on_conflict="rename")
            log(
                f"撤销完成：恢复 {report.get('restored', 0)} 个文件，冲突 {report.get('conflicts', 0)}，失败 {report.get('failed', 0)}"
            )
            if report.get("removed_empty_folders"):
                log(f"撤销：已删除空文件夹：{', '.join(report['removed_empty_folders'])}")
            log(f"撤销报告：{report.get('report_path')}")
            show_info("撤销完成（详情见日志）")
        except Exception as ex:
            log(f"撤销失败: {ex}")
            show_error(str(ex), title="撤销失败")
        finally:
            set_busy(False)

    def on_undo_click(_):
        if not root_path_field.value:
            log("请先选择目录")
            return

        def close_dialog(e):
            confirm_dialog.open = False
            page.update()

        def run_after_confirm(e):
            confirm_dialog.open = False
            page.update()
            set_busy(True)
            new_stop_event()
            threading.Thread(target=do_undo_last, daemon=True).start()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认撤销上一次"),
            content=ft.Text(
                "将根据 .autosniffer_history 中最近一次记录，尽量把已移动文件移回原位置。\n"
                "如遇同名冲突，会自动重命名保留两份。"
            ),
            actions=[
                ft.TextButton("取消", on_click=close_dialog),
                ft.FilledButton("撤销", on_click=run_after_confirm),
            ],
        )
        page.open(confirm_dialog)

    undo_btn = ft.OutlinedButton("撤销上一次", icon=ft.Icons.UNDO, on_click=on_undo_click, disabled=False)

    stop_btn = ft.OutlinedButton("停止", icon=ft.Icons.STOP_CIRCLE, on_click=on_stop_click, disabled=True)

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text("AutoSniffer", size=22, weight=ft.FontWeight.BOLD),
                ft.Text("智能文件整理", size=14, color=ft.Colors.GREY_700),
                ft.Container(expand=True),
                progress,
                busy_ring,
                undo_btn,
                stop_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.only(bottom=8),
    )

    top_controls = ft.Row(
        controls=[root_path_field, pick_dir_btn],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    actions_row = ft.Row(
        controls=[
            scan_btn,
            plan_folders_btn,
            create_folders_btn,
            start_stage2_btn,
        ],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def on_help_click(_):
        show_dialog(
            "使用流程：\n"
            "1) 在“文件整理”页选择目标目录并点击‘分析目录’\n"
            "2) 点击‘生成目录’，确认/编辑目录列表\n"
            "3) 点击‘创建文件夹’（只创建，不移动）\n"
            "4) 点击‘批量移动’（按批调用 AI 并实际移动文件）\n"
            "5) 需要中断可点右上角‘停止’\n\n"
            "配置说明：请在“设置”页填写 API Key、Base URL（可选）、模型、批大小与超时。",
            title="使用指引",
        )

    def on_folders_change(_):
        _update_mkdir_preview()

    def on_api_key_change(_):
        refresh_action_states()

    folders_field.on_change = on_folders_change
    api_key_field.on_change = on_api_key_change

    stage1_view = ft.Column(
        controls=[
            ft.Text("阶段1：规划分类目录（只创建文件夹）", weight=ft.FontWeight.BOLD),
            ft.Text(
                "提示：你可以在下方直接编辑目录列表（每行一个），再点击“阶段1：创建文件夹”。",
                size=12,
                color=ft.Colors.GREY_700,
            ),
            folders_field,
            mkdir_script_preview,
        ],
        spacing=10,
        expand=True,
    )

    stage2_view = ft.Column(
        controls=[
            ft.Text("阶段2：批量归类并移动（可视化进度）", weight=ft.FontWeight.BOLD),
            ft.Text(
                "提示：会按“阶段2批大小 n”分批请求 AI，然后每批生成一个脚本一次执行。需要中断可点右上角“停止”。",
                size=12,
                color=ft.Colors.GREY_700,
            ),
            stage2_current,
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("处理进度"),
                        stage2_progress,
                        stage2_progress_text,
                    ],
                    spacing=8,
                ),
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                padding=10,
            ),
        ],
        spacing=10,
        expand=True,
    )

    left_panel = ft.Column(
        controls=[
            ft.Text("步骤 1：选择目录并分析", weight=ft.FontWeight.BOLD),
            top_controls,
            actions_row,
            organize_requirements_field,
            structure_preview,
            ft.Container(
                content=stage2_view,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                padding=12,
                expand=True,
            ),
        ],
        expand=True,
        spacing=12,
    )

    right_panel = ft.Column(
        controls=[
            ft.Text("步骤 2：阶段化执行", weight=ft.FontWeight.BOLD),
            ft.Container(
                content=stage1_view,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                padding=12,
            ),
            ft.Text("运行日志", weight=ft.FontWeight.BOLD),
            ft.Container(
                content=logs,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                padding=10,
                expand=True,
            ),
        ],
        expand=True,
        spacing=12,
    )

    workflow_tab = ft.Tab(
        text="文件整理",
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("文件整理", size=18, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.Icons.HELP_OUTLINE,
                            tooltip="使用指引",
                            on_click=on_help_click,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(col={"sm": 12, "md": 6}, content=left_panel),
                        ft.Container(col={"sm": 12, "md": 6}, content=right_panel),
                    ],
                    spacing=16,
                    run_spacing=16,
                ),
            ],
            spacing=12,
            expand=True,
        ),
    )

    settings_tab = ft.Tab(
        text="设置",
        content=ft.Column(
            controls=[
                ft.Text("设置", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "在这里集中配置 API Key、接口地址与模型参数。修改后会在下次执行时生效。",
                    size=12,
                    color=ft.Colors.GREY_700,
                ),
                ft.Text("鉴权与接口", weight=ft.FontWeight.BOLD),
                api_key_field,
                base_url_field,
                ft.Text("模型与执行参数", weight=ft.FontWeight.BOLD),
                ft.Row(controls=[stage1_model_field, stage2_model_field, image_model_field], spacing=10, wrap=True),
                ft.Row(controls=[batch_size_field, timeout_field], spacing=10),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )

    # --- Smart Rename tab ---

    rename_top_controls = ft.Row(
        controls=[root_path_field_rename, pick_dir_btn_rename],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    rename_actions_row = ft.Row(
        controls=[scan_btn_rename, detect_ambiguous_btn, build_rename_preview_btn, apply_rename_btn],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
    )

    rename_tab = ft.Tab(
        text="智能重命名",
        content=ft.Column(
            controls=[
                ft.Text("智能重命名", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "流程：分析目录 → AI 识别命名模糊文件 → 提取内容 → AI 生成新名前缀 → 以 prefix_original 方式重命名。",
                    size=12,
                    color=ft.Colors.GREY_700,
                ),
                rename_top_controls,
                rename_actions_row,
                rename_requirements_field,
                structure_preview_rename,
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("进度"),
                            rename_progress,
                            rename_progress_text,
                        ],
                        spacing=8,
                    ),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    padding=10,
                ),
                ambiguous_list,
                rename_preview,
                ft.Text("运行日志（与整理流程共用）", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=logs,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    padding=10,
                    expand=True,
                ),
            ],
            spacing=12,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    page.add(
        header,
        ft.Tabs(
            selected_index=0,
            tabs=[workflow_tab, rename_tab, settings_tab],
            expand=True,
        ),
    )

    refresh_action_states()
    log("就绪：请选择要整理的目录")


if __name__ == "__main__":
    ft.app(target=main)
