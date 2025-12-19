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

    def set_busy(is_busy: bool):
        pick_dir_btn.disabled = is_busy
        scan_btn.disabled = is_busy
        plan_folders_btn.disabled = is_busy
        create_folders_btn.disabled = is_busy
        start_stage2_btn.disabled = is_busy
        stop_btn.disabled = not is_busy
        timeout_field.disabled = is_busy
        folders_field.disabled = is_busy
        api_key_field.disabled = is_busy
        base_url_field.disabled = is_busy
        stage1_model_field.disabled = is_busy
        stage2_model_field.disabled = is_busy
        batch_size_field.disabled = is_busy
        progress.visible = is_busy
        page.update()

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

    def on_pick_directory_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        root_path_field.value = e.path
        log(f"已选择目录: {e.path}")
        page.update()

    picker = ft.FilePicker(on_result=on_pick_directory_result)
    page.overlay.append(picker)

    root_path_field = ft.TextField(
        label="目标目录",
        hint_text="请选择要整理的文件夹",
        read_only=True,
        expand=True,
    )

    pick_dir_btn = ft.ElevatedButton(
        "选择目录",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: picker.get_directory_path(dialog_title="选择要整理的目录"),
    )

    structure_preview = ft.TextField(
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

    batch_size_field = ft.TextField(
        label="阶段2批大小 n",
        value="5",
        width=160,
        input_filter=ft.NumbersOnlyInputFilter(),
    )

    def do_scan():
        nonlocal directory_json_text, structure_obj, files
        try:
            root_path = root_path_field.value or ""
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
        if not root_path_field.value:
            log("请先选择目录")
            return
        set_busy(True)
        new_stop_event()
        threading.Thread(target=do_scan, daemon=True).start()

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
        page.update()

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
            folders = wf.stage1_plan_folders(directory_json_text, model=(stage1_model_field.value or "").strip())
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

            # Persist journal for Undo.
            journal = {
                "id": run_id,
                "created_folders": list(last_created_folders or []),
                "moves": journal_moves,
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
    plan_folders_btn = ft.FilledButton("阶段1：生成目录", icon=ft.Icons.AUTO_AWESOME, on_click=on_plan_folders_click)
    create_folders_btn = ft.FilledButton("阶段1：创建文件夹", icon=ft.Icons.CREATE_NEW_FOLDER, on_click=on_create_folders_click)
    start_stage2_btn = ft.FilledButton("阶段2：批量移动", icon=ft.Icons.DRIVE_FILE_MOVE, on_click=on_start_stage2_click)

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
            "2) 点击‘阶段1：生成目录’，确认/编辑目录列表\n"
            "3) 点击‘阶段1：创建文件夹’（只创建，不移动）\n"
            "4) 点击‘阶段2：批量移动’（按批调用 AI 并实际移动文件）\n"
            "5) 需要中断可点右上角‘停止’\n\n"
            "配置说明：请在“设置”页填写 API Key、Base URL（可选）、模型、批大小与超时。",
            title="使用指引",
        )

    def on_folders_change(_):
        _update_mkdir_preview()

    folders_field.on_change = on_folders_change

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
                ft.Row(controls=[stage1_model_field, stage2_model_field], spacing=10),
                ft.Row(controls=[batch_size_field, timeout_field], spacing=10),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )

    page.add(
        header,
        ft.Tabs(
            selected_index=0,
            tabs=[workflow_tab, settings_tab],
            expand=True,
        ),
    )

    log("就绪：请选择要整理的目录")


if __name__ == "__main__":
    ft.app(target=main)
