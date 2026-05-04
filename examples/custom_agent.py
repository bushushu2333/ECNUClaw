"""Custom Agent Example — Build your own education agent."""

from lebotclaw.core.agent import Agent, AgentRegistry
from lebotclaw.core.memory import MemoryStore
from lebotclaw.core.planner import Planner
from lebotclaw.core.router import IntentRouter
from lebotclaw.tools.base import Tool, ToolResult
from lebotclaw.tools.registry import ToolRegistry
from lebotclaw.tools.builtin.calculator import CalculatorTool
from lebotclaw.tools.builtin.knowledge import KnowledgeTool


class GeometryTool(Tool):
    """Custom geometry calculator tool."""
    name = "geometry"
    description = "Calculate geometric properties: area, perimeter, volume."
    parameters = {
        "type": "object",
        "properties": {
            "shape": {"type": "string", "description": "Shape: circle, rectangle, triangle, sphere, cube"},
            "params": {"type": "object", "description": "Shape parameters, e.g. {'radius': 5} or {'length': 3, 'width': 4}"}
        },
        "required": ["shape", "params"]
    }

    def execute(self, **kwargs) -> ToolResult:
        import math
        shape = kwargs.get("shape", "")
        params = kwargs.get("params", {})

        if shape == "circle":
            r = params.get("radius", 0)
            return ToolResult(
                success=True,
                output=f"圆 (r={r}): 面积={math.pi * r**2:.2f}, 周长={2 * math.pi * r:.2f}"
            )
        elif shape == "rectangle":
            l, w = params.get("length", 0), params.get("width", 0)
            return ToolResult(
                success=True,
                output=f"长方形 ({l}×{w}): 面积={l*w}, 周长={2*(l+w)}"
            )
        elif shape == "triangle":
            b, h = params.get("base", 0), params.get("height", 0)
            return ToolResult(
                success=True,
                output=f"三角形 (底={b}, 高={h}): 面积={0.5*b*h}"
            )
        else:
            return ToolResult(success=False, output="", error=f"Unknown shape: {shape}")


def main():
    # Create a custom geometry-focused math agent
    tools = ToolRegistry()
    tools.register(CalculatorTool())
    tools.register(KnowledgeTool())
    tools.register(GeometryTool())

    memory = MemoryStore()

    agent = Agent(
        name="geometry_tutor",
        system_prompt=(
            "你是一个几何学老师。你善于用图形和实例帮助学生理解几何概念。"
            "当学生问面积、周长、体积时，使用 geometry 工具进行计算。"
        ),
        tools=tools,
        memory=memory,
    )

    # Test the custom tool
    print("=== Custom Geometry Tool ===")
    result = tools.execute("geometry", shape="circle", params={"radius": 5})
    print(f"  {result.output}")

    result = tools.execute("geometry", shape="rectangle", params={"length": 3, "width": 4})
    print(f"  {result.output}")

    result = tools.execute("geometry", shape="triangle", params={"base": 6, "height": 4})
    print(f"  {result.output}")

    # Register in multi-agent system
    from lebotclaw.education.subjects import MathAgent, ChineseAgent

    registry = AgentRegistry()
    registry.register(agent)
    registry.register(MathAgent.create())
    registry.register(ChineseAgent.create())

    print(f"\nRegistered agents: {registry.list_agents()}")

    # Switch between agents
    registry.switch_to("geometry_tutor")
    print(f"Active agent: {registry.get_active().name}")

    print("\n✅ Custom Agent Demo 完成！")


if __name__ == "__main__":
    main()
