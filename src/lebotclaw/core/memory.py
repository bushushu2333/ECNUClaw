import sqlite3
import json
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Union, List, Dict


@dataclass
class MemoryEntry:
    id: Optional[int] = None
    category: str = ""
    subject: str = ""
    key: str = ""
    content: str = ""
    tags: str = ""
    relevance_score: float = 0.0
    created_at: float = 0.0
    updated_at: float = 0.0
    access_count: int = 0


# ── 学习者画像 5 维数据结构（张治「数字画像三层框架」） ──

@dataclass
class CognitiveDimension:
    knowledge_state: Dict[str, str] = field(default_factory=dict)
    bloom_level: str = "remember"
    prior_knowledge: List[str] = field(default_factory=list)
    knowledge_tracing: Dict[str, float] = field(default_factory=dict)


@dataclass
class BehavioralDimension:
    question_frequency: float = 0.0
    avg_session_duration: float = 0.0
    tool_usage: Dict[str, int] = field(default_factory=dict)
    interaction_patterns: List[str] = field(default_factory=list)
    total_sessions: int = 0
    total_questions: int = 0


@dataclass
class EmotionalDimension:
    current_mood: str = "neutral"
    motivation_level: float = 0.5
    self_efficacy: float = 0.5
    frustration_count: int = 0
    engagement_signals: List[str] = field(default_factory=list)


@dataclass
class MetacognitiveDimension:
    self_regulation: float = 0.5
    preferred_strategy: str = "guided"
    reflection_ability: float = 0.5
    goal_setting: List[str] = field(default_factory=list)


@dataclass
class ContextualDimension:
    grade: str = ""
    learning_environment: str = "home"
    time_preference: str = ""
    subject_focus: str = ""
    learning_goal: str = ""


@dataclass
class LearnerProfile:
    cognitive: CognitiveDimension = field(default_factory=CognitiveDimension)
    behavioral: BehavioralDimension = field(default_factory=BehavioralDimension)
    emotional: EmotionalDimension = field(default_factory=EmotionalDimension)
    metacognitive: MetacognitiveDimension = field(default_factory=MetacognitiveDimension)
    contextual: ContextualDimension = field(default_factory=ContextualDimension)
    updated_at: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LearnerProfile":
        if not data:
            return cls()
        cognitive = CognitiveDimension(**data.get("cognitive", {}))
        behavioral = BehavioralDimension(**data.get("behavioral", {}))
        emotional = EmotionalDimension(**data.get("emotional", {}))
        metacognitive = MetacognitiveDimension(**data.get("metacognitive", {}))
        contextual = ContextualDimension(**data.get("contextual", {}))
        return cls(
            cognitive=cognitive,
            behavioral=behavioral,
            emotional=emotional,
            metacognitive=metacognitive,
            contextual=contextual,
            updated_at=data.get("updated_at", 0.0),
        )


# ── 画像信号提取用的标记词 ──

_FRUSTRATION_MARKERS = ["错", "不对", "不会", "不懂", "没学过", "忘记了", "太难了", "烦", "放弃"]
_ENGAGEMENT_MARKERS = ["明白了", "懂了", "原来如此", "谢谢", "我会了", "有趣", "还想学"]
_REFLECTION_MARKERS = ["我想想", "让我思考", "回顾一下", "总结", "我觉得", "我发现"]
_STRATEGY_MARKERS = {
    "guided": ["教我", "帮我", "提示", "引导"],
    "exploratory": ["试试", "自己来", "探索", "实验"],
    "collaborative": ["一起", "讨论", "商量"],
}

_BLOOM_KEYWORDS = {
    "remember": ["什么是", "定义", "叫什么", "回忆"],
    "understand": ["为什么", "解释", "说明", "理解", "什么意思"],
    "apply": ["怎么做", "计算", "运用", "解题", "练习"],
    "analyze": ["比较", "分析", "区别", "关系", "分类"],
    "evaluate": ["判断", "评价", "哪个好", "对不对", "是否合理"],
    "create": ["设计", "创造", "写一个", "发明", "提出"],
}

_MOOD_KEYWORDS = {
    "confident": ["太简单", "已经会了", "这个我知道"],
    "curious": ["为什么", "怎么回事", "好奇", "有趣"],
    "confused": ["不明白", "不懂", "什么意思", "搞不清"],
    "frustrated": _FRUSTRATION_MARKERS,
    "excited": ["太棒了", "厉害", "好玩", "有趣"],
}


_CREATE_MEMORIES_TABLE = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    subject TEXT NOT NULL DEFAULT 'general',
    key TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT DEFAULT '',
    relevance_score REAL DEFAULT 0.0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    access_count INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
CREATE INDEX IF NOT EXISTS idx_memories_subject ON memories(subject);
CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);
"""

_CREATE_CONTEXTS_TABLE = """
CREATE TABLE IF NOT EXISTS contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_id TEXT UNIQUE NOT NULL,
    agent_name TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""

_CREATE_PROFILE_TABLE = """
CREATE TABLE IF NOT EXISTS learner_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dimension TEXT NOT NULL UNIQUE,
    data TEXT NOT NULL,
    updated_at REAL NOT NULL
);
"""


class MemoryStore:
    def __init__(self, db_path: Union[str, Path] = "~/.lebotclaw/memory.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_CREATE_MEMORIES_TABLE)
        self._conn.executescript(_CREATE_CONTEXTS_TABLE)
        self._conn.executescript(_CREATE_PROFILE_TABLE)
        self._conn.commit()

    def save_memory(
        self,
        category: str,
        subject: str,
        key: str,
        content: Union[str, dict],
        tags: List[str] = None,
    ) -> int:
        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        tags_str = ",".join(tags) if tags else ""
        now = time.time()
        cur = self._conn.execute(
            """INSERT INTO memories (category, subject, key, content, tags, relevance_score, created_at, updated_at, access_count)
               VALUES (?, ?, ?, ?, ?, 1.0, ?, ?, 0)""",
            (category, subject, key, content, tags_str, now, now),
        )
        self._conn.commit()
        return cur.lastrowid

    def search_memory(
        self,
        query: str = "",
        category: str = "",
        subject: str = "",
        tags: List[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        conditions = []
        params: list = []

        if query:
            conditions.append("(key LIKE ? OR content LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        if category:
            conditions.append("category = ?")
            params.append(category)
        if subject:
            conditions.append("subject = ?")
            params.append(subject)
        if tags:
            tag_conds = []
            for tag in tags:
                tag_conds.append("tags LIKE ?")
                params.append(f"%{tag}%")
            conditions.append(f"({' OR '.join(tag_conds)})")

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM memories WHERE {where} ORDER BY (relevance_score * (access_count + 1)) DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def summarize_session(self, messages: List[dict]) -> str:
        if not messages:
            return ""

        summaries = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if not content:
                continue

            if role == "user":
                if "?" in content or "？" in content:
                    self.save_memory(
                        "session_summary", "general",
                        f"学生提问: {content[:50]}",
                        {"question": content, "type": "student_question"},
                        ["提问"],
                    )
                    summaries.append(f"学生提问: {content[:100]}")

                wrong_markers = ["错", "不对", "不会", "不懂", "没学过", "忘记了"]
                if any(m in content for m in wrong_markers):
                    self.save_memory(
                        "learning_progress", "general",
                        f"错题/薄弱点: {content[:50]}",
                        {"issue": content, "type": "weakness"},
                        ["错题", "薄弱"],
                    )
                    summaries.append(f"发现薄弱点: {content[:100]}")

            elif role == "assistant":
                knowledge_markers = ["定义", "概念", "公式", "定理", "原理", "方法", "规律", "规则"]
                if any(m in content for m in knowledge_markers):
                    self.save_memory(
                        "skill_memory", "general",
                        f"知识点讲解: {content[:50]}",
                        {"explanation": content[:500], "type": "knowledge"},
                        ["知识点"],
                    )
                    summaries.append(f"讲解知识点: {content[:100]}")

        if summaries:
            summary_text = "\n".join(f"- {s}" for s in summaries)
            self.save_memory(
                "session_summary", "general",
                "会话摘要",
                {"summaries": summaries, "message_count": len(messages)},
                ["摘要"],
            )
            return summary_text
        return "本会话未提取到显著教育记忆。"

    def freeze_context(self, agent_name: str, current_context: Dict) -> str:
        context_id = str(uuid.uuid4())
        now = time.time()
        self._conn.execute(
            "INSERT INTO contexts (context_id, agent_name, data, created_at) VALUES (?, ?, ?, ?)",
            (context_id, agent_name, json.dumps(current_context, ensure_ascii=False, default=str), now),
        )
        self._conn.commit()
        return context_id

    def restore_context(self, context_id: str) -> Dict:
        row = self._conn.execute(
            "SELECT * FROM contexts WHERE context_id = ?", (context_id,)
        ).fetchone()
        if not row:
            return {}
        return {"agent_name": row["agent_name"], "data": json.loads(row["data"]), "created_at": row["created_at"]}

    def get_student_profile(self) -> Dict:
        rows = self._conn.execute(
            "SELECT * FROM memories WHERE category = 'student_profile' ORDER BY updated_at DESC"
        ).fetchall()
        profile = {}
        for row in rows:
            key = row["key"]
            try:
                value = json.loads(row["content"])
            except (json.JSONDecodeError, TypeError):
                value = row["content"]
            profile[key] = value
        return profile

    # ── 学习者画像方法 ──

    def get_learner_profile(self) -> LearnerProfile:
        rows = self._conn.execute(
            "SELECT dimension, data FROM learner_profile"
        ).fetchall()
        if not rows:
            return self._migrate_profile_from_student_profile()
        dims = {}
        for row in rows:
            dims[row["dimension"]] = json.loads(row["data"])
        return LearnerProfile.from_dict(dims)

    def save_learner_profile(self, profile: LearnerProfile) -> None:
        now = time.time()
        profile.updated_at = now
        d = profile.to_dict()
        for dim_name, dim_data in d.items():
            if dim_name == "updated_at":
                continue
            self._conn.execute(
                """INSERT INTO learner_profile (dimension, data, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(dimension) DO UPDATE SET data=?, updated_at=?""",
                (dim_name, json.dumps(dim_data, ensure_ascii=False), now,
                 json.dumps(dim_data, ensure_ascii=False), now),
            )
        self._conn.commit()

    def update_profile_from_interaction(self, messages: List[dict]) -> LearnerProfile:
        profile = self.get_learner_profile()

        user_msgs = [m.get("content", "") for m in messages if m.get("role") == "user"]
        all_user_text = " ".join(user_msgs)

        # 认知维度：布鲁姆分类 + 知识追踪
        for level, keywords in _BLOOM_KEYWORDS.items():
            if any(kw in all_user_text for kw in keywords):
                profile.cognitive.bloom_level = level
                break

        weakness_topics = []
        for msg in user_msgs:
            if any(m in msg for m in _FRUSTRATION_MARKERS):
                topic = msg[:30]
                weakness_topics.append(topic)
                profile.cognitive.knowledge_state[topic] = "weak"
        for topic in weakness_topics:
            old_score = profile.cognitive.knowledge_tracing.get(topic, 0.5)
            profile.cognitive.knowledge_tracing[topic] = max(0.0, old_score - 0.1)

        # 行为维度
        profile.behavioral.total_sessions += 1
        question_count = sum(1 for m in user_msgs if "?" in m or "？" in m)
        profile.behavioral.total_questions += question_count
        total = profile.behavioral.total_sessions
        profile.behavioral.question_frequency = (
            profile.behavioral.total_questions / total if total > 0 else 0.0
        )

        # 情感维度
        for mood, keywords in _MOOD_KEYWORDS.items():
            if any(kw in all_user_text for kw in keywords):
                profile.emotional.current_mood = mood
                break

        frustration_count = sum(1 for m in user_msgs if any(kw in m for kw in _FRUSTRATION_MARKERS))
        profile.emotional.frustration_count += frustration_count
        if frustration_count > 0:
            profile.emotional.self_efficacy = max(0.1, profile.emotional.self_efficacy - 0.05)

        for marker in _ENGAGEMENT_MARKERS:
            if marker in all_user_text:
                if marker not in profile.emotional.engagement_signals:
                    profile.emotional.engagement_signals.append(marker)
                profile.emotional.motivation_level = min(1.0, profile.emotional.motivation_level + 0.05)

        # 元认知维度
        for marker in _REFLECTION_MARKERS:
            if marker in all_user_text:
                profile.metacognitive.reflection_ability = min(1.0, profile.metacognitive.reflection_ability + 0.03)
                break

        for strategy, keywords in _STRATEGY_MARKERS.items():
            if any(kw in all_user_text for kw in keywords):
                profile.metacognitive.preferred_strategy = strategy
                break

        # 情境维度：从 student_profile 迁移的数据
        sp = self.get_student_profile()
        if sp:
            if "年级" in sp and not profile.contextual.grade:
                profile.contextual.grade = str(sp["年级"])
            if "年级" in sp:
                profile.contextual.grade = str(sp["年级"])
            if "学习目标" in sp:
                profile.contextual.learning_goal = str(sp["学习目标"])
            if "喜欢科目" in sp:
                profile.contextual.subject_focus = str(sp["喜欢科目"])

        self.save_learner_profile(profile)
        return profile

    def get_learner_summary(self) -> str:
        profile = self.get_learner_profile()
        c = profile.cognitive
        b = profile.behavioral
        e = profile.emotional
        m = profile.metacognitive
        ctx = profile.contextual

        bloom_names = {
            "remember": "记忆", "understand": "理解", "apply": "应用",
            "analyze": "分析", "evaluate": "评价", "create": "创造",
        }
        mood_names = {
            "neutral": "平静", "confident": "自信", "curious": "好奇",
            "confused": "困惑", "frustrated": "受挫", "excited": "兴奋",
        }

        weak_topics = [k for k, v in c.knowledge_state.items() if v == "weak"]
        strong_topics = [k for k, v in c.knowledge_state.items() if v == "mastered"]

        lines = [
            f"【学习者画像摘要】",
            f"情境：{ctx.grade or '未知年级'} | 专注科目：{ctx.subject_focus or '未设定'} | 目标：{ctx.learning_goal or '未设定'}",
            f"认知：布鲁姆「{bloom_names.get(c.bloom_level, c.bloom_level)}」水平 | 薄弱点 {len(weak_topics)} 个 | 已掌握 {len(strong_topics)} 个",
            f"行为：累计 {b.total_sessions} 次会话 | 提问 {b.total_questions} 次 | 平均提问频率 {b.question_frequency:.1f}",
            f"情感：当前「{mood_names.get(e.current_mood, e.current_mood)}」| 动机 {e.motivation_level:.0%} | 自我效能 {e.self_efficacy:.0%} | 累计受挫 {e.frustration_count} 次",
            f"元认知：策略偏好「{m.preferred_strategy}」| 自我调节 {m.self_regulation:.0%} | 反思能力 {m.reflection_ability:.0%}",
        ]
        return "\n".join(lines)

    def _migrate_profile_from_student_profile(self) -> LearnerProfile:
        sp = self.get_student_profile()
        profile = LearnerProfile()
        if sp:
            if "年级" in sp:
                profile.contextual.grade = str(sp["年级"])
            if "学习目标" in sp:
                profile.contextual.learning_goal = str(sp["学习目标"])
            if "喜欢科目" in sp:
                profile.contextual.subject_focus = str(sp["喜欢科目"])
            self.save_learner_profile(profile)
        return profile

    def update_access(self, memory_id: int) -> None:
        now = time.time()
        self._conn.execute(
            "UPDATE memories SET access_count = access_count + 1, updated_at = ? WHERE id = ?",
            (now, memory_id),
        )
        self._conn.commit()

    def cleanup_old(self, days: int = 90) -> int:
        cutoff = time.time() - days * 86400
        cur = self._conn.execute(
            "DELETE FROM memories WHERE updated_at < ? AND access_count < 2 AND relevance_score < 0.5",
            (cutoff,),
        )
        self._conn.commit()
        return cur.rowcount

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            id=row["id"],
            category=row["category"],
            subject=row["subject"],
            key=row["key"],
            content=row["content"],
            tags=row["tags"],
            relevance_score=row["relevance_score"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            access_count=row["access_count"],
        )
