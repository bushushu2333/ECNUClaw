from enum import Enum
from dataclasses import dataclass
import re
import time


class IntentCategory(str, Enum):
    MATH_CALCULATION = "math_calculation"
    TEXT_CREATION = "text_creation"
    KNOWLEDGE_QA = "knowledge_qa"
    LEARNING_PLAN = "learning_plan"
    EMOTIONAL_SUPPORT = "emotional_support"
    TOOL_CALL = "tool_call"
    MULTI_TURN = "multi_turn"
    GENERAL = "general"


@dataclass
class RoutingDecision:
    intent: IntentCategory
    target_agent: str
    target_model: str
    use_tools: list[str]
    confidence: float
    reasoning: str

    def to_dict(self) -> dict:
        return {
            "intent": self.intent.value,
            "target_agent": self.target_agent,
            "target_model": self.target_model,
            "use_tools": self.use_tools,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


_SUBJECT_KEYWORDS = {
    "math": ["数学", "算", "几何", "代数", "方程", "函数", "三角", "概率", "统计", "数列"],
    "chinese": ["语文", "作文", "阅读", "写作", "古诗", "文言文", "汉字", "拼音", "修辞"],
    "science": ["科学", "物理", "化学", "生物", "实验", "地球", "生态", "力", "电", "磁", "水", "光", "热", "植物", "动物", "太阳", "磁铁"],
}


def _detect_subject(text: str) -> str:
    scores = {}
    for subject, keywords in _SUBJECT_KEYWORDS.items():
        scores[subject] = sum(1 for kw in keywords if kw in text)
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return "general"
    return best


class IntentRouter:

    def __init__(self):
        self._route_log: list[dict] = []
        self._keyword_rules = {
            IntentCategory.MATH_CALCULATION: [
                r"计算|等于|加减|乘除|方程|几何|角度|面积|周长|体积|分数|小数|百分比",
                r"\d+\s*[+\-*/×÷]\s*\d+",
            ],
            IntentCategory.TEXT_CREATION: [
                r"作文|写作|写一篇文章|日记|读后感|续写|扩写|缩写",
            ],
            IntentCategory.KNOWLEDGE_QA: [
                r"什么是|为什么|怎么回事|解释|定义|原理|概念|意思",
            ],
            IntentCategory.LEARNING_PLAN: [
                r"复习|学习计划|帮我安排|制定计划|备考|预习|学习路线",
            ],
            IntentCategory.EMOTIONAL_SUPPORT: [
                r"不开心|害怕|焦虑|紧张|压力大|讨厌|烦|难过|伤心|害怕考试",
            ],
            IntentCategory.TOOL_CALL: [
                r"计时|番茄钟|查字典|查词|查知识点",
            ],
        }
        self._priority = [
            IntentCategory.EMOTIONAL_SUPPORT,
            IntentCategory.TOOL_CALL,
            IntentCategory.MATH_CALCULATION,
            IntentCategory.TEXT_CREATION,
            IntentCategory.LEARNING_PLAN,
            IntentCategory.KNOWLEDGE_QA,
            IntentCategory.MULTI_TURN,
            IntentCategory.GENERAL,
        ]

    def classify(self, user_input: str, context: dict = None) -> RoutingDecision:
        scores: dict[IntentCategory, float] = {cat: 0.0 for cat in IntentCategory}
        matched_rules: dict[IntentCategory, list[str]] = {cat: [] for cat in IntentCategory}

        for category, patterns in self._keyword_rules.items():
            for pattern in patterns:
                matches = re.findall(pattern, user_input)
                if matches:
                    rule_score = len(matches) * 1.0
                    if any(c in pattern for c in r"+\-*/×÷"):
                        rule_score += 0.5
                    scores[category] += rule_score
                    matched_rules[category].extend(matches)

        has_question_mark = "？" in user_input or "?" in user_input
        if has_question_mark and scores[IntentCategory.KNOWLEDGE_QA] == 0:
            scores[IntentCategory.KNOWLEDGE_QA] = 0.3

        if context and context.get("history"):
            history = context["history"]
            if len(history) >= 2 and history[-1].get("role") == "assistant":
                if scores[IntentCategory.KNOWLEDGE_QA] > 0:
                    scores[IntentCategory.MULTI_TURN] = 0.5

        max_score = max(scores.values())
        if max_score == 0:
            best_intent = IntentCategory.GENERAL
        else:
            candidates = [cat for cat, s in scores.items() if s == max_score]
            best_intent = candidates[0]
            for cat in self._priority:
                if cat in candidates:
                    best_intent = cat
                    break

        confidence = min(max_score / 3.0, 1.0) if max_score > 0 else 0.2
        decision = self._build_decision(best_intent, user_input, context, confidence, matched_rules)

        self._route_log.append({
            "timestamp": time.time(),
            "input": user_input[:200],
            **decision.to_dict(),
        })
        return decision

    def _build_decision(
        self,
        intent: IntentCategory,
        user_input: str,
        context: dict,
        confidence: float,
        matched_rules: dict,
    ) -> RoutingDecision:
        routing_map = {
            IntentCategory.MATH_CALCULATION: ("math", "innoSpark", ["calculator"]),
            IntentCategory.TEXT_CREATION: ("chinese", "qwen", []),
            IntentCategory.KNOWLEDGE_QA: (None, "innoSpark", ["knowledge"]),
            IntentCategory.LEARNING_PLAN: ("general", "innoSpark", ["timer"]),
            IntentCategory.EMOTIONAL_SUPPORT: ("general", "doubao", []),
            IntentCategory.TOOL_CALL: (None, "innoSpark", []),
            IntentCategory.MULTI_TURN: (None, "innoSpark", []),
            IntentCategory.GENERAL: (None, "innoSpark", []),
        }

        agent, model, tools = routing_map[intent]

        if intent == IntentCategory.KNOWLEDGE_QA:
            agent = _detect_subject(user_input)
        elif intent == IntentCategory.TOOL_CALL:
            if "字典" in user_input or "查词" in user_input:
                agent = "chinese"
                tools = ["dictionary"]
            elif "计时" in user_input or "番茄钟" in user_input:
                agent = "general"
                tools = ["timer"]
            elif "知识点" in user_input:
                agent = _detect_subject(user_input)
                tools = ["knowledge"]
            else:
                agent = _detect_subject(user_input)
        elif intent in (IntentCategory.MULTI_TURN, IntentCategory.GENERAL):
            if context and context.get("active_agent"):
                agent = context["active_agent"]
            else:
                agent = _detect_subject(user_input)

        reasoning_parts = []
        if matched_rules[intent]:
            reasoning_parts.append(f"匹配关键词: {matched_rules[intent][:5]}")
        reasoning_parts.append(f"意图: {intent.value}")
        reasoning_parts.append(f"路由到 {agent} 智能体, 使用 {model} 模型")
        reasoning = "; ".join(reasoning_parts)

        return RoutingDecision(
            intent=intent,
            target_agent=agent or "general",
            target_model=model,
            use_tools=tools,
            confidence=round(confidence, 2),
            reasoning=reasoning,
        )

    def get_route_log(self) -> list[dict]:
        return list(self._route_log)

    def get_stats(self) -> dict:
        if not self._route_log:
            return {
                "total_routes": 0,
                "model_usage": {},
                "intent_distribution": {},
                "avg_confidence": 0.0,
            }

        model_usage: dict[str, int] = {}
        intent_dist: dict[str, int] = {}
        total_confidence = 0.0

        for entry in self._route_log:
            model = entry.get("target_model", "unknown")
            model_usage[model] = model_usage.get(model, 0) + 1

            intent = entry.get("intent", "unknown")
            intent_dist[intent] = intent_dist.get(intent, 0) + 1

            total_confidence += entry.get("confidence", 0.0)

        total = len(self._route_log)
        return {
            "total_routes": total,
            "model_usage": model_usage,
            "intent_distribution": intent_dist,
            "avg_confidence": round(total_confidence / total, 3),
        }
