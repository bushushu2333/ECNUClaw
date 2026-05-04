from abc import ABC, abstractmethod
from typing import Generator


class ModelMessage:
    def __init__(self, role: str, content: str, tool_calls: list = None):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls or []


class ModelResponse:
    def __init__(self, content: str, tool_calls: list = None, usage: dict = None, model: str = ""):
        self.content = content
        self.tool_calls = tool_calls or []
        self.usage = usage or {}
        self.model = model


class ModelAdapterError(Exception):
    def __init__(self, message: str, provider: str = "", status_code: int = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class ModelAdapter(ABC):
    def __init__(self, model_name: str, api_key: str = "", base_url: str = "", **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs

    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        ...

    @abstractmethod
    def stream(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        ...

    def health_check(self) -> bool:
        try:
            resp = self.generate(
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10,
            )
            return bool(resp.content)
        except Exception:
            return False
