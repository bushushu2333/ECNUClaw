from dataclasses import dataclass, field
import time

from lebotclaw.core.memory import LearnerProfile


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


@dataclass
class ProfileAssessment:
    cognitive_score: float = 0.0
    behavioral_score: float = 0.0
    emotional_score: float = 0.0
    metacognitive_score: float = 0.0
    overall_profile_score: float = 0.0
    feedback: str = ""
    details: dict = field(default_factory=dict)


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

_METACOGNITIVE_PHRASES = [
    "你是怎么想到的", "为什么这样想", "回顾一下", "总结一下",
    "你觉得哪种方法更好", "如果再遇到", "你发现了什么",
    "反思", "归纳", "比较一下",
]

_BLOOM_ASSESSMENT_KEYWORDS = {
    "remember": ["记得", "回忆", "背诵", "说出"],
    "understand": ["理解", "解释", "用自己的话", "什么意思"],
    "apply": ["运用", "计算", "解题", "做一题"],
    "analyze": ["分析", "比较", "区别", "分类"],
    "evaluate": ["评价", "判断", "哪个更好", "为什么对"],
    "create": ["设计", "创造", "编一道", "想一个"],
}


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

    def assess_profile(self, profile: LearnerProfile) -> ProfileAssessment:
        """评估学习者画像各维度的发展水平"""
        cognitive = self._assess_cognitive(profile)
        behavioral = self._assess_behavioral(profile)
        emotional = self._assess_emotional(profile)
        metacognitive = self._assess_metacognitive(profile)

        overall = round(
            cognitive * 0.30
            + behavioral * 0.20
            + emotional * 0.25
            + metacognitive * 0.25,
            3,
        )

        feedback_parts = []
        if cognitive >= 0.7:
            feedback_parts.append("认知水平发展良好，知识掌握扎实。")
        elif cognitive >= 0.4:
            feedback_parts.append("认知水平中等，建议加强薄弱知识点。")
        else:
            feedback_parts.append("认知水平偏低，需要系统回顾基础知识。")

        if emotional >= 0.6:
            feedback_parts.append("情感状态积极，学习动机充足。")
        elif emotional >= 0.35:
            feedback_parts.append("情感状态一般，建议增加鼓励和正向反馈。")
        else:
            feedback_parts.append("情感状态需要关注，学习自信心不足，需更多支持。")

        if metacognitive >= 0.6:
            feedback_parts.append("元认知能力发展良好，能主动反思和调节。")
        elif metacognitive >= 0.35:
            feedback_parts.append("元认知能力有待提升，建议引导更多反思性提问。")
        else:
            feedback_parts.append("元认知能力较弱，需要系统培养自我调节和反思习惯。")

        bloom_names = {
            "remember": "记忆", "understand": "理解", "apply": "应用",
            "analyze": "分析", "evaluate": "评价", "create": "创造",
        }
        mood_names = {
            "neutral": "平静", "confident": "自信", "curious": "好奇",
            "confused": "困惑", "frustrated": "受挫", "excited": "兴奋",
        }

        details = {
            "cognitive_score": round(cognitive, 3),
            "behavioral_score": round(behavioral, 3),
            "emotional_score": round(emotional, 3),
            "metacognitive_score": round(metacognitive, 3),
            "bloom_level": profile.cognitive.bloom_level,
            "bloom_level_cn": bloom_names.get(profile.cognitive.bloom_level, profile.cognitive.bloom_level),
            "current_mood": profile.emotional.current_mood,
            "current_mood_cn": mood_names.get(profile.emotional.current_mood, profile.emotional.current_mood),
            "weak_topics_count": sum(1 for v in profile.cognitive.knowledge_state.values() if v == "weak"),
            "total_sessions": profile.behavioral.total_sessions,
            "preferred_strategy": profile.metacognitive.preferred_strategy,
        }

        return ProfileAssessment(
            cognitive_score=round(cognitive, 3),
            behavioral_score=round(behavioral, 3),
            emotional_score=round(emotional, 3),
            metacognitive_score=round(metacognitive, 3),
            overall_profile_score=overall,
            feedback=" ".join(feedback_parts),
            details=details,
        )

    def generate_report(self, result: AssessmentResult) -> str:
        lines = [
            "========== ECNUClaw 教学评估报告 ==========",
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

    def generate_profile_report(self, pa: ProfileAssessment) -> str:
        """生成多维度学习报告"""
        d = pa.details
        lines = [
            "========== ECNUClaw 学习者画像评估报告 ==========",
            "",
            f"画像综合评分: {pa.overall_profile_score:.1%}",
            "",
            "【认知维度】" + " " + f"{pa.cognitive_score:.1%}",
            f"  布鲁姆认知水平: {d.get('bloom_level_cn', '未知')}",
            f"  薄弱知识点: {d.get('weak_topics_count', 0)} 个",
            "",
            "【行为维度】" + " " + f"{pa.behavioral_score:.1%}",
            f"  累计会话: {d.get('total_sessions', 0)} 次",
            "",
            "【情感维度】" + " " + f"{pa.emotional_score:.1%}",
            f"  当前状态: {d.get('current_mood_cn', '未知')}",
            "",
            "【元认知维度】" + " " + f"{pa.metacognitive_score:.1%}",
            f"  策略偏好: {d.get('preferred_strategy', '未知')}",
            "",
            f"综合反馈: {pa.feedback}",
            "",
            "=" * 48,
        ]
        return "\n".join(lines)

    def _assess_cognitive(self, profile: LearnerProfile) -> float:
        score = 0.3
        bloom_scores = {
            "remember": 0.2, "understand": 0.35, "apply": 0.5,
            "analyze": 0.65, "evaluate": 0.8, "create": 0.95,
        }
        score += bloom_scores.get(profile.cognitive.bloom_level, 0.2)

        mastered = sum(1 for v in profile.cognitive.knowledge_state.values() if v == "mastered")
        weak = sum(1 for v in profile.cognitive.knowledge_state.values() if v == "weak")
        total = max(len(profile.cognitive.knowledge_state), 1)
        knowledge_ratio = mastered / total
        score += knowledge_ratio * 0.3

        if profile.cognitive.prior_knowledge:
            score += min(len(profile.cognitive.prior_knowledge) * 0.02, 0.1)

        return max(0.0, min(1.0, score))

    def _assess_behavioral(self, profile: LearnerProfile) -> float:
        score = 0.2
        if profile.behavioral.total_sessions > 0:
            score += min(profile.behavioral.total_sessions * 0.05, 0.3)
        if profile.behavioral.question_frequency > 0:
            score += min(profile.behavioral.question_frequency * 0.2, 0.3)
        if profile.behavioral.total_questions > 0:
            score += min(profile.behavioral.total_questions * 0.02, 0.2)
        return max(0.0, min(1.0, score))

    def _assess_emotional(self, profile: LearnerProfile) -> float:
        score = profile.emotional.motivation_level * 0.4
        score += profile.emotional.self_efficacy * 0.4
        if profile.emotional.current_mood in ("confident", "excited", "curious"):
            score += 0.15
        elif profile.emotional.current_mood == "neutral":
            score += 0.05
        if profile.emotional.frustration_count > 3:
            score -= 0.1
        return max(0.0, min(1.0, score))

    def _assess_metacognitive(self, profile: LearnerProfile) -> float:
        score = profile.metacognitive.self_regulation * 0.4
        score += profile.metacognitive.reflection_ability * 0.4
        if profile.metacognitive.goal_setting:
            score += min(len(profile.metacognitive.goal_setting) * 0.05, 0.15)
        strategy_scores = {"guided": 0.3, "exploratory": 0.6, "collaborative": 0.5}
        score += strategy_scores.get(profile.metacognitive.preferred_strategy, 0.3) * 0.1
        return max(0.0, min(1.0, score))

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
