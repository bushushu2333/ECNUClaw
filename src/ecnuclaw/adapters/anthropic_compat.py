import json
import os
from typing import Generator

import httpx

from ecnuclaw.adapters.base import ModelAdapter, ModelResponse, ModelAdapterError


class AnthropicCompatAdapter(ModelAdapter):
    """Anthropic Messages API 兼容适配器。

    支持 Kimi Coding (api.kimi.com)、GLM Anthropic 端点、
    以及所有兼容 Anthropic Messages API 格式的第三方服务。
    """

    DEFAULT_BASE_URL = "https://api.anthropic.com"

    def __init__(self, api_key=None, base_url=None, model=None, **kwargs):
        super().__init__(
            "anthropic_compat",
            api_key or os.getenv("ANTHROPIC_AUTH_TOKEN", ""),
            base_url or os.getenv("ANTHROPIC_BASE_URL", self.DEFAULT_BASE_URL),
            **kwargs,
        )
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    def _headers(self):
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def _convert_messages(self, messages):
        system = None
        converted = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                system = content
            elif role in ("user", "assistant"):
                converted.append({"role": role, "content": content})
        return system, converted

    def generate(self, messages, tools=None, temperature=0.7, max_tokens=2048):
        url = f"{self.base_url.rstrip('/')}/v1/messages"
        system, msgs = self._convert_messages(messages)

        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": msgs,
        }
        if system:
            body["system"] = system
        if temperature is not None:
            body["temperature"] = temperature

        try:
            resp = httpx.post(url, headers=self._headers(), json=body, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()

            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")

            usage = {}
            if "usage" in data:
                inp = data["usage"].get("input_tokens", 0)
                out = data["usage"].get("output_tokens", 0)
                usage = {"prompt_tokens": inp, "completion_tokens": out, "total_tokens": inp + out}

            return ModelResponse(
                content=content,
                tool_calls=[],
                usage=usage,
                model=data.get("model", self.model),
            )
        except httpx.HTTPStatusError as e:
            raise ModelAdapterError(
                f"API error ({e.response.status_code}): {e.response.text[:200]}",
                provider="anthropic_compat",
                status_code=e.response.status_code,
            )
        except httpx.TimeoutException as e:
            raise ModelAdapterError(f"请求超时: {e}", provider="anthropic_compat")
        except Exception as e:
            raise ModelAdapterError(f"连接失败: {e}", provider="anthropic_compat")

    def stream(self, messages, tools=None, temperature=0.7, max_tokens=2048):
        url = f"{self.base_url.rstrip('/')}/v1/messages"
        system, msgs = self._convert_messages(messages)

        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": msgs,
            "stream": True,
        }
        if system:
            body["system"] = system
        if temperature is not None:
            body["temperature"] = temperature

        try:
            with httpx.stream("POST", url, headers=self._headers(), json=body, timeout=60.0) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload == "[DONE]":
                        break
                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    if data.get("type") == "content_block_delta":
                        delta = data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield delta.get("text", "")
        except httpx.HTTPStatusError as e:
            raise ModelAdapterError(
                f"Stream API error ({e.response.status_code}): {e.response.text[:200]}",
                provider="anthropic_compat",
                status_code=e.response.status_code,
            )
        except Exception as e:
            raise ModelAdapterError(f"Stream 连接失败: {e}", provider="anthropic_compat")
