"""Tests for ECNUClaw router and planner."""
import pytest
import tempfile
import os

from ecnuclaw.core.router import IntentRouter, IntentCategory
from ecnuclaw.core.planner import Planner, Plan, Step, StepStatus
from ecnuclaw.core.memory import MemoryStore
from ecnuclaw.core.skills import SkillLibrary, TeachingSkill


class TestIntentRouter:
    def setup_method(self):
        self.router = IntentRouter()

    def test_math_calculation(self):
        d = self.router.classify("计算 3 * 7 + 2")
        assert d.intent == IntentCategory.MATH_CALCULATION
        assert d.target_agent == "math"

    def test_text_creation(self):
        d = self.router.classify("帮我写一篇关于春天的作文")
        assert d.intent == IntentCategory.TEXT_CREATION
        assert d.target_agent == "chinese"

    def test_knowledge_qa(self):
        d = self.router.classify("什么是光合作用？")
        assert d.intent == IntentCategory.KNOWLEDGE_QA

    def test_learning_plan(self):
        d = self.router.classify("帮我复习第三章")
        assert d.intent == IntentCategory.LEARNING_PLAN

    def test_emotional_support(self):
        d = self.router.classify("我考试好紧张，压力很大")
        assert d.intent == IntentCategory.EMOTIONAL_SUPPORT
        assert d.target_model == "doubao"

    def test_general(self):
        d = self.router.classify("你好")
        assert d.intent == IntentCategory.GENERAL

    def test_routing_stats(self):
        self.router.classify("计算1+1")
        self.router.classify("写作文")
        stats = self.router.get_stats()
        assert stats["total_routes"] == 2
        assert "model_usage" in stats


class TestPlanner:
    def setup_method(self):
        self.planner = Planner()

    def test_review_template(self):
        plan = self.planner.decompose("帮我复习第三章", subject="math")
        assert len(plan.steps) == 4
        assert plan.steps[0].title == "知识点回顾"

    def test_learn_template(self):
        plan = self.planner.decompose("我想学分数", subject="math")
        assert len(plan.steps) == 5
        assert plan.steps[0].title == "概念引入"

    def test_practice_template(self):
        plan = self.planner.decompose("我要做数学题")
        assert len(plan.steps) == 4 or len(plan.steps) == 5

    def test_writing_template(self):
        plan = self.planner.decompose("帮我写作文", subject="chinese")
        assert len(plan.steps) == 5

    def test_generic_template(self):
        plan = self.planner.decompose("随便聊聊")
        assert len(plan.steps) >= 3

    def test_advance_step(self):
        plan = self.planner.decompose("复习第三章")
        plan = self.planner.advance_step(plan, result="回顾完成")
        assert plan.current_step_index == 1
        assert plan.steps[0].status == StepStatus.COMPLETED

    def test_get_progress(self):
        plan = self.planner.decompose("复习第三章")
        progress = self.planner.get_progress(plan)
        assert progress["total_steps"] == 4
        assert progress["completed_steps"] == 0
        assert progress["completion_rate"] == 0.0

    def test_replan_positive(self):
        plan = self.planner.decompose("复习第三章")
        plan = self.planner.advance_step(plan, result="简单")
        new_plan = self.planner.replan(plan, "太简单了，都会了")
        assert isinstance(new_plan, Plan)

    def test_replan_negative(self):
        plan = self.planner.decompose("复习第三章")
        new_plan = self.planner.replan(plan, "太难了，我还是不会")
        assert isinstance(new_plan, Plan)
        assert len(new_plan.steps) >= len(plan.steps)


class TestMemoryStore:
    def setup_method(self):
        self.db_path = tempfile.mktemp(suffix=".db")
        self.memory = MemoryStore(db_path=self.db_path)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_save_and_search(self):
        self.memory.save_memory("student_profile", "math", "年级", "五年级")
        results = self.memory.search_memory(query="年级")
        assert len(results) >= 1
        assert results[0].content == "五年级"

    def test_search_by_category(self):
        self.memory.save_memory("student_profile", "math", "风格", "视觉型")
        self.memory.save_memory("learning_progress", "math", "错题", "通分错误")
        results = self.memory.search_memory(category="student_profile")
        assert all(r.category == "student_profile" for r in results)

    def test_student_profile(self):
        self.memory.save_memory("student_profile", "general", "年级", "五年级")
        self.memory.save_memory("student_profile", "general", "名字", "小明")
        profile = self.memory.get_student_profile()
        assert "年级" in profile
        assert "名字" in profile

    def test_freeze_restore(self):
        ctx_id = self.memory.freeze_context("math", {"step": 1, "topic": "分数"})
        restored = self.memory.restore_context(ctx_id)
        assert restored["agent_name"] == "math"
        assert restored["data"]["step"] == 1

    def test_summarize_session(self):
        msgs = [
            {"role": "user", "content": "什么是通分？"},
            {"role": "assistant", "content": "通分的定义是把两个分数变成同分母"},
            {"role": "user", "content": "我还是不太懂"},
        ]
        summary = self.memory.summarize_session(msgs)
        assert len(summary) > 0

    def test_cleanup(self):
        self.memory.save_memory("session_summary", "general", "old", "旧记忆")
        count = self.memory.cleanup_old(days=0)
        assert count >= 0


class TestSkillLibrary:
    def setup_method(self):
        self.path = tempfile.mktemp(suffix=".json")
        self.lib = SkillLibrary(store_path=self.path)

    def teardown_method(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_add_and_find(self):
        skill = TeachingSkill(
            name="分数概念讲解",
            trigger_scenario="学生问什么是分数",
            subject="math",
            applicable_grades=["3年级", "4年级", "5年级"],
            steps_template=[{"title": "引入", "prompt_hint": "用一个披萨来举例"}],
        )
        sid = self.lib.add_skill(skill)
        assert sid > 0

        found = self.lib.find_skill(scenario="分数", subject="math")
        assert len(found) >= 1
        assert found[0].name == "分数概念讲解"

    def test_update_effectiveness(self):
        skill = TeachingSkill(name="test", subject="math")
        sid = self.lib.add_skill(skill)
        self.lib.update_effectiveness(sid, 0.9)
        skills = self.lib.list_skills()
        assert skills[0].effectiveness_score == 0.9

    def test_list_by_subject(self):
        self.lib.add_skill(TeachingSkill(name="s1", subject="math"))
        self.lib.add_skill(TeachingSkill(name="s2", subject="chinese"))
        math_skills = self.lib.list_skills(subject="math")
        assert all(s.subject == "math" for s in math_skills)
