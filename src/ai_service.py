import json
import base64
from typing import Any, Dict, List, Optional

from openai import OpenAI

from . import config

class AIService:
    USER_REQUIREMENTS_TOKEN = "<<USER_REQUIREMENTS>>"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self._api_key = (api_key or config.API_KEY or "").strip()
        self._base_url = (base_url or config.API_BASE_URL or "").strip()
        # Delay hard failure until first request so UI can be opened without config.
        self.client = OpenAI(
            api_key=self._api_key or "EMPTY",
            base_url=self._base_url,
        )

    @staticmethod
    def _normalize_user_requirements(text: Optional[str], *, max_len: int = 2000) -> str:
        s = (text or "").strip()
        if not s:
            return ""
        # Keep line breaks (users often enter bullet-style constraints), but normalize whitespace per-line.
        lines = [" ".join(line.split()) for line in s.splitlines()]
        lines = [line for line in lines if line]
        s = "\n".join(lines)
        if len(s) > max_len:
            s = s[:max_len].rstrip()
        return s

    def _apply_user_requirements(self, system_prompt: str, user_requirements: Optional[str]) -> str:
        prompt = system_prompt or ""
        req = self._normalize_user_requirements(user_requirements)
        # Keep the placeholder even if empty so templates remain stable.
        replacement = req if req else "（无）"
        if self.USER_REQUIREMENTS_TOKEN in prompt:
            return prompt.replace(self.USER_REQUIREMENTS_TOKEN, replacement)
        # Backward-compatible fallback if template doesn't include token.
        if req:
            return prompt + "\n\n个性化要求：\n" + req + "\n"
        return prompt

    def _chat(
        self,
        system_prompt: str,
        user_content: str,
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> str:
        if not self._api_key:
            raise ValueError("未配置 API Key。请在 UI 中填写，或设置环境变量 AUTOSNIFFER_API_KEY/DASHSCOPE_API_KEY。")
        model_to_use = (model or config.MODEL_NAME or "").strip()
        if not model_to_use:
            raise ValueError("未配置模型名称")
        req_norm = self._normalize_user_requirements(user_requirements)
        system_prompt = self._apply_user_requirements(system_prompt, user_requirements)
        try:
            messages = [{"role": "system", "content": system_prompt}]
            # Some models/providers under-weight system prompt details; also send requirements explicitly.
            if req_norm:
                messages.append({"role": "user", "content": f"个性化要求（请严格遵守）：\n{req_norm}"})
            messages.append({"role": "user", "content": user_content})
            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
            )
            return str(completion.choices[0].message.content or "")
        except Exception as e:
            print(f"AI Service Error: {e}")
            print("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")
            raise

    @staticmethod
    def _parse_json_object(text: str) -> Dict[str, Any]:
        text = (text or "").strip()
        # Best-effort: try to extract the first JSON object if model added extra text.
        if not text:
            raise ValueError("AI 返回为空")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start : end + 1])
            raise

    def get_folder_plan_stage1(
        self,
        directory_json: str,
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> List[str]:
        """Stage 1: return folder list to create."""
        raw = self._chat(
            config.SYSTEM_PROMPT_STAGE1_FOLDERS,
            directory_json,
            model=model or config.MODEL_NAME_STAGE1,
            user_requirements=user_requirements,
        )
        obj = self._parse_json_object(raw)
        folders = obj.get("folders")
        if not isinstance(folders, list) or not all(isinstance(x, str) and x.strip() for x in folders):
            raise ValueError("阶段1返回格式错误：缺少 folders 列表")
        # Normalize: strip and de-dup while preserving order
        seen = set()
        normalized: List[str] = []
        for f in folders:
            name = f.strip().strip("\\/")
            if not name or name in seen:
                continue
            seen.add(name)
            normalized.append(name)
        if "其他" not in normalized:
            normalized.append("其他")
        return normalized

    def choose_destination_stage2(
        self,
        payload: Dict[str, Any],
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> str:
        """Stage 2: choose destination folder for a single file."""
        raw = self._chat(
            config.SYSTEM_PROMPT_STAGE2_DESTINATION,
            json.dumps(payload, ensure_ascii=False),
            model=model or config.MODEL_NAME_STAGE2,
            user_requirements=user_requirements,
        )
        obj = self._parse_json_object(raw)
        dest = obj.get("destination")
        if not isinstance(dest, str) or not dest.strip():
            raise ValueError("阶段2返回格式错误：缺少 destination")
        return dest.strip()

    def choose_destinations_batch_stage2(
        self,
        payload: Dict[str, Any],
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Stage 2 (batch): returns list of {relative_path, destination} in the same order as input files."""
        raw = self._chat(
            config.SYSTEM_PROMPT_STAGE2_BATCH_DESTINATION,
            json.dumps(payload, ensure_ascii=False),
            model=model or config.MODEL_NAME_STAGE2,
            user_requirements=user_requirements,
        )
        obj = self._parse_json_object(raw)
        assignments = obj.get("assignments")
        if not isinstance(assignments, list):
            raise ValueError("阶段2批处理返回格式错误：缺少 assignments 列表")
        cleaned: List[Dict[str, str]] = []
        for a in assignments:
            if not isinstance(a, dict):
                cleaned.append({"relative_path": "", "destination": ""})
                continue
            rp = str(a.get("relative_path") or "")
            dst = str(a.get("destination") or "")
            cleaned.append({"relative_path": rp, "destination": dst})
        return cleaned

    # --- Smart Rename ---

    def detect_ambiguous_files_for_rename(
        self,
        directory_json: str,
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Given directory JSON, return a list of ambiguous files: [{relative_path, reason}]."""
        raw = self._chat(
            config.SYSTEM_PROMPT_RENAME_DETECT_AMBIGUOUS,
            directory_json,
            model=model or config.MODEL_NAME_STAGE2,
            user_requirements=user_requirements,
        )
        obj = self._parse_json_object(raw)
        items = obj.get("ambiguous_files")
        if not isinstance(items, list):
            raise ValueError("智能重命名返回格式错误：缺少 ambiguous_files 数组")

        cleaned: List[Dict[str, str]] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            rp = str(it.get("relative_path") or "").strip()
            reason = str(it.get("reason") or "").strip()
            if not rp:
                continue
            cleaned.append({"relative_path": rp, "reason": reason})
        return cleaned

    def suggest_prefix_for_rename(
        self,
        payload: Dict[str, Any],
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> str:
        """Given file info + extracted content snippet, return a short rename prefix string.

        Note: We prefer using `description` as the filename prefix, but keep a fallback
        to older responses that return `prefix`.
        """
        raw = self._chat(
            config.SYSTEM_PROMPT_RENAME_SUGGEST_PREFIX,
            json.dumps(payload, ensure_ascii=False),
            model=model or config.MODEL_NAME_STAGE2,
            user_requirements=user_requirements,
        )
        obj = self._parse_json_object(raw)
        description = obj.get("description")
        if isinstance(description, str) and description.strip():
            return description.strip()
        prefix = obj.get("prefix")
        if isinstance(prefix, str) and prefix.strip():
            return prefix.strip()
        raise ValueError("智能重命名返回格式错误：缺少 description")

    def describe_image_for_rename(
        self,
        image_base64: str,
        file_info: Dict[str, Any],
        model: Optional[str] = None,
        *,
        user_requirements: Optional[str] = None,
    ) -> str:
        """Use multimodal model to describe image content and return a filename prefix.

        Note: For image rename flow we prefer using `description` as the filename prefix.
        """
        if not self._api_key:
            raise ValueError("未配置 API Key。请在 UI 中填写，或设置环境变量 AUTOSNIFFER_API_KEY/DASHSCOPE_API_KEY。")
        
        model_to_use = (model or config.MODEL_NAME_STAGE2 or "").strip()
        if not model_to_use:
            raise ValueError("未配置模型名称")
        
        # Use qwen-vl series for image understanding
        if "qwen" in model_to_use.lower() and "vl" not in model_to_use.lower():
            # Automatically switch to vision model
            model_to_use = "qwen-vl-max"
        
        system_prompt = """你是一位图片内容识别专家。你将收到一张图片和文件信息。

个性化要求（可选；如果为空请忽略）：
<<USER_REQUIREMENTS>>

任务：
1) 仔细观察图片内容
2) 用简洁的中文描述图片的主要内容（不超过15个字）
3) 生成一个适合作为文件名前缀的简短描述（3-8个字）

输出要求（必须严格遵守）：
- 只输出一个 JSON 对象，不能包含任何额外文本
- JSON 结构固定为：{"description": "用于文件名前缀的描述"}
- description：用于文件名前缀的内容描述，建议 6-18 个字，尽量避免标点符号

示例：
{"description": "傍晚海边日落景色"}
{"description": "年度总结会议现场"}
"""
        
        req_norm = self._normalize_user_requirements(user_requirements)
        system_prompt = self._apply_user_requirements(system_prompt, user_requirements)
        
        file_name = file_info.get("name", "")
        file_path = file_info.get("relative_path", "")
        
        user_content = f"文件名：{file_name}\n相对路径：{file_path}\n\n请分析这张图片并生成重命名前缀。"
        
        try:
            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            *(
                                [{"type": "text", "text": f"个性化要求（请严格遵守）：\n{req_norm}"}]
                                if req_norm
                                else []
                            ),
                            {"type": "text", "text": user_content},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                            },
                        ],
                    },
                ],
                max_tokens=200,
            )
            raw = str(completion.choices[0].message.content or "")
            obj = self._parse_json_object(raw)
            # Prefer description as the filename prefix (user request). Fallback to prefix for compatibility.
            description = obj.get("description")
            if isinstance(description, str) and description.strip():
                return description.strip()
            prefix = obj.get("prefix")
            if isinstance(prefix, str) and prefix.strip():
                return prefix.strip()
            raise ValueError("图片识别返回格式错误：缺少 description")
        except Exception as e:
            # Add minimal context to help users debug provider/model incompatibilities.
            ctx = f"model={model_to_use}, base_url={self._base_url or '(default)'}, image_b64_len={len(image_base64 or '')}"
            print(f"AI Image Service Error: {e} ({ctx})")
            raise RuntimeError(f"图片识别调用失败: {e} ({ctx})") from e

    def get_organization_plan(self, directory_json):
        """
        Sends the directory structure to the AI model and retrieves the organization plan (CMD commands).
        """
        return self._chat(config.SYSTEM_PROMPT, directory_json, model=config.MODEL_NAME)
