from ecnuclaw.core.agent import Agent
from ecnuclaw.tools.registry import ToolRegistry
from ecnuclaw.tools.builtin.calculator import CalculatorTool
from ecnuclaw.tools.builtin.knowledge import KnowledgeTool
from ecnuclaw.education.heads import HEADSTemplate


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
