import json
import time
from typing import Optional

from lebotclaw.core.memory import MemoryStore
from lebotclaw.tools.registry import ToolRegistry
from lebotclaw.adapters.base import ModelAdapter, ModelResponse
from lebotclaw.core.planner import Planner
from lebotclaw.tools.base import Tool


class Agent:

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: ToolRegistry = None,
        model_adapter: ModelAdapter = None,
        memory: MemoryStore = None,
        planner: Planner = None,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or ToolRegistry()
        self.model_adapter = model_adapter
        self.memory = memory or MemoryStore()
        self.planner = planner or Planner()
        self._history: list[dict] = []
        self._frozen_context_id: Optional[str] = None

    def chat(self, user_input: str) -> str:
        if not user_input.strip():
            return "请输入你的问题，我来帮你学习！"

        enriched_prompt = self._build_system_prompt_with_memory(user_input)

        messages = [{"role": "system", "content": enriched_prompt}]
        messages.extend(self._history)
        messages.append({"role": "user", "content": user_input})

        tool_schemas = self.tools.list_tools() if self.tools._tools else None

        if self.model_adapter is None:
            response_text = self._offline_respond(user_input, messages)
            self._history.append({"role": "user", "content": user_input})
            self._history.append({"role": "assistant", "content": response_text})
            self.memory.summarize_session(self._history)
            return response_text

        response = self.model_adapter.generate(
            messages=messages,
            tools=tool_schemas,
            temperature=0.7,
            max_tokens=2048,
        )

        if response.tool_calls:
            self._history.append({"role": "user", "content": user_input})
            self._history.append({
                "role": "assistant",
                "content": response.content or "",
            })

            tool_results = self._handle_tool_calls(response.tool_calls)

            for tr in tool_results:
                tool_msg = {
                    "role": "tool",
                    "content": tr.get("output", ""),
                    "tool_name": tr.get("tool_name", ""),
                    "success": tr.get("success", False),
                }
                messages.append(tool_msg)
                self._history.append(tool_msg)

            second_response = self.model_adapter.generate(
                messages=messages,
                tools=tool_schemas,
                temperature=0.7,
                max_tokens=2048,
            )
            final_text = second_response.content or ""
            self._history.append({"role": "assistant", "content": final_text})
        else:
            final_text = response.content or ""
            self._history.append({"role": "user", "content": user_input})
            self._history.append({"role": "assistant", "content": final_text})

        self.memory.summarize_session(self._history)
        return final_text

    def chat_stream(self, user_input: str):
        if not user_input.strip():
            yield "请输入你的问题，我来帮你学习！"
            return

        enriched_prompt = self._build_system_prompt_with_memory(user_input)

        messages = [{"role": "system", "content": enriched_prompt}]
        messages.extend(self._history)
        messages.append({"role": "user", "content": user_input})

        tool_schemas = self.tools.list_tools() if self.tools._tools else None

        if self.model_adapter is None:
            response_text = self._offline_respond(user_input, messages)
            self._history.append({"role": "user", "content": user_input})
            self._history.append({"role": "assistant", "content": response_text})
            self.memory.summarize_session(self._history)
            yield response_text
            return

        collected_chunks = []
        for chunk in self.model_adapter.stream(
            messages=messages,
            tools=tool_schemas,
            temperature=0.7,
            max_tokens=2048,
        ):
            collected_chunks.append(chunk)
            yield chunk

        full_response = "".join(collected_chunks)
        self._history.append({"role": "user", "content": user_input})
        self._history.append({"role": "assistant", "content": full_response})
        self.memory.summarize_session(self._history)

    def freeze(self) -> str:
        context_data = {
            "agent_name": self.name,
            "history": self._history,
            "frozen_at": time.time(),
        }
        self._frozen_context_id = self.memory.freeze_context(self.name, context_data)
        return self._frozen_context_id

    def restore(self, context_id: str) -> None:
        data = self.memory.restore_context(context_id)
        if not data:
            return
        self._frozen_context_id = context_id
        inner = data.get("data", data)
        self._history = inner.get("history", [])

    def reset(self) -> None:
        self._history = []

    def _build_system_prompt_with_memory(self, user_input: str) -> str:
        prompt_parts = [self.system_prompt]

        related = self.memory.search_memory(query=user_input, limit=5)
        if related:
            memory_lines = []
            for entry in related:
                content = entry.content
                if len(content) > 150:
                    content = content[:150] + "..."
                memory_lines.append(f"- [{entry.category}] {content}")
            prompt_parts.append("\n\n相关学习记忆：\n" + "\n".join(memory_lines))

        profile = self.memory.get_student_profile()
        if profile:
            profile_summary = json.dumps(profile, ensure_ascii=False, indent=None)
            prompt_parts.append(f"\n\n学生画像：{profile_summary}")

        return "\n".join(prompt_parts)

    def _handle_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        results = []
        for tc in tool_calls:
            tool_name = tc.get("tool_name", "")
            raw_args = tc.get("arguments", {})

            if isinstance(raw_args, str):
                try:
                    raw_args = json.loads(raw_args)
                except json.JSONDecodeError:
                    raw_args = {}

            try:
                result = self.tools.execute(tool_name, **raw_args)
                results.append({
                    "tool_name": tool_name,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error or "",
                })
            except Exception as e:
                results.append({
                    "tool_name": tool_name,
                    "success": False,
                    "output": "",
                    "error": str(e),
                })
        return results

    def _offline_respond(self, user_input: str, messages: list[dict]) -> str:
        # 无模型时，尝试直接执行工具
        tool_calls = Tool.parse_tool_calls(user_input)
        if tool_calls:
            results = self._handle_tool_calls(tool_calls)
            parts = []
            for r in results:
                if r["success"]:
                    parts.append(r["output"])
                else:
                    parts.append(f"工具 {r['tool_name']} 执行失败: {r['error']}")
            if parts:
                return "\n\n".join(parts)

        # 尝试按常见模式直接调用工具
        import re
        calc_pattern = re.compile(r'[\d.]+\s*[+\-*/×÷^]\s*[\d.]+|sqrt|sin|cos|tan|log')
        if calc_pattern.search(user_input):
            expr = user_input.strip()
            try:
                result = self.tools.execute("calculator", expression=expr)
                if result.success:
                    return result.output
            except (KeyError, Exception):
                pass

        if "查" in user_input or "字典" in user_input or "词典" in user_input:
            word = re.sub(r'查[一下]?[字典词典]*', '', user_input).strip()
            if word:
                try:
                    result = self.tools.execute("dictionary", word=word)
                    if result.success:
                        return result.output
                except (KeyError, Exception):
                    pass

        return (
            f"⚠ 未连接 AI 模型，无法回答你的问题。\n"
            f"请配置 API Key 后重启 LebotClaw（推荐 DeepSeek 或 Qwen）。\n"
            f"设置方法：export DEEPSEEK_API_KEY=\"your-key\""
        )


class AgentRegistry:

    def __init__(self):
        self._agents: dict[str, Agent] = {}
        self._active_agent: Optional[str] = None

    def register(self, agent: Agent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> Agent:
        if name not in self._agents:
            raise KeyError(
                f"Agent '{name}' not found. Available: {list(self._agents.keys())}"
            )
        return self._agents[name]

    def list_agents(self) -> list[str]:
        return list(self._agents.keys())

    def get_active(self) -> Optional[Agent]:
        if self._active_agent:
            return self._agents.get(self._active_agent)
        return None

    def switch_to(self, name: str) -> Agent:
        if self._active_agent and self._active_agent in self._agents:
            self._agents[self._active_agent].freeze()
        self._active_agent = name
        agent = self.get(name)
        if agent._frozen_context_id:
            agent.restore(agent._frozen_context_id)
        return agent
