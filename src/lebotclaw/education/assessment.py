from dataclasses import dataclass, field
import time


@dataclass
class AssessmentResult:
    knowledge_accuracy: float = 0.0
    interaction_naturalness: float = 0.0
    personalization: float = 0.0
    overall_score: float = 0.0
    feedback: str = ""
    details: dict = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


_GUIDING_PHRASES = [
    "你觉得", "你是怎么想的", "试试看", "想一想", "第一步",
    "第二步", "接下来", "为什么呢", "能不能", "有没有其他方法",
    "提示一下", "换个角度", "联想一下", "回忆一下",
]

_ENCOURAGEMENT_PHRASES = [
    "很好", "不错", "棒", "聪明", "正确", "对了", "有进步",
    "继续", "加油", "很好", "太棒了", "非常好", "很接近了",
    "没关系", "再试试", "不要怕", "大胆",
]

_STEP_PHRASES = [
    "首先", "然后", "接着", "最后", "第一步", "第二步", "第三步",
    "我们分", "来看一下", "接下来我们",
]

_ERROR_MARKERS = [
    "错误答案:", "答案是错的", "不对，", "其实不是",
]


class AssessmentModule:

    def assess_interaction(
        self,
        messages: list[dict],
        student_profile: dict = None,
    ) -> AssessmentResult:
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
        user_msgs = [m for m in messages if m.get("role") == "user"]

        if not assistant_msgs:
            return AssessmentResult(
                feedback="没有助手回复可供评估。",
                details={"message_count": len(messages)},
            )

        all_assistant_text = "\n".join(m.get("content", "") for m in assistant_msgs)

        knowledge_accuracy = self._score_knowledge_accuracy(all_assistant_text)
        interaction_naturalness = self._score_interaction_naturalness(all_assistant_text)
        personalization = self._score_personalization(
            all_assistant_text, student_profile
        )

        overall = round(
            knowledge_accuracy * 0.35
            + interaction_naturalness * 0.35
            + personalization * 0.30,
            3,
        )

        details = {
            "assistant_message_count": len(assistant_msgs),
            "user_message_count": len(user_msgs),
            "total_chars": len(all_assistant_text),
            "knowledge_accuracy_raw": knowledge_accuracy,
            "interaction_naturalness_raw": interaction_naturalness,
            "personalization_raw": personalization,
        }

        feedback_parts = []
        if knowledge_accuracy >= 0.8:
            feedback_parts.append("知识讲解准确、清晰。")
        elif knowledge_accuracy >= 0.5:
            feedback_parts.append("知识讲解基本准确，但可以更清晰。")
        else:
            feedback_parts.append("知识讲解有待改进，存在不确定内容。")

        if interaction_naturalness >= 0.8:
            feedback_parts.append("交互自然度高，有良好的引导和鼓励。")
        elif interaction_naturalness >= 0.5:
            feedback_parts.append("交互基本自然，建议增加更多引导性提问。")
        else:
            feedback_parts.append("交互较为生硬，建议多用引导式提问和鼓励。")

        if personalization >= 0.7:
            feedback_parts.append("个性化适配良好，能根据学生情况调整。")
        elif personalization >= 0.4:
            feedback_parts.append("有一定个性化，建议更充分利用学生画像。")
        else:
            feedback_parts.append("个性化不足，建议参考学生的历史学习记录。")

        return AssessmentResult(
            knowledge_accuracy=round(knowledge_accuracy, 3),
            interaction_naturalness=round(interaction_naturalness, 3),
            personalization=round(personalization, 3),
            overall_score=overall,
            feedback=" ".join(feedback_parts),
            details=details,
        )

    def assess_session(
        self,
        session_messages: list[dict],
        plan=None,
    ) -> AssessmentResult:
        interaction_result = self.assess_interaction(session_messages)

        plan_completion = 0.0
        if plan:
            total_steps = len(plan.steps)
            if total_steps > 0:
                completed = sum(
                    1 for s in plan.steps
                    if s.status.value in ("completed", "skipped")
                )
                plan_completion = completed / total_steps

        overall = interaction_result.overall_score
        if plan:
            overall = round(overall * 0.7 + plan_completion * 0.3, 3)

        details = {**interaction_result.details, "plan_completion": plan_completion}

        return AssessmentResult(
            knowledge_accuracy=interaction_result.knowledge_accuracy,
            interaction_naturalness=interaction_result.interaction_naturalness,
            personalization=interaction_result.personalization,
            overall_score=overall,
            feedback=interaction_result.feedback,
            details=details,
        )

    def generate_report(self, result: AssessmentResult) -> str:
        lines = [
            "========== LebotClaw 教学评估报告 ==========",
            "",
            f"综合评分: {result.overall_score:.1%}",
            f"知识准确性: {result.knowledge_accuracy:.1%}",
            f"交互自然度: {result.interaction_naturalness:.1%}",
            f"个性化适配: {result.personalization:.1%}",
            "",
            f"评估反馈: {result.feedback}",
        ]

        if result.details:
            lines.append("")
            lines.append("--- 详细指标 ---")
            for k, v in result.details.items():
                if isinstance(v, float):
                    lines.append(f"  {k}: {v:.3f}")
                else:
                    lines.append(f"  {k}: {v}")

        lines.append("")
        lines.append("=" * 44)
        return "\n".join(lines)

    def _score_knowledge_accuracy(self, text: str) -> float:
        score = 0.7

        for marker in _ERROR_MARKERS:
            if marker in text:
                score -= 0.15
                break

        explanation_markers = ["因为", "所以", "由于", "因此", "也就是说", "换句话说", "举例来说"]
        explanation_count = sum(1 for m in explanation_markers if m in text)
        score += min(explanation_count * 0.05, 0.15)

        if "定义" in text or "概念" in text:
            score += 0.05
        if "公式" in text and "=" in text:
            score += 0.05

        return max(0.0, min(1.0, score))

    def _score_interaction_naturalness(self, text: str) -> float:
        score = 0.3

        guiding_count = sum(1 for p in _GUIDING_PHRASES if p in text)
        score += min(guiding_count * 0.1, 0.3)

        encourage_count = sum(1 for p in _ENCOURAGEMENT_PHRASES if p in text)
        score += min(encourage_count * 0.08, 0.2)

        step_count = sum(1 for p in _STEP_PHRASES if p in text)
        score += min(step_count * 0.05, 0.15)

        question_marks = text.count("？") + text.count("?")
        score += min(question_marks * 0.03, 0.1)

        return max(0.0, min(1.0, score))

    def _score_personalization(self, text: str, student_profile: dict = None) -> float:
        score = 0.4

        if student_profile:
            profile_keys_used = 0
            for key, value in student_profile.items():
                val_str = str(value)
                words = val_str.split()
                for word in words:
                    if len(word) >= 2 and word in text:
                        profile_keys_used += 1
                        break
            if student_profile:
                ratio = profile_keys_used / max(len(student_profile), 1)
                score += min(ratio * 0.3, 0.3)

        adaptation_phrases = [
            "根据你的", "你之前", "上次", "还记得吗", "我们之前",
            "按照你的水平", "对你来说", "你觉得难吗", "太快了吗",
        ]
        adaptation_count = sum(1 for p in adaptation_phrases if p in text)
        score += min(adaptation_count * 0.08, 0.2)

        return max(0.0, min(1.0, score))
