# LebotClaw Architecture

## Overview

LebotClaw is a CLI agent runtime designed for K-12 education. It combines OpenClaw-style tool calling and persistent memory with Hermes-style long-horizon planning and skill formation.

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
    ├── 2. Build messages (system prompt + memory + history + input)
    ├── 3. Model call (generate via ModelAdapter)
    ├── 4. Tool call loop (if tool_calls in response)
    │       ├── parse tool calls
    │       ├── execute via ToolRegistry
    │       └── feed results back to model
    ├── 5. Update history
    ├── 6. Summarize session → write to MemoryStore
    └── 7. Return response
```

## Module Details

### Tool Calling Protocol

```
LLM Output
    │
    ├── ```tool_call {"tool_name": "calculator", "arguments": {"expression": "3*7"}} ```
    │
    ▼
Tool.parse_tool_calls() → [ToolCall(tool_name="calculator", arguments={...})]
    │
    ▼
ToolRegistry.execute("calculator", expression="3*7") → ToolResult(success=True, output="21")
    │
    ▼
Result injected back into message context
```

### Memory System

4 categories stored in SQLite (`~/.lebotclaw/memory.db`):

- **student_profile**: Student attributes (grade, learning style, preferences)
- **learning_progress**: Learning trajectory (current chapter, errors, mastery)
- **session_summary**: Per-session outcomes (key points, tool results, follow-ups)
- **skill_memory**: Reusable teaching patterns

Recall strategy: query by `intent keywords + subject + tags`, rank by `relevance_score × access_count`.

### Planner

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

### Intent Router

Keyword-based classification into 7 intents:

1. `math_calculation` → math agent, innoSpark model, calculator tool
2. `text_creation` → chinese agent, qwen model
3. `knowledge_qa` → subject-specific agent, innoSpark model, knowledge tool
4. `learning_plan` → general agent, innoSpark model, timer tool
5. `emotional_support` → general agent, doubao model
6. `tool_call` → routed by specific tool
7. `multi_turn` / `general` → current agent, innoSpark model

Fallback: if primary model times out, automatically switches to backup model.

### Model Adapters

All adapters follow the OpenAI-compatible API pattern:

| Adapter | Base URL | Default Model | Env Key |
|---------|----------|---------------|---------|
| InnoSpark | `api.innospark.ai/v1` | innoSpark | `INNOSPARK_API_KEY` |
| Doubao | `ark.cn-beijing.volces.com/api/v3` | endpoint_id | `DOUBAO_API_KEY` + `DOUBAO_ENDPOINT_ID` |
| Qwen | `dashscope.aliyuncs.com/compatible-mode/v1` | qwen-plus | `QWEN_API_KEY` |
| DeepSeek | `api.deepseek.com/v1` | deepseek-chat | `DEEPSEEK_API_KEY` |

### Skill Library

Stored in JSON (`~/.lebotclaw/skills.json`). Skills are auto-extracted when:
- Plan completion rate > 80%
- Teaching effectiveness score > 0.7

Each skill contains: trigger scenario, applicable grades, recommended tools, step template, common Q&A handling.

### Assessment

3-dimensional evaluation:
- **Knowledge Accuracy** (0-1): Checks for factual markers and correctness
- **Interaction Naturalness** (0-1): Checks for guided questions, encouragement, step-by-step explanation
- **Personalization** (0-1): Checks for student profile references, difficulty adjustment

## CLI Commands

| Command | Description |
|---------|-------------|
| `/switch <agent>` | Switch to a different subject agent |
| `/agents` | List available agents |
| `/history` | Show recent conversation history |
| `/profile` | Display student profile |
| `/route_stats` | Show routing statistics |
| `/help` | Show available commands |
| `/quit` | Exit LebotClaw |

## File Layout

```
~/.lebotclaw/
├── memory.db          # SQLite database (memories + contexts)
├── skills.json        # Teaching skill library
└── history            # CLI command history
```
