# LebotClaw 🐾

**A Safe, Low-Barrier CLI Intelligent Study Companion for K-12 Learners**

面向 K-12 学生的终端智能学伴框架 — 融合"智能学伴"理念，让每个孩子都能拥有一个安全、可靠、低门槛的 AI 学习伙伴，记住你、理解你、陪你一起成长。

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 67 passed](https://img.shields.io/badge/Tests-67%20passed-brightgreen.svg)](tests/)

---

## Why LebotClaw?

| Principle | How We Do It |
|-----------|-------------|
| **Education-First Safety** | Content filtering, age-appropriate responses, topic boundary enforcement — students only discuss learning |
| **Intelligent Study Companion** | Not a chatbot that gives answers — a study buddy that guides you to think, step by step, with patience and encouragement |
| **Low Barrier** | 4-step setup wizard, all-Chinese interface, no technical knowledge needed — works right out of the box |
| **Persistent Understanding** | Remembers your name, grade, strengths, and weaknesses across sessions — gets to know you better over time |
| **Reliable Architecture** | Tool calling protocol, structured memory, intent routing, and multi-agent orchestration — built on proven patterns |

## Features

- **Intelligent Study Companion** — 数学问伴、语文问伴、科学问伴、万能问伴，4 个学科伙伴自动路由
- **Safe Education Memory** — SQLite 驱动的 4 类教育记忆（学生画像、学习进度、会话摘要、技能沉淀）
- **HEADS Prompt Templates** — K-12 专属的温暖、鼓励式教学提示词，不直接给答案，引导思考
- **Tool Calling Framework** — 统一的工具调用协议，内置计算器、字典、知识库、计时器 4 个教育工具
- **Intent Router** — 意图识别 + 自动路由，学生不需要手动切换，问什么问题就找什么伙伴
- **Task Planner** — 5 套教育规划模板（复习/学习/练习/写作/通用），分步引导
- **Skill Library** — 成功教学链路自动沉淀为可复用技能模板
- **Multi-Model Adapters** — DeepSeek / Qwen / GLM / Kimi / Doubao / Seed / InnoSpark 7 个国内模型适配器
- **Setup Wizard** — 4 步初始化向导（选模型、选风格、选详细程度、填写学生信息），零门槛上手

## Architecture

```
┌──────────────────────────────────────────────────┐
│                  CLI Interface                    │
│          (prompt_toolkit + rich)                  │
├──────────────────────────────────────────────────┤
│              Intent Router                        │
│   (关键词匹配 → 意图分类 → Agent路由 → 模型路由)    │
├──────────────────────────────────────────────────┤
│  AgentRegistry                                    │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │
│  │ Math │ │Chinese│ │Science│ │General│           │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘            │
│     │        │        │        │                  │
│  ┌──┴────────┴────────┴────────┴──┐              │
│  │         ToolRegistry            │              │
│  │ calculator dictionary knowledge │              │
│  │          timer                  │              │
│  └─────────────────────────────────┘              │
├──────────────────────────────────────────────────┤
│  MemoryStore (SQLite)  │  SkillLibrary (JSON)    │
│  · Student Profile     │  · Teaching Templates   │
│  · Learning Progress   │  · Auto-Extract Skills  │
│  · Session Summary     │                         │
│  · Skill Memory        │                         │
├──────────────────────────────────────────────────┤
│  Planner           │  ModelAdapters              │
│  · Decompose       │  · DeepSeek / Qwen / GLM    │
│  · Replan          │  · Kimi / Doubao / Seed     │
│  · 5 Templates     │  · InnoSpark                │
├──────────────────────────────────────────────────┤
│            Assessment Module                      │
│  知识准确性 │ 交互自然度 │ 个性化适配度             │
└──────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
pip install lebotclaw
```

### 5 Lines to Run

```python
from lebotclaw.core.agent import Agent, AgentRegistry
from lebotclaw.core.router import IntentRouter

router = IntentRouter()
registry = AgentRegistry()

# Register default agents (math, chinese, science, general)
from lebotclaw.education.subjects import MathAgent, ChineseAgent, ScienceAgent
registry.register(MathAgent.create())
registry.register(ChineseAgent.create())
registry.register(ScienceAgent.create())

# Start the CLI
from lebotclaw.core.cli import main
main()
```

### Use as a Library

```python
from lebotclaw.core.memory import MemoryStore
from lebotclaw.core.planner import Planner

# Plan a learning session
planner = Planner()
plan = planner.decompose("帮我复习分数", subject="math")
for step in plan.steps:
    print(f"  {step.id}. {step.title}")

# Save student memory
memory = MemoryStore()
memory.save_memory("student_profile", "math", "年级", "五年级")
memory.save_memory("learning_progress", "math", "错题", "分数加减法容易忘记通分")

# Recall relevant memory
results = memory.search_memory(query="分数", subject="math")
```

### Custom Agent

```python
from lebotclaw.core.agent import Agent
from lebotclaw.tools.builtin.calculator import CalculatorTool
from lebotclaw.tools.registry import ToolRegistry

tools = ToolRegistry()
tools.register(CalculatorTool())

agent = Agent(
    name="my_math_agent",
    system_prompt="你是一个友善的数学老师，善于引导学生思考。",
    tools=tools,
)

# When model_adapter is configured, agent.chat() runs the full pipeline
response = agent.chat("3 * 7 + 2 等于多少？")
```

## Project Structure

```
LebotClaw/
├── src/lebotclaw/
│   ├── core/                    # Core Engine
│   │   ├── agent.py             # Agent base class + AgentRegistry
│   │   ├── router.py            # Intent classification + routing
│   │   ├── memory.py            # SQLite-backed persistent memory
│   │   ├── planner.py           # Task decomposition + replan
│   │   ├── skills.py            # Teaching skill library
│   │   └── cli.py               # CLI entry point
│   ├── tools/                   # Tool Calling Framework
│   │   ├── base.py              # Tool/ToolCall/ToolResult
│   │   ├── registry.py          # ToolRegistry
│   │   └── builtin/             # Built-in tools
│   │       ├── calculator.py    # Math expression calculator
│   │       ├── dictionary.py    # Chinese-English dictionary
│   │       ├── knowledge.py     # K-12 knowledge retrieval
│   │       └── timer.py         # Study timer / Pomodoro
│   ├── adapters/                # Model Adapters (OpenAI-compatible)
│   │   ├── base.py              # ModelAdapter base
│   │   ├── deepseek.py          # DeepSeek
│   │   ├── qwen.py              # Qwen (Alibaba)
│   │   ├── glm.py               # GLM (Zhipu AI)
│   │   ├── kimi.py              # Kimi (Moonshot)
│   │   ├── doubao.py            # Doubao (ByteDance)
│   │   └── innoSpark.py         # InnoSpark education model
│   └── education/               # Education Modules
│       ├── heads.py             # HEADS prompt templates
│       ├── assessment.py        # Growth assessment
│       └── subjects/            # Subject agents
│           ├── math.py
│           ├── chinese.py
│           └── science.py
├── tests/                       # 67 tests
├── docs/
│   └── architecture.md
└── pyproject.toml
```

## Memory Architecture

LebotClaw implements a 4-category education memory system inspired by OpenClaw's persistent memory and Hermes's growing memory concepts:

| Category | What It Stores | Example |
|----------|---------------|---------|
| `student_profile` | Student attributes and preferences | 年级, 学习风格, 学科偏好 |
| `learning_progress` | Learning trajectory and weak points | 错题记录, 当前章节, 知识盲点 |
| `session_summary` | Session-level outcomes | 知识点讲解, 工具结果摘要, 待跟进事项 |
| `skill_memory` | Successful teaching patterns | 高质量讲解套路, 可复用教学模板 |

Memory lifecycle: **对话/工具执行 → 抽取关键记忆 → 持久化保存 → 按意图/学科召回 → 注入 prompt → 执行后更新**

## Planning Templates

The Planner includes 5 built-in education templates:

| Trigger | Template | Steps |
|---------|----------|-------|
| "复习/回顾" | Review | 知识点回顾 → 例题练习 → 错题巩固 → 总结 |
| "学/了解/新概念" | Learn | 概念引入 → 举例说明 → 练习闯关 → 检查理解 → 拓展应用 |
| "做题/练习" | Practice | 题目分析 → 分步解答 → 方法总结 → 变式训练 |
| "作文/写作" | Writing | 审题 → 素材收集 → 列提纲 → 写作 → 修改润色 |
| Other | General | 目标确认 → 知识准备 → 实践练习 → 检查反馈 → 总结 |

## Configuration

Model adapters read API keys from environment variables:

```bash
export DEEPSEEK_API_KEY="your-key"
export QWEN_API_KEY="your-key"
export GLM_API_KEY="your-key"
export MOONSHOT_API_KEY="your-key"       # Kimi
export DOUBAO_API_KEY="your-key"
export INNOSPARK_API_KEY="your-key"
```

Or use the built-in setup wizard (`lebotclaw setup`) to configure interactively.

Memory and skills are stored in `~/.lebotclaw/` by default.

## Inspiration & References

LebotClaw draws engineering and pedagogical ideas from:

- **OpenClaw** — Tool calling protocol, agent registration, persistent memory
- **Hermes Agent** — Long-horizon planning, skill formation, cross-session memory growth
- **Intelligent Tutoring Systems (ITS)** — Socratic questioning, adaptive scaffolding, formative assessment
- **HEADS Framework** — Human-centered education agent design principles
- **OpenHands** — Agent SDK modularity, multi-entry deployment

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built by [Lanboat Intelligence](https://lanboat.com) · 苏州斓舟智能科技有限公司 · 2026*
