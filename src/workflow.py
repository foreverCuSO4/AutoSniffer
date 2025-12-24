import json
import os
import shutil
import base64
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from io import BytesIO

from PIL import Image, ImageOps

from extract import extract_text_from_file

from . import file_ops
from .ai_service import AIService
from . import cmd_executor
from . import config


@dataclass
class ExecutionResult:
    return_code: int
    stdout: str
    stderr: str
    executed_file: str


class OrganizerWorkflow:
    """High-level workflow wrapper for the organizer.

    Keeps UI thin by centralizing:
    1) directory scanning
    2) AI planning
    3) script execution
    """

    def __init__(self, ai_service: Optional[AIService] = None):
        self._ai_service = ai_service or AIService()

    @staticmethod
    def validate_root_path(root_path: str) -> str:
        if not root_path:
            raise ValueError("root_path 不能为空")
        root_path = os.path.abspath(root_path)
        if not os.path.isdir(root_path):
            raise ValueError(f"不是有效目录: {root_path}")
        return root_path

    @staticmethod
    def scan_directory(root_path: str) -> Dict[str, Any]:
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        return file_ops.get_directory_structure(root_path)

    @staticmethod
    def format_structure_json(structure: Dict[str, Any]) -> str:
        return json.dumps(structure, indent=4, ensure_ascii=False)

    def plan_with_ai(self, directory_json: str) -> str:
        if not directory_json or not directory_json.strip():
            raise ValueError("directory_json 不能为空")
        cmd_instruction = self._ai_service.get_organization_plan(directory_json)
        if not cmd_instruction or not str(cmd_instruction).strip():
            raise RuntimeError("AI 未返回有效的整理指令")
        return str(cmd_instruction)

    # --- Two-stage pipeline ---

    def stage1_plan_folders(
        self,
        directory_json: str,
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> List[str]:
        return self._ai_service.get_folder_plan_stage1(directory_json, model=model, user_requirements=user_requirements)

    @staticmethod
    def build_mkdir_script(folders: List[str]) -> str:
        safe_folders = [f.strip().strip("\\/") for f in (folders or []) if (f or "").strip()]
        lines = [
            "@echo off",
            "cd /d \"%~dp0\"",
        ]
        for folder in safe_folders:
            # Quote folder names; suppress errors if exists
            lines.append(f'mkdir "{folder}" 2>nul')
        return "\n".join(lines) + "\n"

    @staticmethod
    def flatten_files(structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        files: List[Dict[str, Any]] = []

        def walk(node: Dict[str, Any]):
            if not isinstance(node, dict):
                return
            if node.get("type") == "file":
                rel = str(node.get("relative_path") or node.get("name") or "")
                name = str(node.get("name") or "")
                ext = os.path.splitext(name)[1].lower()
                files.append(
                    {
                        "name": name,
                        "relative_path": rel,
                        "extension": ext,
                        "metadata": node.get("metadata"),
                    }
                )
                return
            for child in node.get("children", []) or []:
                walk(child)

        walk(structure)
        # stable order
        files.sort(key=lambda x: str(x.get("relative_path") or ""))
        return files

    def stage2_choose_destination(
        self,
        file_item: Dict[str, Any],
        allowed_folders: List[str],
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> str:
        payload = {
            "allowed_folders": allowed_folders,
            "file": file_item,
        }
        dest = self._ai_service.choose_destination_stage2(payload, model=model, user_requirements=user_requirements)
        if dest not in allowed_folders:
            # enforce constraint
            return "其他" if "其他" in allowed_folders else allowed_folders[-1]
        return dest

    def stage2_choose_destinations_batch(
        self,
        file_items: List[Dict[str, Any]],
        allowed_folders: List[str],
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> List[str]:
        payload = {
            "allowed_folders": allowed_folders,
            "files": file_items,
        }
        assignments = self._ai_service.choose_destinations_batch_stage2(
            payload,
            model=model,
            user_requirements=user_requirements,
        )

        # Build a map by relative_path to be resilient to minor model mistakes
        by_path: Dict[str, str] = {}
        for a in assignments:
            rp = str(a.get("relative_path") or "")
            dst = str(a.get("destination") or "")
            if rp:
                by_path[rp] = dst

        destinations: List[str] = []
        for item in file_items:
            rp = str(item.get("relative_path") or "")
            dst = by_path.get(rp, "")
            if dst not in allowed_folders:
                dst = "其他" if "其他" in allowed_folders else allowed_folders[-1]
            destinations.append(dst)
        return destinations

    @staticmethod
    def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
        if chunk_size <= 0:
            chunk_size = 1
        return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]

    @staticmethod
    def build_move_command(file_relative_path: str, destination_folder: str) -> str:
        src = (file_relative_path or "").replace("/", "\\")
        dst = (destination_folder or "").strip().strip("\\/") + "\\"
        return f'move "{src}" "{dst}" >nul 2>nul'

    @staticmethod
    def build_batch_script(cmd_lines: List[str]) -> str:
        lines = [
            "@echo off",
            "cd /d \"%~dp0\"",
        ]
        for line in cmd_lines:
            if (line or "").strip():
                lines.append(line)
        return "\n".join(lines) + "\n"

    def stage2_process_files(
        self,
        root_path: str,
        structure: Dict[str, Any],
        allowed_folders: List[str],
        timeout_seconds: int = 300,
    ) -> Tuple[List[Dict[str, Any]], List[ExecutionResult]]:
        """Process files one-by-one: ask AI for destination then execute move.

        Returns:
          - per-file decisions list: {relative_path, destination, command}
          - execution results list aligned with decisions
        """
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        files = self.flatten_files(structure)
        decisions: List[Dict[str, Any]] = []
        results: List[ExecutionResult] = []
        for item in files:
            rel = str(item.get("relative_path") or "")
            dest = self.stage2_choose_destination(item, allowed_folders)
            cmd_line = self.build_move_command(rel, dest)
            decisions.append({"relative_path": rel, "destination": dest, "command": cmd_line})
            results.append(
                self.execute_script(cmd_line, working_dir=root_path, timeout_seconds=timeout_seconds)
            )
        return decisions, results

    def stage2_process_files_batched(
        self,
        root_path: str,
        structure: Dict[str, Any],
        allowed_folders: List[str],
        batch_size: int = 5,
        timeout_seconds: int = 300,
        model: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], List[ExecutionResult]]:
        """Stage2 batched: one AI call per N files, then execute ONE bat per batch containing N move commands."""
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        all_files = self.flatten_files(structure)
        decisions: List[Dict[str, Any]] = []
        batch_results: List[ExecutionResult] = []

        for batch in self.chunk_list(all_files, batch_size):
            destinations = self.stage2_choose_destinations_batch(batch, allowed_folders, model=model)
            cmd_lines: List[str] = []
            for item, dest in zip(batch, destinations):
                rel = str(item.get("relative_path") or "")
                cmd_line = self.build_move_command(rel, dest)
                decisions.append({"relative_path": rel, "destination": dest, "command": cmd_line})
                cmd_lines.append(cmd_line)

            script = self.build_batch_script(cmd_lines)
            batch_results.append(
                self.execute_script(script, working_dir=root_path, timeout_seconds=timeout_seconds)
            )

        return decisions, batch_results

    # --- Journaling + Undo (Python-based, conflict-safe) ---

    @staticmethod
    def _history_dir(root_path: str) -> str:
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        history = os.path.join(root_path, ".autosniffer_history")
        os.makedirs(history, exist_ok=True)
        return history

    @staticmethod
    def _now_id() -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def _unique_path(path: str, suffix: str) -> str:
        p = Path(path)
        parent = p.parent
        stem = p.stem
        ext = p.suffix
        candidate = parent / f"{stem}{suffix}{ext}"
        i = 1
        while candidate.exists():
            candidate = parent / f"{stem}{suffix}_{i}{ext}"
            i += 1
        return str(candidate)

    def create_folders_python(self, root_path: str, folders: List[str]) -> List[str]:
        """Create top-level folders and return the list that were newly created (relative names)."""
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        created: List[str] = []
        for f in folders or []:
            name = (f or "").strip().strip("\\/")
            if not name:
                continue
            abs_dir = os.path.join(root_path, name)
            if not os.path.exists(abs_dir):
                os.makedirs(abs_dir, exist_ok=True)
                created.append(name)
        return created

    def move_files_python(
        self,
        root_path: str,
        file_items: List[Dict[str, Any]],
        destinations: List[str],
        *,
        on_conflict: str = "rename",
    ) -> List[Dict[str, Any]]:
        """Move a batch of files with conflict handling.

        Returns per-file records:
          {src_rel, intended_dst_folder, intended_dst_rel, final_dst_rel, status, error, conflict}
        """
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        if len(file_items or []) != len(destinations or []):
            raise ValueError("file_items 与 destinations 长度不一致")

        results: List[Dict[str, Any]] = []
        for item, dst_folder in zip(file_items, destinations):
            src_rel = str(item.get("relative_path") or "").replace("/", "\\")
            name = str(item.get("name") or os.path.basename(src_rel) or "")
            safe_folder = (dst_folder or "").strip().strip("\\/")
            if not safe_folder:
                safe_folder = "其他"

            src_abs = os.path.join(root_path, src_rel)
            dst_dir_abs = os.path.join(root_path, safe_folder)
            os.makedirs(dst_dir_abs, exist_ok=True)
            intended_dst_abs = os.path.join(dst_dir_abs, name)

            record: Dict[str, Any] = {
                "src_rel": src_rel.replace("\\", "/"),
                "intended_dst_folder": safe_folder,
                "intended_dst_rel": os.path.join(safe_folder, name).replace("\\", "/"),
                "final_dst_rel": "",
                "status": "pending",
                "error": "",
                "conflict": False,
            }

            try:
                if not os.path.exists(src_abs):
                    record["status"] = "skipped"
                    record["error"] = "源文件不存在（可能已被移动/删除）"
                    results.append(record)
                    continue

                final_dst_abs = intended_dst_abs
                if os.path.exists(final_dst_abs):
                    record["conflict"] = True
                    if on_conflict == "rename":
                        final_dst_abs = self._unique_path(final_dst_abs, "__conflict")
                    else:
                        record["status"] = "failed"
                        record["error"] = "目标已存在"
                        results.append(record)
                        continue

                shutil.move(src_abs, final_dst_abs)
                record["status"] = "moved"
                record["final_dst_rel"] = os.path.relpath(final_dst_abs, root_path).replace("\\", "/")
            except Exception as e:
                record["status"] = "failed"
                record["error"] = str(e)
            results.append(record)

        return results

    def write_journal(self, root_path: str, journal: Dict[str, Any]) -> str:
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        history = self._history_dir(root_path)
        run_id = str(journal.get("id") or self._now_id())
        journal["id"] = run_id
        journal.setdefault("version", 1)
        journal.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
        journal.setdefault("root_path", root_path)
        path = os.path.join(history, f"{run_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(journal, f, ensure_ascii=False, indent=2)
        return path

    def cleanup_empty_folders(self, root_path: str, *, exclude: Optional[List[str]] = None) -> List[str]:
        """Delete empty folders under root_path and return removed folder relative paths.

        Notes:
        - Traverses bottom-up so nested empty folders are removed safely.
        - Always excludes `.autosniffer_history`.
        """
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        excluded = {".autosniffer_history"}
        for x in exclude or []:
            v = str(x or "").strip().strip("\\/")
            if v:
                excluded.add(v)

        removed: List[str] = []
        history_abs = os.path.join(root_path, ".autosniffer_history")

        for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
            # Never delete root itself
            if os.path.abspath(dirpath) == os.path.abspath(root_path):
                continue
            # Never touch history folder
            if os.path.abspath(dirpath).startswith(os.path.abspath(history_abs) + os.sep):
                continue

            rel = os.path.relpath(dirpath, root_path)
            rel_norm = rel.replace("\\", "/")
            top_name = rel.split(os.sep, 1)[0] if rel else ""
            if top_name in excluded or rel_norm in excluded:
                continue

            try:
                if os.path.isdir(dirpath) and not os.listdir(dirpath):
                    os.rmdir(dirpath)
                    removed.append(rel_norm)
            except Exception:
                # best-effort cleanup
                pass

        removed.sort(key=lambda s: (s.count("/"), len(s)))
        return removed

    # --- Smart Rename ---

    @staticmethod
    def _sanitize_filename_component(text: str, max_len: int = 32) -> str:
        """Sanitize a filename component for Windows and trim length."""
        s = (text or "").strip()
        if not s:
            return ""
        # remove Windows-illegal characters
        for ch in '<>:"/\\|?*':
            s = s.replace(ch, " ")
        s = " ".join(s.split())
        s = s.strip(" .\t\r\n")
        if not s:
            return ""
        if len(s) > max_len:
            s = s[:max_len].rstrip(" .")
        return s

    @staticmethod
    def _truncate_words(text: str, *, threshold_words: int = 100, max_words: int = 1000) -> str:
        words = (text or "").split()
        if len(words) > threshold_words:
            words = words[:max_words]
        return " ".join(words)

    def rename_detect_ambiguous(
        self,
        directory_json: str,
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        if not directory_json or not directory_json.strip():
            raise ValueError("directory_json 不能为空")
        return self._ai_service.detect_ambiguous_files_for_rename(directory_json, model=model, user_requirements=user_requirements)

    @staticmethod
    def _is_image_file(file_path: str) -> bool:
        """Check if file is an image based on extension."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
        ext = os.path.splitext(file_path)[1].lower()
        return ext in image_extensions

    @staticmethod
    def _resize_image_if_needed(image_path: str, max_width: int = 1920, max_height: int = 1080) -> Image.Image:
        """Resize image if larger than specified dimensions (1080p)."""
        with Image.open(image_path) as opened:
            img = ImageOps.exif_transpose(opened)
            img.load()

        width, height = img.size

        # Check if resize is needed
        if width <= max_width and height <= max_height:
            return img

        # Calculate new dimensions maintaining aspect ratio
        ratio = min(max_width / width, max_height / height)
        new_width = max(1, int(width * ratio))
        new_height = max(1, int(height * ratio))

        # Resize using high-quality filter
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return resized

    @staticmethod
    def _image_to_base64(img: Image.Image, format: str = "JPEG", *, quality: int = 75) -> str:
        """Convert PIL Image to base64 string."""
        buffered = BytesIO()
        # Convert RGBA to RGB for JPEG
        if img.mode == 'RGBA' and format.upper() == 'JPEG':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
            rgb_img.save(buffered, format=format, quality=quality, optimize=True)
        else:
            # Ensure JPEG is RGB
            if format.upper() == 'JPEG' and img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(buffered, format=format, quality=quality, optimize=True)
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return img_str

    def rename_suggest_prefix(
        self,
        file_item: Dict[str, Any],
        content_snippet: str,
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> str:
        payload = {
            "file": {
                "name": file_item.get("name"),
                "relative_path": file_item.get("relative_path"),
                "extension": file_item.get("extension"),
            },
            "content_snippet": content_snippet,
        }
        prefix = self._ai_service.suggest_prefix_for_rename(payload, model=model, user_requirements=user_requirements)
        return self._sanitize_filename_component(prefix, max_len=32)

    def rename_suggest_prefix_for_image(
        self,
        root_path: str,
        file_item: Dict[str, Any],
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> str:
        """Use multimodal AI to generate prefix for image files."""
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        rel = (file_item.get("relative_path") or "").replace("/", "\\")
        abs_path = os.path.join(root_path, rel)
        
        if not os.path.exists(abs_path):
            raise ValueError(f"图片文件不存在: {abs_path}")
        
        # Resize if needed and convert to base64
        img = self._resize_image_if_needed(abs_path, max_width=1920, max_height=1080)
        
        # Always encode to JPEG for maximum compatibility with OpenAI-style multimodal APIs.
        image_base64 = self._image_to_base64(img, format='JPEG', quality=75)
        
        # Call multimodal AI service (returns `description` preferred as filename prefix)
        model_to_use = (model or config.MODEL_NAME_IMAGE or "").strip() or None
        description = self._ai_service.describe_image_for_rename(
            image_base64,
            file_item,
            model=model_to_use,
            user_requirements=user_requirements,
        )
        return self._sanitize_filename_component(description, max_len=32)

    def rename_extract_content(self, root_path: str, file_relative_path: str) -> str:
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        rel = (file_relative_path or "").replace("/", "\\")
        abs_path = os.path.join(root_path, rel)
        text = extract_text_from_file(abs_path, max_length=50000) or ""
        return self._truncate_words(text, threshold_words=100, max_words=1000)

    def rename_apply_prefix(self, root_path: str, file_relative_path: str, prefix: str) -> Dict[str, Any]:
        """Rename a file by prepending '<prefix>_' to the original filename.

        Returns: {old_rel, new_rel, status, error, conflict}
        """
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        rel = (file_relative_path or "").replace("/", "\\")
        old_abs = os.path.join(root_path, rel)
        old_rel_norm = rel.replace("\\", "/")

        if not os.path.exists(old_abs):
            return {"old_rel": old_rel_norm, "new_rel": "", "status": "skipped", "error": "文件不存在", "conflict": False}

        base_dir = os.path.dirname(old_abs)
        old_name = os.path.basename(old_abs)
        safe_prefix = self._sanitize_filename_component(prefix, max_len=32)
        if not safe_prefix:
            return {"old_rel": old_rel_norm, "new_rel": "", "status": "skipped", "error": "prefix 为空", "conflict": False}

        new_name = f"{safe_prefix}_{old_name}"
        new_abs = os.path.join(base_dir, new_name)

        conflict = False
        if os.path.exists(new_abs):
            conflict = True
            # Add suffix to avoid overwriting
            stem, ext = os.path.splitext(new_name)
            i = 1
            while True:
                candidate = os.path.join(base_dir, f"{stem}__dup{i}{ext}")
                if not os.path.exists(candidate):
                    new_abs = candidate
                    break
                i += 1

        try:
            os.rename(old_abs, new_abs)
            new_rel = os.path.relpath(new_abs, root_path).replace("\\", "/")
            return {"old_rel": old_rel_norm, "new_rel": new_rel, "status": "renamed", "error": "", "conflict": conflict}
        except Exception as e:
            return {"old_rel": old_rel_norm, "new_rel": "", "status": "failed", "error": str(e), "conflict": conflict}

    def load_last_journal(self, root_path: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        history = self._history_dir(root_path)
        candidates = [p for p in Path(history).glob("*.json") if p.is_file()]
        if not candidates:
            return None
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        latest = candidates[0]
        with open(latest, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return str(latest), obj

    def undo_last(self, root_path: str, *, on_conflict: str = "rename") -> Dict[str, Any]:
        root_path = OrganizerWorkflow.validate_root_path(root_path)
        loaded = self.load_last_journal(root_path)
        if not loaded:
            raise ValueError("未找到可撤销的历史记录（.autosniffer_history 为空）")
        journal_path, journal = loaded

        moves = journal.get("moves") or []
        if not isinstance(moves, list) or not moves:
            raise ValueError("历史记录中没有 moves")

        undo_results: List[Dict[str, Any]] = []
        moved_count = 0
        restored_count = 0
        conflict_count = 0
        fail_count = 0

        # Reverse order is safer
        for m in reversed(moves):
            if not isinstance(m, dict):
                continue
            if m.get("status") != "moved":
                continue
            moved_count += 1

            src_rel = str(m.get("src_rel") or "")
            final_dst_rel = str(m.get("final_dst_rel") or m.get("intended_dst_rel") or "")
            if not src_rel or not final_dst_rel:
                continue

            current_abs = os.path.join(root_path, final_dst_rel.replace("/", "\\"))
            target_abs = os.path.join(root_path, src_rel.replace("/", "\\"))

            record = {
                "from": final_dst_rel,
                "to": src_rel,
                "final_to": "",
                "status": "pending",
                "error": "",
                "conflict": False,
            }

            try:
                if not os.path.exists(current_abs):
                    record["status"] = "skipped"
                    record["error"] = "待撤销文件不存在（可能已被改动）"
                    undo_results.append(record)
                    continue

                final_target_abs = target_abs
                if os.path.exists(final_target_abs):
                    record["conflict"] = True
                    conflict_count += 1
                    if on_conflict == "rename":
                        final_target_abs = self._unique_path(final_target_abs, "__undo_conflict")
                    else:
                        record["status"] = "failed"
                        record["error"] = "原位置已存在同名文件"
                        fail_count += 1
                        undo_results.append(record)
                        continue

                os.makedirs(os.path.dirname(final_target_abs), exist_ok=True)
                shutil.move(current_abs, final_target_abs)
                record["status"] = "restored"
                record["final_to"] = os.path.relpath(final_target_abs, root_path).replace("\\", "/")
                restored_count += 1
            except Exception as e:
                record["status"] = "failed"
                record["error"] = str(e)
                fail_count += 1
            undo_results.append(record)

        # Try remove empty folders that were created by this run
        removed_dirs: List[str] = []
        created_folders = journal.get("created_folders") or []
        if isinstance(created_folders, list):
            # deeper first (though these are top-level, keep safe)
            for folder in sorted([str(x) for x in created_folders if str(x).strip()], key=len, reverse=True):
                abs_dir = os.path.join(root_path, folder.strip().strip("\\/"))
                try:
                    if os.path.isdir(abs_dir) and not os.listdir(abs_dir):
                        os.rmdir(abs_dir)
                        removed_dirs.append(folder)
                except Exception:
                    pass

        # Re-create folders that were deleted during post-move cleanup
        restored_empty_dirs: List[str] = []
        deleted_empty_folders = journal.get("deleted_empty_folders") or []
        if isinstance(deleted_empty_folders, list):
            for rel in [str(x) for x in deleted_empty_folders if str(x).strip()]:
                rel_clean = rel.strip().strip("\\/")
                if not rel_clean or rel_clean == ".autosniffer_history":
                    continue
                abs_dir = os.path.join(root_path, rel_clean.replace("/", "\\"))
                try:
                    if os.path.exists(abs_dir) and not os.path.isdir(abs_dir):
                        continue
                    if not os.path.isdir(abs_dir):
                        os.makedirs(abs_dir, exist_ok=True)
                        restored_empty_dirs.append(rel_clean.replace("\\", "/"))
                except Exception:
                    pass

        # Write an undo report next to journal
        report = {
            "journal": os.path.basename(journal_path),
            "moved_in_journal": moved_count,
            "restored": restored_count,
            "conflicts": conflict_count,
            "failed": fail_count,
            "removed_empty_folders": removed_dirs,
            "restored_empty_folders": restored_empty_dirs,
            "undo_results": undo_results,
        }
        report_path = os.path.join(os.path.dirname(journal_path), f"{Path(journal_path).stem}__undo.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return {"report_path": report_path, **report}

    @staticmethod
    def execute_script(script_content: str, working_dir: str, timeout_seconds: int = 300) -> ExecutionResult:
        if not script_content or not script_content.strip():
            raise ValueError("script_content 不能为空")
        working_dir = OrganizerWorkflow.validate_root_path(working_dir)
        result = cmd_executor.execute_cmd_with_powershell(
            script_content,
            working_dir=working_dir,
            timeout=timeout_seconds,
        )
        return ExecutionResult(
            return_code=int(result.get("return_code") or -1),
            stdout=str(result.get("stdout") or ""),
            stderr=str(result.get("stderr") or ""),
            executed_file=str(result.get("executed_file") or ""),
        )
