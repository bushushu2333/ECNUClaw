from lebotclaw.core.agent import Agent
from lebotclaw.tools.registry import ToolRegistry
from lebotclaw.tools.builtin.knowledge import KnowledgeTool
from lebotclaw.tools.builtin.timer import TimerTool
from lebotclaw.education.heads import HEADSTemplate


class ScienceAgent:

    @staticmethod
    def create(model_adapter=None, memory=None) -> Agent:
        tools = ToolRegistry()
        tools.register(KnowledgeTool())
        tools.register(TimerTool())
        return Agent(
            name="science",
            system_prompt=HEADSTemplate.science_prompt(),
            tools=tools,
            model_adapter=model_adapter,
            memory=memory,
        )


def create_science_agent(model_adapter=None, memory=None) -> Agent:
    return ScienceAgent.create(model_adapter=model_adapter, memory=memory)
