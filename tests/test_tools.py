"""Tests for ECNUClaw tools framework."""
import pytest
from ecnuclaw.tools.base import Tool, ToolResult, ToolCall
from ecnuclaw.tools.registry import ToolRegistry
from ecnuclaw.tools.builtin.calculator import CalculatorTool
from ecnuclaw.tools.builtin.dictionary import DictionaryTool
from ecnuclaw.tools.builtin.knowledge import KnowledgeTool
from ecnuclaw.tools.builtin.timer import TimerTool


class TestCalculatorTool:
    def setup_method(self):
        self.calc = CalculatorTool()

    def test_basic_arithmetic(self):
        r = self.calc.execute(expression="2 + 3")
        assert r.success
        assert "5" in r.output

    def test_order_of_operations(self):
        r = self.calc.execute(expression="2 + 3 * 4")
        assert r.success
        assert "14" in r.output

    def test_sqrt(self):
        r = self.calc.execute(expression="sqrt(144)")
        assert r.success
        assert "12" in r.output

    def test_pi(self):
        r = self.calc.execute(expression="pi")
        assert r.success
        assert "3.14" in r.output

    def test_reject_import(self):
        r = self.calc.execute(expression="import os")
        assert not r.success

    def test_reject_assignment(self):
        r = self.calc.execute(expression="x = 1")
        assert not r.success

    def test_reject_dangerous(self):
        r = self.calc.execute(expression="__import__('os').system('ls')")
        assert not r.success

    def test_schema(self):
        schema = self.calc.to_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "calculator"


class TestDictionaryTool:
    def setup_method(self):
        self.d = DictionaryTool()

    def test_lookup_chinese(self):
        r = self.d.execute(word="美丽")
        assert r.success
        assert "měi" in r.output or "形容词" in r.output

    def test_lookup_english(self):
        r = self.d.execute(word="happy", language="en")
        assert r.success
        assert "快乐" in r.output or "happy" in r.output.lower()

    def test_not_found(self):
        r = self.d.execute(word="xyzabc123")
        assert not r.success


class TestKnowledgeTool:
    def setup_method(self):
        self.k = KnowledgeTool()

    def test_search_math(self):
        r = self.k.execute(query="分数", subject="数学")
        assert r.success
        assert "分数" in r.output

    def test_search_by_grade(self):
        r = self.k.execute(query="加法", grade="一年级")
        assert r.success

    def test_search_all(self):
        r = self.k.execute(query="数学")
        assert r.success


class TestTimerTool:
    def setup_method(self):
        self.t = TimerTool()

    def test_start_stop(self):
        r = self.t.execute(action="start_timer", label="test_timer")
        assert r.success
        r2 = self.t.execute(action="stop_timer", label="test_timer")
        assert r2.success
        assert "0m" in r2.output

    def test_pomodoro(self):
        r = self.t.execute(action="pomodoro")
        assert r.success
        assert "25" in r.output

    def test_status_empty(self):
        r = self.t.execute(action="status")
        assert r.success


class TestToolRegistry:
    def setup_method(self):
        self.reg = ToolRegistry()
        self.calc = CalculatorTool()
        self.reg.register(self.calc)

    def test_register_and_get(self):
        t = self.reg.get("calculator")
        assert t is self.calc

    def test_get_not_found(self):
        with pytest.raises(KeyError):
            self.reg.get("nonexistent")

    def test_list_tools(self):
        tools = self.reg.list_tools()
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "calculator"

    def test_execute(self):
        r = self.reg.execute("calculator", expression="1+1")
        assert r.success

    def test_unregister(self):
        self.reg.unregister("calculator")
        with pytest.raises(KeyError):
            self.reg.get("calculator")


class TestToolCallParsing:
    def test_parse_json_block(self):
        text = '```tool_call\n{"tool_name": "calculator", "arguments": {"expression": "1+1"}}\n```'
        calls = Tool.parse_tool_calls(text)
        assert len(calls) >= 1
        assert calls[0].tool_name == "calculator"

    def test_parse_inline_json(self):
        text = '```tool_call\n{"tool_name": "calculator", "arguments": {"expression": "2+2"}}\n```'
        calls = Tool.parse_tool_calls(text)
        assert len(calls) >= 1
        assert calls[0].tool_name == "calculator"

    def test_no_tool_call(self):
        text = "This is just a normal response."
        calls = Tool.parse_tool_calls(text)
        assert len(calls) == 0
