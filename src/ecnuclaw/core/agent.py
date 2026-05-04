import json
import time
from typing import Optional

from ecnuclaw.core.memory import MemoryStore, LearnerProfile
from ecnuclaw.tools.registry import ToolRegistry
from ecnuclaw.adapters.base import ModelAdapter, ModelResponse
from ecnuclaw.core.planner import Planner
from ecnuclaw.tools.base import Tool


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
            self.memory.update_profile_from_interaction(self._history)
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
        self.memory.update_profile_from_interaction(self._history)
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
            self.memory.update_profile_from_interaction(self._history)
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
        self.memory.update_profile_from_interaction(self._history)

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

        # 注入 5 维学习者画像（张治「数字画像三层框架」）
        profile = self.memory.get_learner_profile()
        prompt_parts.append("\n\n" + self._build_profile_injection(profile))

        # 注入画像驱动的自适应策略
        adaptive = self._build_adaptive_strategy(profile)
        if adaptive:
            prompt_parts.append("\n\n" + adaptive)

        return "\n".join(prompt_parts)

    def _build_profile_injection(self, profile: LearnerProfile) -> str:
        c = profile.cognitive
        b = profile.behavioral
        e = profile.emotional
        m = profile.metacognitive
        ctx = profile.contextual

        bloom_names = {
            "remember": "记忆", "understand": "理解", "apply": "应用",
            "analyze": "分析", "evaluate": "评价", "create": "创造",
        }

        weak_topics = [k for k, v in c.knowledge_state.items() if v == "weak"]
        mastered = [k for k, v in c.knowledge_state.items() if v == "mastered"]

        lines = [
            "【学习者画像】（基于张治「数字画像三层框架」）",
            f"情境维度：年级「{ctx.grade or '未知'}」| 专注「{ctx.subject_focus or '未设定'}」| 目标「{ctx.learning_goal or '未设定'}」",
            f"认知维度：布鲁姆「{bloom_names.get(c.bloom_level, c.bloom_level)}」水平 | 先验知识 {len(c.prior_knowledge)} 项",
        ]
        if weak_topics:
            lines.append(f"  ⚠ 薄弱知识点：{', '.join(weak_topics[:5])}")
        if mastered:
            lines.append(f"  ✓ 已掌握：{', '.join(mastered[:5])}")

        lines.append(f"行为维度：累计 {b.total_sessions} 次会话 | 提问 {b.total_questions} 次")
        lines.append(f"情感维度：动机 {e.motivation_level:.0%} | 自我效能 {e.self_efficacy:.0%} | 累计受挫 {e.frustration_count} 次")
        lines.append(f"元认知维度：策略偏好「{m.preferred_strategy}」| 反思能力 {m.reflection_ability:.0%}")

        return "\n".join(lines)

    def _build_adaptive_strategy(self, profile: LearnerProfile) -> str:
        strategies = []
        e = profile.emotional
        c = profile.cognitive
        m = profile.metacognitive

        # 情感自适应
        if e.self_efficacy < 0.3 or e.frustration_count > 5:
            strategies.append(
                "- 该同学自我效能感较低/受挫较多，请增加鼓励频率，降低任务难度，"
                "每次只给一小步，多肯定进步，避免直接指出错误。"
            )
        elif e.motivation_level > 0.8:
            strategies.append(
                "- 该同学动机水平很高，可以适当提高挑战难度，鼓励独立探索和创造性思考。"
            )

        # 认知自适应
        weak_count = sum(1 for v in c.knowledge_state.values() if v == "weak")
        if weak_count > 3:
            strategies.append(
                "- 该同学有多个薄弱知识点，优先巩固基础，"
                "讲解时多用类比和生活例子，确保每步都理解再继续。"
            )

        bloom_detail = {
            "remember": "- 该同学目前处于记忆/识记水平，帮助建立知识点之间的联系，向理解层次提升。",
            "understand": "- 该同学处于理解水平，多引导用自己的话解释概念，向应用层次提升。",
            "apply": "- 该同学处于应用水平，多给变式练习和实际问题，向分析层次提升。",
            "analyze": "- 该同学处于分析水平，引导比较异同、归纳规律，向评价层次提升。",
            "evaluate": "- 该同学处于评价水平，引导批判性思考和论证，向创造层次提升。",
            "create": "- 该同学已达到创造水平，鼓励独立设计和创新性解决问题。",
        }
        if c.bloom_level in bloom_detail:
            strategies.append(bloom_detail[c.bloom_level])

        # 元认知自适应
        if m.preferred_strategy == "guided":
            strategies.append("- 该同学偏好引导式学习，多用提问引导思考，不直接给答案。")
        elif m.preferred_strategy == "exploratory":
            strategies.append("- 该同学偏好探索式学习，给开放性问题和探索空间，少给提示。")
        elif m.preferred_strategy == "collaborative":
            strategies.append("- 该同学偏好协作式学习，多使用「我们一起」的语气，模拟对话式探究。")

        if strategies:
            return "【自适应教学策略】\n" + "\n".join(strategies)
        return ""

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
            f"请配置 API Key 后重启 ECNUClaw（推荐 DeepSeek 或 Qwen）。\n"
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
