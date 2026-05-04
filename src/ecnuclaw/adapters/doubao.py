import os
from typing import Generator

from openai import OpenAI, APIError, APITimeoutError, APIConnectionError

from ecnuclaw.adapters.base import ModelAdapter, ModelResponse, ModelAdapterError


class DoubaoAdapter(ModelAdapter):
    DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

    def __init__(self, api_key: str = None, base_url: str = None, endpoint_id: str = None, **kwargs):
        super().__init__(
            "doubao",
            api_key or os.getenv("DOUBAO_API_KEY", ""),
            base_url or os.getenv("DOUBAO_BASE_URL", self.DEFAULT_BASE_URL),
            **kwargs,
        )
        self.endpoint_id = endpoint_id or os.getenv("DOUBAO_ENDPOINT_ID", "")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        try:
            kwargs = {
                "model": self.endpoint_id,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            content = choice.message.content or ""

            tool_calls = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    tool_calls.append({
                        "tool_name": tc.function.name,
                        "arguments": tc.function.arguments,
                    })

            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return ModelResponse(
                content=content,
                tool_calls=tool_calls,
                usage=usage,
                model=response.model or self.endpoint_id,
            )
        except APITimeoutError as e:
            raise ModelAdapterError(f"Doubao request timeout: {e}", provider="doubao")
        except APIConnectionError as e:
            raise ModelAdapterError(f"Doubao connection error: {e}", provider="doubao")
        except APIError as e:
            raise ModelAdapterError(
                f"Doubao API error: {e}",
                provider="doubao",
                status_code=e.status_code,
            )

    def stream(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        try:
            kwargs = {
                "model": self.endpoint_id,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        except APITimeoutError as e:
            raise ModelAdapterError(f"Doubao stream timeout: {e}", provider="doubao")
        except APIConnectionError as e:
            raise ModelAdapterError(f"Doubao stream connection error: {e}", provider="doubao")
        except APIError as e:
            raise ModelAdapterError(
                f"Doubao stream API error: {e}",
                provider="doubao",
                status_code=e.status_code,
            )
