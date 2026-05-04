from lebotclaw.core.agent import Agent
from lebotclaw.tools.registry import ToolRegistry
from lebotclaw.tools.builtin.calculator import CalculatorTool
from lebotclaw.tools.builtin.knowledge import KnowledgeTool
from lebotclaw.education.heads import HEADSTemplate


class MathAgent:

    @staticmethod
    def create(model_adapter=None, memory=None) -> Agent:
        tools = ToolRegistry()
        tools.register(CalculatorTool())
        tools.register(KnowledgeTool())
        return Agent(
            name="math",
            system_prompt=HEADSTemplate.math_prompt(),
            tools=tools,
            model_adapter=model_adapter,
            memory=memory,
        )


def create_math_agent(model_adapter=None, memory=None) -> Agent:
    return MathAgent.create(model_adapter=model_adapter, memory=memory)
