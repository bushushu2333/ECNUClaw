import json
import re
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
    metadata: dict = {}


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    call_id: Optional[str] = None


class Tool(ABC):
    name: str
    description: str
    parameters: dict

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        ...

    def to_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

    @staticmethod
    def parse_tool_calls(message_content: str) -> list[ToolCall]:
        results: list[ToolCall] = []

        pattern_fence = re.compile(
            r"```tool_call\s*\n(.*?)```", re.DOTALL
        )
        for match in pattern_fence.finditer(message_content):
            raw = match.group(1).strip()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            name = data.get("name") or data.get("tool_name")
            if not name:
                continue
            results.append(ToolCall(
                tool_name=name,
                arguments=data.get("arguments", data.get("args", {})),
                call_id=data.get("call_id") or str(uuid.uuid4()),
            ))

        stripped = message_content.strip()
        if stripped.startswith("{") and not results:
            try:
                data = json.loads(stripped)
                name = data.get("name") or data.get("tool_name")
                if name:
                    results.append(ToolCall(
                        tool_name=name,
                        arguments=data.get("arguments", data.get("args", {})),
                        call_id=data.get("call_id") or str(uuid.uuid4()),
                    ))
            except json.JSONDecodeError:
                pass

        pattern_inline = re.compile(
            r'\{[^{}]*"tool_name"\s*:\s*"[^"]+?"[^{}]*\}'
        )
        for match in pattern_inline.finditer(message_content):
            span = match.group(0)
            if any(m.start() <= match.start() < m.end() for m in pattern_fence.finditer(message_content)):
                continue
            try:
                data = json.loads(span)
                results.append(ToolCall(
                    tool_name=data["tool_name"],
                    arguments=data.get("arguments", data.get("args", {})),
                    call_id=data.get("call_id") or str(uuid.uuid4()),
                ))
            except (json.JSONDecodeError, KeyError):
                pass

        return results
