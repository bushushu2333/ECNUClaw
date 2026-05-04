import sqlite3
import json
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, asdict
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


class MemoryStore:
    def __init__(self, db_path: Union[str, Path] = "~/.lebotclaw/memory.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_CREATE_MEMORIES_TABLE)
        self._conn.executescript(_CREATE_CONTEXTS_TABLE)
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
