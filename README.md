# ECNUClaw

**A Safe, Low-Barrier Intelligent Study Companion Framework for K-12 Education**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 67 passed](https://img.shields.io/badge/Tests-67%20passed-brightgreen.svg)](tests/)
[![arXiv](https://img.shields.io/badge/arXiv-2026.xxxxx-b31b1b.svg)](https://arxiv.org/)

> East China Normal University · Shanghai Institute of AI Education · AI Education Laboratory

ECNUClaw is an open-source intelligent study companion framework that integrates personalized learning theory, learner profiling, and Socratic pedagogy into a safe, low-barrier CLI-based agent system for K-12 students.

---

## Core Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Personalized Learning** | Learner profile construction, adaptive scaffolding, dynamic difficulty adjustment based on individual progress |
| **Educational Safety** | Topic boundary enforcement, content filtering, age-appropriate responses — conversations stay within learning domains |
| **Intelligent Companionship** | Socratic questioning (not direct answers), persistent memory across sessions, warm and encouraging tone |
| **Low-Barrier Access** | 4-step setup wizard, all-native-language interface, zero technical knowledge required |

## Theoretical Foundations

ECNUClaw is grounded in three theoretical pillars:

1. **Personalized Learning & Learner Profiling** — Constructs and maintains multi-dimensional learner profiles (knowledge state, learning style, cognitive level, emotional state) to drive adaptive instruction, informed by Prof. Zhi Zhang's framework for AI-enabled personalized education.

2. **Socratic Pedagogy** — The HEADS prompt template system encodes Socratic questioning strategies: never giving direct answers, but guiding students to discover knowledge through structured questioning, aligned with the Zone of Proximal Development.

3. **Intelligent Tutoring Systems (ITS)** — Builds on decades of ITS research, translating principles of adaptive scaffolding, formative assessment, and mastery learning into LLM-native architecture.

## Architecture

```
┌──────────────────────────────────────────────────┐
│            CLI Interface (Setup Wizard)           │
├──────────────────────────────────────────────────┤
│           Intent Router (Auto Classification)     │
├──────────────────────────────────────────────────┤
│  Math Companion │ Chinese │ Science │ General     │
│     (Agent)     │ Agent   │ Agent   │ Agent       │
├──────────────────────────────────────────────────┤
│  Tool Calling (Calculator + Dictionary + KB + Timer)│
├──────────────────────────────────────────────────┤
│  Learner Profile │ Learning Progress │ Skills     │
│  (SQLite-backed Persistent Education Memory)      │
├──────────────────────────────────────────────────┤
│  HEADS Prompt Templates │ Assessment Module       │
└──────────────────────────────────────────────────┘
```

## Quick Start

```bash
pip install ecnucleaw
ecnucleaw
```

The setup wizard will guide you through: model selection → dialogue style → detail level → student profile.

## Learner Profile System

ECNUClaw maintains a 4-category learner profile that evolves across sessions:

| Category | What It Tracks | Example |
|----------|---------------|---------|
| **Student Profile** | Demographics, preferences, goals | Grade, learning style, favorite subjects |
| **Learning Progress** | Knowledge state, weak points, trajectories | Error patterns, current topic mastery |
| **Session Summary** | Per-session outcomes | Topics covered, questions asked, outcomes |
| **Skill Memory** | Successful teaching patterns | Effective explanations, reusable templates |

## Evaluation

The built-in Assessment Module evaluates companion interactions across three dimensions:

- **Knowledge Accuracy**: Is the information correct?
- **Interaction Naturalness**: Is the conversation pedagogically appropriate?
- **Personalization**: Is the response adapted to this specific learner?

## Citation

If you use ECNUClaw in your research, please cite:

```bibtex
@article{zhou2026ecnucleaw,
  title={ECNUClaw: A Safe, Low-Barrier Intelligent Study Companion Framework for K-12 Education},
  author={Zhou, Yizhou and Li, Jiayin and Zhang, Zhi},
  journal={arXiv preprint arXiv:2026.xxxxx},
  year={2026}
}
```

## Authors

- **Yizhou Zhou** — East China Normal University, Shanghai Institute of AI Education
- **Jiayin Li** — East China Normal University, Faculty of Education
- **Zhi Zhang** (Corresponding) — East China Normal University, Shanghai Institute of AI Education

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*East China Normal University · Shanghai Institute of AI Education · AI Education Laboratory · 2026*
