# ECNUClaw Architecture

## Overview

ECNUClaw 是华东师范大学智能教育实验室研发的 K-12 智能学伴框架，基于张治教授的「教育大脑」三层架构设计。

## Core Data Flow

```
User Input
    │
    ▼
Intent Router ─── classify intent → route to agent + model
    │
    ▼
Agent.chat()
    │
    ├── 1. Memory recall (search_memory by intent + subject)
    ├── 2. Load 5-dimension learner profile
    ├── 3. Build messages (system prompt + profile + memory + adaptive strategy + input)
    ├── 4. Model call (generate via ModelAdapter)
    ├── 5. Tool call loop (if tool_calls in response)
    │       ├── parse tool calls
    │       ├── execute via ToolRegistry
    │       └── feed results back to model
    ├── 6. Update history
    ├── 7. Summarize session → write to MemoryStore
    ├── 8. Update learner profile (5 dimensions from interaction signals)
    └── 9. Return response
```

## Learner Profile System (5 Dimensions)

Based on Zhang Zhi's Digital Portrait Three-Layer Framework:

| Dimension | Data Class | Key Fields |
|-----------|-----------|------------|
| **Cognitive** | `CognitiveDimension` | knowledge_state, bloom_level, prior_knowledge, knowledge_tracing |
| **Behavioral** | `BehavioralDimension` | question_frequency, tool_usage, interaction_patterns, total_sessions |
| **Emotional** | `EmotionalDimension` | current_mood, motivation_level, self_efficacy, frustration_count |
| **Metacognitive** | `MetacognitiveDimension` | self_regulation, preferred_strategy, reflection_ability |
| **Contextual** | `ContextualDimension` | grade, learning_environment, subject_focus, learning_goal |

Profile is stored in SQLite (`learner_profile` table) and automatically updated after each interaction via `update_profile_from_interaction()`.

## Adaptive Strategy Engine

Profile signals drive real-time strategy injection into system prompts:

- **Emotional adaptation**: low self-efficacy → more encouragement, high motivation → raise challenge
- **Cognitive adaptation**: multiple weak topics → foundation building, Bloom's level → scaffold to next level
- **Metacognitive adaptation**: strategy preference → adjust guidance style

## Memory System

4 categories stored in SQLite (`~/.ecnuclaw/memory.db`):

- **student_profile**: Student attributes (grade, learning style, preferences)
- **learning_progress**: Learning trajectory (current chapter, errors, mastery)
- **session_summary**: Per-session outcomes (key points, tool results, follow-ups)
- **skill_memory**: Reusable teaching patterns

Recall strategy: query by `intent keywords + subject + tags`, rank by `relevance_score × access_count`.

## Planner

5 built-in templates matched by goal keywords:

| Trigger Keyword | Template | Steps |
|-----------------|----------|-------|
| 复习/回顾 | Review | 4 steps |
| 学/了解/新概念 | Learn | 5 steps |
| 做题/练习 | Practice | 4 steps |
| 作文/写作 | Writing | 5 steps |
| (default) | General | 5 steps |

`replan()` adjusts based on student feedback:
- Positive → skip easy steps
- Negative → insert review steps
- Frustration → insert encouragement

## Intent Router

Keyword-based classification into 7 intents:

1. `math_calculation` → math agent, innoSpark model, calculator tool
2. `text_creation` → chinese agent, qwen model
3. `knowledge_qa` → subject-specific agent, innoSpark model, knowledge tool
4. `learning_plan` → general agent, innoSpark model, timer tool
5. `emotional_support` → general agent, doubao model
6. `tool_call` → routed by specific tool
7. `multi_turn` / `general` → current agent, innoSpark model

## Model Adapters

| Adapter | Base URL | Default Model | Env Key |
|---------|----------|---------------|---------|
| InnoSpark | `api.innospark.ai/v1` | innoSpark | `INNOSPARK_API_KEY` |
| Doubao | `ark.cn-beijing.volces.com/api/v3` | endpoint_id | `DOUBAO_API_KEY` + `DOUBAO_ENDPOINT_ID` |
| Qwen | `dashscope.aliyuncs.com/compatible-mode/v1` | qwen-plus | `QWEN_API_KEY` |
| DeepSeek | `api.deepseek.com/v1` | deepseek-chat | `DEEPSEEK_API_KEY` |

## Assessment

Teaching quality evaluation (3 dimensions):
- **Knowledge Accuracy** (0-1)
- **Interaction Naturalness** (0-1)
- **Personalization** (0-1)

Learner profile evaluation (4 dimensions):
- **Cognitive Score** — Bloom's level + knowledge mastery
- **Behavioral Score** — session count + engagement
- **Emotional Score** — motivation + self-efficacy + mood
- **Metacognitive Score** — self-regulation + reflection ability

## CLI Commands

| Command | Description |
|---------|-------------|
| `/switch <agent>` | Switch to a different subject agent |
| `/agents` | List available agents |
| `/history` | Show recent conversation history |
| `/profile` | Display student profile |
| `/route_stats` | Show routing statistics |
| `/help` | Show available commands |
| `/quit` | Exit ECNUClaw |

## File Layout

```
~/.ecnuclaw/
├── memory.db          # SQLite database (memories + contexts + learner_profile)
├── skills.json        # Teaching skill library
└── history            # CLI command history
```
