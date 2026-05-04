import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Union, List, Dict


@dataclass
class TeachingSkill:
    id: Optional[int] = None
    name: str = ""
    trigger_scenario: str = ""
    applicable_grades: List[str] = field(default_factory=list)
    subject: str = ""
    recommended_tools: List[str] = field(default_factory=list)
    steps_template: List[Dict] = field(default_factory=list)
    common_questions: List[Dict] = field(default_factory=list)
    effectiveness_score: float = 0.0
    usage_count: int = 0
    created_at: float = 0.0
    source_session: str = ""


class SkillLibrary:
    def __init__(self, store_path: Union[str, Path] = "~/.lebotclaw/skills.json"):
        self.store_path = Path(store_path).expanduser()
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._skills: List[Dict] = []
        self._next_id = 1
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text(encoding="utf-8"))
                self._skills = data.get("skills", [])
                self._next_id = data.get("next_id", 1)
            except (json.JSONDecodeError, OSError):
                self._skills = []
                self._next_id = 1

    def _save(self):
        self.store_path.write_text(
            json.dumps({"skills": self._skills, "next_id": self._next_id}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_skill(self, skill: TeachingSkill) -> int:
        skill.id = self._next_id
        self._next_id += 1
        if not skill.created_at:
            skill.created_at = time.time()
        self._skills.append(asdict(skill))
        self._save()
        return skill.id

    def find_skill(
        self,
        scenario: str = "",
        subject: str = "",
        grade: str = "",
    ) -> List[TeachingSkill]:
        results = []
        for raw in self._skills:
            s = TeachingSkill(**raw)
            if subject and s.subject and s.subject != subject:
                continue
            if grade and s.applicable_grades and grade not in s.applicable_grades:
                continue
            if scenario:
                scenario_lower = scenario.lower()
                match_name = scenario_lower in s.name.lower()
                match_trigger = scenario_lower in s.trigger_scenario.lower()
                name_words = any(w in s.name for w in scenario.split() if len(w) > 1)
                trigger_words = any(w in s.trigger_scenario for w in scenario.split() if len(w) > 1)
                if not (match_name or match_trigger or name_words or trigger_words):
                    continue
            results.append(s)

        results.sort(key=lambda x: x.effectiveness_score * (x.usage_count + 1), reverse=True)
        return results

    def update_effectiveness(self, skill_id: int, score: float) -> None:
        for raw in self._skills:
            if raw["id"] == skill_id:
                old_score = raw["effectiveness_score"]
                old_count = raw["usage_count"]
                raw["usage_count"] = old_count + 1
                raw["effectiveness_score"] = round(
                    (old_score * old_count + score) / (old_count + 1), 2
                )
                self._save()
                return

    def auto_extract_skill(
        self,
        plan,
        session_summary: str,
        effectiveness: float,
    ) -> Optional[TeachingSkill]:
        total = len(plan.steps)
        completed = sum(1 for s in plan.steps if s.status.value in ("completed", "skipped"))
        completion_rate = round(completed / total, 2) if total > 0 else 0.0
        if completion_rate <= 0.8 or effectiveness <= 0.7:
            return None

        completed_steps = []
        for step in plan.steps:
            if step.status.value in ("completed", "skipped"):
                completed_steps.append({
                    "title": step.title,
                    "prompt_hint": step.description,
                    "result": step.result[:200] if step.result else "",
                })

        if not completed_steps:
            return None

        skill = TeachingSkill(
            name=f"自动提取: {plan.goal[:30]}",
            trigger_scenario=session_summary[:200] if session_summary else plan.goal,
            applicable_grades=[plan.grade] if plan.grade else [],
            subject=plan.subject,
            steps_template=completed_steps,
            effectiveness_score=effectiveness,
            usage_count=1,
            created_at=time.time(),
        )
        self.add_skill(skill)
        return skill

    def list_skills(self, subject: str = "") -> List[TeachingSkill]:
        results = []
        for raw in self._skills:
            if subject and raw.get("subject") != subject:
                continue
            results.append(TeachingSkill(**raw))
        results.sort(key=lambda x: x.usage_count, reverse=True)
        return results
