# ECNUClaw

**A Learner-Profiled Intelligent Study Companion Framework for K-12 Personalized Education**

基于张治教授「数字画像 + 教育大脑 + 人机协同智商」理论的 K-12 智能学伴框架，由华东师范大学智能教育实验室研发。

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 67 passed](https://img.shields.io/badge/Tests-67%20passed-brightgreen.svg)](tests/)

---

## Theoretical Foundations

ECNUClaw is grounded in three core theories developed by Prof. Zhi Zhang (张治) and colleagues at ECNU's Intelligent Education Laboratory:

### 1. Digital Portrait Three-Layer Framework (数字画像三层框架, 2021)

> 张治 等. 基于数字画像的综合素质评价：框架、指标、模型与应用. 中国电化教育, 2021(8): 25-33.

ECNUClaw implements this framework through a **5-dimension learner profile** that replaces static test-score-driven assessment with dynamic, data-driven, multi-dimensional profiling:

| Layer | ECNUClaw Implementation |
|-------|------------------------|
| **Indicator System Layer** | 5 profile dimensions with structured indicators (cognitive, behavioral, emotional, metacognitive, contextual) |
| **Data Practice Layer** | Multi-source data extraction from conversations — dialogue behavior, tool usage, error patterns, emotional signals, metacognitive markers |
| **Digital Portrait Layer** | SQLite-persisted `LearnerProfile` with dynamic updates across sessions, plus structured summary output |

### 2. Education Brain Model (教育大脑模型, 2022)

> 张治, 徐冰冰. 人工智能教育大脑的生态架构和应用场景. 开放教育研究, 2022(02): 64-72.

ECNUClaw's architecture mirrors the three-layer brain-inspired computing model:

| Brain Layer | Function | ECNUClaw Module |
|------------|----------|-----------------|
| **Sensory Nervous System** | Multi-source data perception | CLI interaction + Intent Router + conversation signal extraction |
| **Central Nervous System** | AI analysis + profile construction + pedagogical decision | Agent + LearnerProfile + Planner + adaptive strategy generation |
| **Motor Nervous System** | Personalized output + adaptive intervention | HEADS Prompt Templates + profile-driven adaptive strategies + tool calling |

### 3. Human-AI Collaborative IQ (人机协同智商, 2023)

> 张治. ChatGPT/生成式人工智能重塑教育的底层逻辑和可能路径. 华东师范大学学报(教育科学版), 2023, 41(7): 131-142.

ECNUClaw is designed not to replace learning, but to enhance learners' thinking and metacognitive abilities through:
- Socratic questioning rather than direct answer-giving
- Profile-aware scaffolding that adapts to cognitive level (Bloom's taxonomy)
- Metacognitive reflection prompts embedded in teaching strategies
- Goal: cultivating the learner's ability to **collaborate with AI to solve problems**

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Education Brain Architecture               │
│                 (张治「教育大脑」三层架构)                       │
├──────────────────────────────────────────────────────────────┤
│  Motor Layer (类脑运动神经系统)                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  HEADS Templates + Adaptive Strategies                  │ │
│  │  Profile-driven: detail level / guidance strength /     │ │
│  │  encouragement frequency / Bloom scaffolding             │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│  Central Layer (类脑中枢神经系统)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │   Agent      │  │   Learner    │  │     Planner       │  │
│  │  Registry    │  │   Profile    │  │  5 Teaching Plans │  │
│  │ Math/Chinese │  │  5 Dimensions│  │  + Replan         │  │
│  │ Science/Gen  │  │  + Auto-     │  │                   │  │
│  │              │  │    Update    │  │                   │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────────────┘  │
│         │                 │                                   │
│  ┌──────┴─────────────────┴──────────────────────────────┐   │
│  │              Tool Calling Framework                     │   │
│  │   calculator │ dictionary │ knowledge │ timer           │   │
│  └────────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│  Sensory Layer (类脑感知神经系统)                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  CLI + Intent Router + Signal Extraction                │ │
│  │  Cognitive signals │ Emotional markers │ Behavioral data│ │
│  │  Metacognitive cues │ Contextual info                    │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│              Assessment Module                                │
│  Cognitive │ Behavioral │ Emotional │ Metacognitive           │
│  + Teaching Quality: Accuracy │ Naturalness │ Personalization│
└──────────────────────────────────────────────────────────────┘
```

---

## 5-Dimension Learner Profile

ECNUClaw maintains a dynamic learner profile across 5 dimensions, automatically extracted from conversations:

| Dimension | Indicators | Data Sources |
|-----------|-----------|--------------|
| **Cognitive** | Knowledge state, Bloom's taxonomy level, prior knowledge, knowledge tracing | Question patterns, error analysis, topic coverage |
| **Behavioral** | Question frequency, session duration, tool usage, interaction patterns | Conversation logs, tool call records |
| **Emotional** | Current mood, motivation level, self-efficacy, frustration count | Sentiment markers (困惑/挫折/兴奋), engagement signals |
| **Metacognitive** | Self-regulation, preferred learning strategy, reflection ability | Strategy choice keywords, reflection markers |
| **Contextual** | Grade, learning environment, subject focus, learning goal | Setup wizard, profile migration |

The profile is automatically updated after each interaction via `update_profile_from_interaction()`, and injected into the system prompt to drive adaptive teaching strategies.

---

## Adaptive Teaching Strategies

ECNUClaw generates **profile-aware adaptive strategies** in real-time:

| Profile Signal | Adaptive Response |
|---------------|-------------------|
| Low self-efficacy / high frustration | Increase encouragement, reduce difficulty, validate effort |
| High motivation | Raise challenge level, encourage independent exploration |
| Multiple weak knowledge points | Prioritize foundation building, use analogies and examples |
| Bloom's "remember" level | Help build connections, scaffold toward "understand" |
| Bloom's "apply" level | Provide varied exercises, scaffold toward "analyze" |
| Prefers guided learning | More Socratic questioning, structured step-by-step |
| Prefers exploratory learning | Open-ended problems, less direct guidance |

---

## Project Structure

```
ECNUClaw/
├── src/lebotclaw/
│   ├── core/
│   │   ├── agent.py          # Agent + profile injection + adaptive strategies
│   │   ├── memory.py         # MemoryStore + LearnerProfile (5 dimensions)
│   │   ├── router.py         # Intent classification + routing
│   │   ├── planner.py        # 5 teaching plan templates + replan
│   │   ├── skills.py         # Teaching skill library
│   │   └── cli.py            # CLI entry point
│   ├── tools/                # Tool calling framework
│   │   └── builtin/          # calculator, dictionary, knowledge, timer
│   ├── adapters/             # Multi-model adapters (DeepSeek/Qwen/GLM/Kimi/...)
│   └── education/
│       ├── heads.py          # HEADS templates (教育大脑 + 人机协同)
│       ├── assessment.py     # Multi-dimension assessment + profile evaluation
│       └── subjects/         # Math/Chinese/Science agents
├── tests/                    # 67 tests
└── pyproject.toml
```

---

## Quick Start

```bash
pip install lebotclaw
```

```python
from lebotclaw.core.agent import Agent, AgentRegistry
from lebotclaw.core.memory import MemoryStore

# Create an agent with learner profiling
memory = MemoryStore()
agent = Agent(
    name="math_companion",
    system_prompt="...",  # or use HEADSTemplate.math_prompt()
    memory=memory,
)

response = agent.chat("我不会做这道分数题")

# The learner profile is automatically updated
profile = memory.get_learner_profile()
print(memory.get_learner_summary())
```

---

## Key References

- 张治 等. 基于数字画像的综合素质评价：框架、指标、模型与应用. 中国电化教育, 2021(8): 25-33.
- 张治, 戚业国. 基于大数据的多源多维综合素质评价模型的构建. 中国电化教育, 2017(09): 69-77.
- 余明华, 张治, 祝智庭. 基于可视化学习分析的研究性学习学生画像构建研究. 中国电化教育, 2020(12): 36-43.
- 张治, 徐冰冰. 人工智能教育大脑的生态架构和应用场景. 开放教育研究, 2022(02): 64-72.
- 张治. ChatGPT/生成式人工智能重塑教育的底层逻辑和可能路径. 华东师范大学学报(教育科学版), 2023, 41(7): 131-142.
- 张治, 刘德建, 徐冰冰. 智能型数字教材系统的核心理念和技术实现. 开放教育研究, 2021(01): 44-54.

---

## Authors

- **Yizhou Zhou** (周艺舟) — East China Normal University
- **Jiayin Li** (李佳音) — East China Normal University
- **Zhi Zhang** (张治) — East China Normal University (Corresponding Author)

## Acknowledgments

Research conducted at the **Intelligent Education Laboratory** (智能教育实验室), Faculty of Education, East China Normal University (华东师范大学教育学部).

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*East China Normal University · Intelligent Education Laboratory · 2026*
