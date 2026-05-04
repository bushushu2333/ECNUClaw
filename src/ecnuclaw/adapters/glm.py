from ecnuclaw.adapters.base import ModelAdapter, ModelResponse, ModelAdapterError
from openai import OpenAI
import os


class GLMAdapter(ModelAdapter):
    """智谱 GLM 系列模型适配器"""

    def __init__(self, api_key=None, model="glm-4-flash", **kwargs):
        super().__init__(
            "glm",
            api_key or os.getenv("GLM_API_KEY", ""),
            "https://open.bigmodel.cn/api/paas/v4",
            **kwargs,
        )
        self.model = model
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(self, messages, tools=None, temperature=0.7, max_tokens=2048):
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            resp = self.client.chat.completions.create(**kwargs)
            choice = resp.choices[0]
            tool_calls = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    import json
                    tool_calls.append({
                        "tool_name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments,
                    })
            return ModelResponse(
                content=choice.message.content or "",
                tool_calls=tool_calls,
                usage={"prompt_tokens": resp.usage.prompt_tokens, "completion_tokens": resp.usage.completion_tokens} if resp.usage else {},
                model=self.model,
            )
        except Exception as e:
            raise ModelAdapterError(str(e), provider="glm")

    def stream(self, messages, tools=None, temperature=0.7, max_tokens=2048):
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }
            if tools:
                kwargs["tools"] = tools
            resp = self.client.chat.completions.create(**kwargs)
            for chunk in resp:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        except Exception as e:
            raise ModelAdapterError(str(e), provider="glm")
