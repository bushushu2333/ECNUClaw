import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class Step:
    id: int
    title: str
    description: str = ""
    tools_needed: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: str = ""
    student_feedback: str = ""


@dataclass
class Plan:
    goal: str
    steps: List[Step]
    current_step_index: int = 0
    subject: str = "general"
    grade: str = ""


_REVIEW_TEMPLATE = [
    {"title": "知识点回顾", "description": "回顾相关的核心知识点，帮助学生建立认知基础"},
    {"title": "例题练习", "description": "通过典型例题巩固理解", "tools_needed": ["calculator"]},
    {"title": "错题巩固", "description": "针对常见错误进行针对性练习"},
    {"title": "总结", "description": "归纳复习要点，形成知识框架"},
]

_LEARN_TEMPLATE = [
    {"title": "概念引入", "description": "用生活化的例子引入新概念，激发兴趣"},
    {"title": "举例说明", "description": "通过多个具体例子帮助学生理解抽象概念"},
    {"title": "练习闯关", "description": "设计分层练习，从易到难逐步提升", "tools_needed": ["calculator"]},
    {"title": "检查理解", "description": "通过提问确认学生是否真正掌握了核心概念"},
    {"title": "拓展应用", "description": "将新知识应用到实际问题中，加深理解"},
]

_PRACTICE_TEMPLATE = [
    {"title": "题目分析", "description": "帮助学生理解题目要求和已知条件"},
    {"title": "分步解答", "description": "引导学生一步步完成解题过程"},
    {"title": "方法总结", "description": "总结解题思路和方法，形成可复用的策略"},
    {"title": "变式训练", "description": "提供变式题目，确保方法迁移能力"},
]

_WRITING_TEMPLATE = [
    {"title": "审题", "description": "分析题目要求，明确写作方向和要点"},
    {"title": "素材", "description": "帮助学生回忆和整理相关素材与经历"},
    {"title": "列提纲", "description": "梳理论述结构，确定段落安排"},
    {"title": "写作", "description": "根据提纲进行分段写作"},
    {"title": "修改", "description": "通读全文，从用词、句式、逻辑等方面进行修改提升"},
]

_GENERIC_TEMPLATE = [
    {"title": "目标确认", "description": "明确本次学习的具体目标和预期成果"},
    {"title": "知识准备", "description": "激活已有知识，为学习新内容做准备"},
    {"title": "实践", "description": "通过动手操作或练习来内化知识"},
    {"title": "检查", "description": "检验学习效果，发现遗漏"},
    {"title": "总结", "description": "梳理本次学习收获，形成完整认知"},
]


def _match_template(goal: str) -> List[Dict]:
    if any(kw in goal for kw in ("复习",)):
        return _REVIEW_TEMPLATE
    if any(kw in goal for kw in ("学", "了解", "新概念", "认识")):
        return _LEARN_TEMPLATE
    if any(kw in goal for kw in ("做题", "练习", "解题", "算")):
        return _PRACTICE_TEMPLATE
    if any(kw in goal for kw in ("作文", "写作", "写一篇")):
        return _WRITING_TEMPLATE
    return _GENERIC_TEMPLATE


def _build_steps(template: List[Dict]) -> List[Step]:
    steps = []
    for i, item in enumerate(template):
        steps.append(Step(
            id=i,
            title=item["title"],
            description=item.get("description", ""),
            tools_needed=item.get("tools_needed", []),
        ))
    return steps


class Planner:
    def __init__(self):
        self._templates: Dict[str, List[Dict]] = {
            "review": _REVIEW_TEMPLATE,
            "learn": _LEARN_TEMPLATE,
            "practice": _PRACTICE_TEMPLATE,
            "writing": _WRITING_TEMPLATE,
            "generic": _GENERIC_TEMPLATE,
        }

    def decompose(self, goal: str, subject: str = "", grade: str = "") -> Plan:
        template = _match_template(goal)
        steps = _build_steps(template)
        if steps:
            steps[0].status = StepStatus.IN_PROGRESS
        return Plan(
            goal=goal,
            steps=steps,
            subject=subject or "general",
            grade=grade,
        )

    def replan(self, plan: Plan, feedback: str) -> Plan:
        positive_words = ("对了", "正确", "懂了", "会了", "明白", "理解", "简单", "容易")
        negative_words = ("错了", "不会", "不懂", "不明白", "太难", "不理解", "听不懂")
        frustrated_words = ("太难了", "不想学", "放弃", "烦", "枯燥", "没意思")

        is_positive = any(w in feedback for w in positive_words)
        is_negative = any(w in feedback for w in negative_words)
        is_frustrated = any(w in feedback for w in frustrated_words)

        if is_frustrated:
            encourage_step = Step(
                id=len(plan.steps),
                title="鼓励与信心重建",
                description="先停下来，给予鼓励，用更简单的方式重新讲解",
                status=StepStatus.PENDING,
            )
            insert_idx = plan.current_step_index + 1
            plan.steps.insert(insert_idx, encourage_step)
            for i, step in enumerate(plan.steps):
                step.id = i

        elif is_negative:
            review_step = Step(
                id=len(plan.steps),
                title="回退：补充前置概念",
                description="学生出现理解困难，回退到基础概念重新讲解",
                status=StepStatus.PENDING,
            )
            insert_idx = plan.current_step_index + 1
            plan.steps.insert(insert_idx, review_step)
            for i, step in enumerate(plan.steps):
                step.id = i

        elif is_positive:
            remaining = [s for s in plan.steps[plan.current_step_index + 1:]
                         if s.status == StepStatus.PENDING]
            if len(remaining) >= 2:
                remaining[0].status = StepStatus.SKIPPED
                remaining[0].result = "学生掌握良好，跳过此步骤"

        return plan

    def get_current_step(self, plan: Plan) -> Optional[Step]:
        if 0 <= plan.current_step_index < len(plan.steps):
            return plan.steps[plan.current_step_index]
        return None

    def advance_step(self, plan: Plan, result: str = "", feedback: str = "") -> Plan:
        if 0 <= plan.current_step_index < len(plan.steps):
            current = plan.steps[plan.current_step_index]
            current.status = StepStatus.COMPLETED
            current.result = result
            current.student_feedback = feedback
            plan.current_step_index += 1
            if plan.current_step_index < len(plan.steps):
                plan.steps[plan.current_step_index].status = StepStatus.IN_PROGRESS
        return plan

    def get_progress(self, plan: Plan) -> Dict:
        total = len(plan.steps)
        completed = sum(1 for s in plan.steps if s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED))
        remaining = total - completed
        return {
            "goal": plan.goal,
            "total_steps": total,
            "completed_steps": completed,
            "remaining_steps": remaining,
            "completion_rate": round(completed / total, 2) if total > 0 else 0.0,
            "current_step": (
                plan.steps[plan.current_step_index].title
                if plan.current_step_index < total else "已完成"
            ),
        }
