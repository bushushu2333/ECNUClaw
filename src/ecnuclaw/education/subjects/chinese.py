from ecnuclaw.core.agent import Agent
from ecnuclaw.tools.registry import ToolRegistry
from ecnuclaw.tools.builtin.dictionary import DictionaryTool
from ecnuclaw.tools.builtin.knowledge import KnowledgeTool
from ecnuclaw.education.heads import HEADSTemplate


class ChineseAgent:

    @staticmethod
    def create(model_adapter=None, memory=None) -> Agent:
        tools = ToolRegistry()
        tools.register(DictionaryTool())
        tools.register(KnowledgeTool())
        return Agent(
            name="chinese",
            system_prompt=HEADSTemplate.chinese_prompt(),
            tools=tools,
            model_adapter=model_adapter,
            memory=memory,
        )


def create_chinese_agent(model_adapter=None, memory=None) -> Agent:
    return ChineseAgent.create(model_adapter=model_adapter, memory=memory)
