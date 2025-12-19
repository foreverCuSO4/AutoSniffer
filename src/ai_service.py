import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from . import config

class AIService:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self._api_key = (api_key or config.API_KEY or "").strip()
        self._base_url = (base_url or config.API_BASE_URL or "").strip()
        # Delay hard failure until first request so UI can be opened without config.
        self.client = OpenAI(
            api_key=self._api_key or "EMPTY",
            base_url=self._base_url,
        )

    def _chat(self, system_prompt: str, user_content: str, model: Optional[str] = None) -> str:
        if not self._api_key:
            raise ValueError("未配置 API Key。请在 UI 中填写，或设置环境变量 AUTOSNIFFER_API_KEY/DASHSCOPE_API_KEY。")
        model_to_use = (model or config.MODEL_NAME or "").strip()
        if not model_to_use:
            raise ValueError("未配置模型名称")
        try:
            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
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

    def get_folder_plan_stage1(self, directory_json: str, model: Optional[str] = None) -> List[str]:
        """Stage 1: return folder list to create."""
        raw = self._chat(config.SYSTEM_PROMPT_STAGE1_FOLDERS, directory_json, model=model or config.MODEL_NAME_STAGE1)
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

    def choose_destination_stage2(self, payload: Dict[str, Any], model: Optional[str] = None) -> str:
        """Stage 2: choose destination folder for a single file."""
        raw = self._chat(
            config.SYSTEM_PROMPT_STAGE2_DESTINATION,
            json.dumps(payload, ensure_ascii=False),
            model=model or config.MODEL_NAME_STAGE2,
        )
        obj = self._parse_json_object(raw)
        dest = obj.get("destination")
        if not isinstance(dest, str) or not dest.strip():
            raise ValueError("阶段2返回格式错误：缺少 destination")
        return dest.strip()

    def choose_destinations_batch_stage2(self, payload: Dict[str, Any], model: Optional[str] = None) -> List[Dict[str, str]]:
        """Stage 2 (batch): returns list of {relative_path, destination} in the same order as input files."""
        raw = self._chat(
            config.SYSTEM_PROMPT_STAGE2_BATCH_DESTINATION,
            json.dumps(payload, ensure_ascii=False),
            model=model or config.MODEL_NAME_STAGE2,
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

    def get_organization_plan(self, directory_json):
        """
        Sends the directory structure to the AI model and retrieves the organization plan (CMD commands).
        """
        return self._chat(config.SYSTEM_PROMPT, directory_json, model=config.MODEL_NAME)
