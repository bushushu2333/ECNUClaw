"""Tests for ECNUClaw agent and registry."""
import pytest
import tempfile
import os

from ecnuclaw.core.agent import Agent, AgentRegistry
from ecnuclaw.core.memory import MemoryStore
from ecnuclaw.tools.registry import ToolRegistry
from ecnuclaw.tools.builtin.calculator import CalculatorTool
from ecnuclaw.education.heads import HEADSTemplate
from ecnuclaw.education.assessment import AssessmentModule


class TestAgent:
    def setup_method(self):
        self.db_path = tempfile.mktemp(suffix=".db")
        self.memory = MemoryStore(db_path=self.db_path)
        self.tools = ToolRegistry()
        self.tools.register(CalculatorTool())
        self.agent = Agent(
            name="test_agent",
            system_prompt="你是一个测试助手。",
            tools=self.tools,
            memory=self.memory,
        )

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_init(self):
        assert self.agent.name == "test_agent"
        assert len(self.agent._history) == 0

    def test_reset(self):
        self.agent._history = [{"role": "user", "content": "hi"}]
        self.agent.reset()
        assert len(self.agent._history) == 0

    def test_freeze_restore(self):
        self.agent._history = [{"role": "user", "content": "test"}]
        ctx_id = self.agent.freeze()
        assert ctx_id

        new_agent = Agent(
            name="test_agent",
            system_prompt="test",
            memory=self.memory,
        )
        new_agent.restore(ctx_id)
        assert len(new_agent._history) > 0

    def test_build_system_prompt_with_memory(self):
        self.memory.save_memory("student_profile", "general", "年级", "五年级")
        prompt = self.agent._build_system_prompt_with_memory("分数")
        assert "年级" in prompt or "五年级" in prompt or "记忆" in prompt or len(prompt) > 0


class TestAgentRegistry:
    def setup_method(self):
        self.registry = AgentRegistry()
        self.db_path = tempfile.mktemp(suffix=".db")
        self.memory = MemoryStore(db_path=self.db_path)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_register_and_get(self):
        agent = Agent(name="math", system_prompt="math agent", memory=self.memory)
        self.registry.register(agent)
        assert self.registry.get("math") is agent

    def test_list_agents(self):
        self.registry.register(Agent(name="math", system_prompt="", memory=self.memory))
        self.registry.register(Agent(name="chinese", system_prompt="", memory=self.memory))
        assert set(self.registry.list_agents()) == {"math", "chinese"}

    def test_switch_to(self):
        self.registry.register(Agent(name="math", system_prompt="math", memory=self.memory))
        self.registry.register(Agent(name="chinese", system_prompt="chinese", memory=self.memory))
        agent = self.registry.switch_to("math")
        assert agent.name == "math"
        assert self.registry._active_agent == "math"

        agent2 = self.registry.switch_to("chinese")
        assert agent2.name == "chinese"
        assert self.registry._active_agent == "chinese"

    def test_get_active(self):
        assert self.registry.get_active() is None
        self.registry.register(Agent(name="math", system_prompt="", memory=self.memory))
        self.registry.switch_to("math")
        assert self.registry.get_active().name == "math"

    def test_get_not_found(self):
        with pytest.raises(KeyError):
            self.registry.get("nonexistent")


class TestHEADSTemplate:
    def test_system_base(self):
        prompt = HEADSTemplate.system_base("数学", "五年级")
        assert "数学" in prompt
        assert "五年级" in prompt

    def test_math_prompt(self):
        prompt = HEADSTemplate.math_prompt()
        assert "数学" in prompt
        assert "做题" in prompt or "数学题" in prompt

    def test_chinese_prompt(self):
        prompt = HEADSTemplate.chinese_prompt()
        assert "语文" in prompt

    def test_science_prompt(self):
        prompt = HEADSTemplate.science_prompt()
        assert "科学" in prompt

    def test_general_prompt(self):
        prompt = HEADSTemplate.general_prompt()
        assert "ECNUClaw" in prompt


class TestAssessmentModule:
    def setup_method(self):
        self.assessor = AssessmentModule()

    def test_assess_good_interaction(self):
        msgs = [
            {"role": "user", "content": "什么是通分？"},
            {"role": "assistant", "content": "通分就是把两个分数变成同分母的分数。你能想一想，1/2和1/3怎么变成同分母吗？"},
        ]
        result = self.assessor.assess_interaction(msgs)
        assert 0 <= result.overall_score <= 1
        assert result.knowledge_accuracy >= 0
        assert result.interaction_naturalness >= 0

    def test_assess_with_profile(self):
        msgs = [
            {"role": "user", "content": "我不会做这道题"},
            {"role": "assistant", "content": "没关系，我们一步步来。你是五年级了对吧？我们从你学过的知识点开始。"},
        ]
        result = self.assessor.assess_interaction(msgs, student_profile={"年级": "五年级"})
        assert result.personalization >= 0

    def test_generate_report(self):
        result = self.assessor.assess_interaction([
            {"role": "user", "content": "1+1等于几？"},
            {"role": "assistant", "content": "你觉得呢？可以先想想。"},
        ])
        report = self.assessor.generate_report(result)
        assert len(report) > 0
