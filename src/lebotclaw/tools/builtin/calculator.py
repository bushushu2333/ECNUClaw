import ast
import math
import operator

from lebotclaw.tools.base import Tool, ToolResult

_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "abs": abs,
    "round": round,
    "ceil": math.ceil,
    "floor": math.floor,
}

_SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.UnaryOp):
        op_func = _SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(_safe_eval(node.operand))
    if isinstance(node, ast.BinOp):
        op_func = _SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct function calls are allowed")
        func_name = node.func.id
        if func_name not in _SAFE_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' is not allowed")
        args = [_safe_eval(arg) for arg in node.args]
        return _SAFE_FUNCTIONS[func_name](*args)
    if isinstance(node, ast.Name):
        if node.id in _SAFE_CONSTANTS:
            return _SAFE_CONSTANTS[node.id]
        raise ValueError(f"Name '{node.id}' is not allowed")
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


class CalculatorTool(Tool):
    name = "calculator"
    description = "Safe math expression calculator. Supports +, -, *, /, **, %, and functions like sqrt, sin, cos, tan, log, abs, round, ceil, floor, plus constants pi and e."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Math expression to evaluate, e.g. 'sqrt(2) + 3 * 4'",
            }
        },
        "required": ["expression"],
    }

    def execute(self, **kwargs) -> ToolResult:
        expression = kwargs.get("expression", "").strip()
        if not expression:
            return ToolResult(success=False, output="", error="Empty expression")

        forbidden = ("import", "__", "exec", "eval", "compile", "open", "input")
        for token in forbidden:
            if token in expression:
                return ToolResult(
                    success=False, output="",
                    error=f"Forbidden token '{token}' in expression",
                )

        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            return ToolResult(success=False, output="", error=f"Syntax error: {exc}")

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef, ast.ClassDef, ast.Lambda)):
                return ToolResult(
                    success=False, output="",
                    error="Statements (import, assignment, function definition) are not allowed",
                )

        try:
            result = _safe_eval(tree)
        except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
            return ToolResult(success=False, output="", error=str(exc))

        if isinstance(result, float) and result == int(result) and abs(result) < 1e15:
            result = int(result)

        return ToolResult(
            success=True,
            output=str(result),
            metadata={"expression": expression, "result": result},
        )
