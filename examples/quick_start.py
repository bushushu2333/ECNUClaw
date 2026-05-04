"""LebotClaw Quick Start — 5 lines to run an education agent."""
from lebotclaw.core.agent import Agent
from lebotclaw.core.memory import MemoryStore
from lebotclaw.core.planner import Planner
from lebotclaw.core.router import IntentRouter
from lebotclaw.tools.builtin import CalculatorTool, DictionaryTool, KnowledgeTool, TimerTool
from lebotclaw.tools.registry import ToolRegistry


def main():
    # 1. Set up tools
    tools = ToolRegistry()
    tools.register(CalculatorTool())
    tools.register(DictionaryTool())
    tools.register(KnowledgeTool())
    tools.register(TimerTool())

    # 2. Create memory and planner
    memory = MemoryStore()
    planner = Planner()

    # 3. Create a math agent (no model adapter — offline mode)
    agent = Agent(
        name="math_demo",
        system_prompt="你是一个友善的数学老师，善于引导学生思考。",
        tools=tools,
        memory=memory,
        planner=planner,
    )

    # 4. Test the planner
    print("=== 学习规划 ===")
    plan = planner.decompose("帮我复习分数", subject="math")
    for step in plan.steps:
        print(f"  Step {step.id}: {step.title} — {step.description}")

    print(f"\n进度: {planner.get_progress(plan)}")

    # 5. Test the router
    print("\n=== 意图路由 ===")
    router = IntentRouter()
    test_inputs = [
        "计算 3 * 7 + 2",
        "帮我写一篇关于春天的作文",
        "什么是光合作用？",
        "我考试好紧张",
    ]
    for text in test_inputs:
        decision = router.classify(text)
        print(f"  '{text}' → intent={decision.intent.value}, agent={decision.target_agent}, model={decision.target_model}")

    # 6. Test tools
    print("\n=== 工具调用 ===")
    result = tools.execute("calculator", expression="sqrt(144) + 3**2")
    print(f"  calculator: sqrt(144) + 3^2 = {result.output}")

    result = tools.execute("dictionary", word="美丽")
    print(f"  dictionary 美丽: {result.output[:60]}...")

    result = tools.execute("knowledge", query="分数", subject="数学")
    print(f"  knowledge 分数: {result.output[:60]}...")

    # 7. Test memory
    print("\n=== 记忆系统 ===")
    memory.save_memory("student_profile", "math", "年级", "五年级", ["数学"])
    memory.save_memory("learning_progress", "math", "错题", "分数加减法容易忘记通分", ["错题"])

    results = memory.search_memory(query="分数", subject="math")
    print(f"  搜索'分数': 找到 {len(results)} 条记忆")
    for r in results:
        print(f"    [{r.category}] {r.key}: {r.content}")

    profile = memory.get_student_profile()
    print(f"  学生画像: {profile}")

    print("\n✅ Quick Start Demo 完成！")


if __name__ == "__main__":
    main()
