"""ECNUClaw CLI — 面向 K-12 学生的终端学习伙伴"""
import sys
import os
import json
from pathlib import Path

from ecnuclaw.core.router import IntentRouter

_CONFIG_DIR = Path.home() / ".ecnuclaw"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

# 国内 AI 模型列表
_MODEL_OPTIONS = [
    {"name": "deepseek", "adapter_class": "ecnuclaw.adapters.deepseek.DeepSeekAdapter",
     "env_key": "DEEPSEEK_API_KEY", "base_env": "DEEPSEEK_BASE_URL",
     "default_model": "deepseek-chat",
     "label": "DeepSeek（深度求索）", "desc": "聪明实惠，推荐先用这个"},
    {"name": "glm", "adapter_class": "ecnuclaw.adapters.glm.GLMAdapter",
     "env_key": "GLM_API_KEY", "base_env": "GLM_BASE_URL",
     "default_model": "glm-5.1",
     "label": "智谱清言（智谱AI）", "desc": "综合能力强，速度快"},
    {"name": "kimi", "adapter_class": "ecnuclaw.adapters.kimi.KimiAdapter",
     "env_key": "MOONSHOT_API_KEY", "base_env": "KIMI_BASE_URL",
     "default_model": "K2.6",
     "label": "Kimi（月之暗面）", "desc": "长文本能力强，适合阅读理解"},
    {"name": "doubao", "adapter_class": "ecnuclaw.adapters.doubao.DoubaoAdapter",
     "env_key": "DOUBAO_API_KEY", "base_env": "DOUBAO_BASE_URL",
     "default_model": "",
     "label": "豆包（字节跳动/火山引擎）", "desc": "聊天自然，适合情感陪伴",
     "extra_env": "DOUBAO_ENDPOINT_ID"},
    {"name": "qwen", "adapter_class": "ecnuclaw.adapters.qwen.QwenAdapter",
     "env_key": "QWEN_API_KEY", "base_env": "QWEN_BASE_URL",
     "default_model": "qwen3-max",
     "label": "通义千问（阿里云）", "desc": "中文理解特别强，语文写作首选"},
    {"name": "seed", "adapter_class": "ecnuclaw.adapters.doubao.DoubaoAdapter",
     "env_key": "SEED_API_KEY", "base_env": "DOUBAO_BASE_URL",
     "default_model": "",
     "label": "Seed（火山引擎）", "desc": "火山引擎最新模型，推理能力强",
     "extra_env": "SEED_ENDPOINT_ID", "extra_env_label": "终端地址"},
    {"name": "innoSpark", "adapter_class": "ecnuclaw.adapters.innoSpark.InnoSparkAdapter",
     "env_key": "INNOSPARK_API_KEY", "base_env": "INNOSPARK_BASE_URL",
     "default_model": "innoSpark",
     "label": "启创教育大模型", "desc": "专门为教育场景设计"},
]

# URL 包含这些关键词时自动切换为 Anthropic Messages API 格式
_ANTHROPIC_URL_HINTS = ("anthropic", "/coding", "claude")

# 对话风格选项
_STYLE_OPTIONS = [
    {"name": "warm", "label": "温柔耐心型", "desc": "像大姐姐一样，慢慢引导，多多鼓励",
     "extra": "你说话温柔有耐心，像一位亲切的大姐姐。多用「没关系」「慢慢来」「你已经很棒了」这样的语气。"},
    {"name": "lively", "label": "活泼有趣型", "desc": "像好朋友一样，用有趣的例子和比喻",
     "extra": "你说话活泼有趣，像同学中的好朋友。多用比喻和生活中的小例子，偶尔用感叹号表达惊喜。"},
    {"name": "serious", "label": "严谨认真型", "desc": "像老师一样，条理清晰，重点明确",
     "extra": "你说话严谨认真，像一位好老师。条理清晰，重点突出，用编号列出关键步骤。"},
]

_SUBJECT_LABELS = {
    "math": "📐 数学小伙伴",
    "chinese": "📝 语文小伙伴",
    "science": "🔬 科学小伙伴",
    "general": "🌟 万能小伙伴",
}


# ── 工具函数 ──────────────────────────────────────────────

def _load_config():
    if _CONFIG_FILE.exists():
        try:
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_config(cfg):
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_anthropic_url(url):
    return any(hint in url.lower() for hint in _ANTHROPIC_URL_HINTS)


def _create_adapter(model_config, api_key=None, base_url=None, model=None):
    import importlib

    effective_url = base_url
    if not effective_url and model_config.get("base_env"):
        effective_url = os.environ.get(model_config["base_env"], "")

    # URL 命中 Anthropic 关键词 → 自动用 Anthropic 兼容适配器
    if effective_url and _is_anthropic_url(effective_url):
        from ecnuclaw.adapters.anthropic_compat import AnthropicCompatAdapter
        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if effective_url:
            kwargs["base_url"] = effective_url
        if model:
            kwargs["model"] = model
        elif model_config.get("default_model"):
            kwargs["model"] = model_config["default_model"]
        return AnthropicCompatAdapter(**kwargs)

    # 走默认的 OpenAI 兼容适配器
    module_path, class_name = model_config["adapter_class"].rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    kwargs = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    elif model_config.get("base_env"):
        env_url = os.environ.get(model_config["base_env"], "")
        if env_url:
            kwargs["base_url"] = env_url
    if model:
        kwargs["model"] = model
    if model_config["name"] in ("doubao", "seed"):
        env_key = model_config.get("extra_env", "")
        endpoint = os.environ.get(env_key, "")
        if endpoint:
            kwargs["endpoint_id"] = endpoint
    return cls(**kwargs)


def _scan_model_adapters():
    adapters = {}
    default = None
    cfg = _load_config()
    model_cfg = cfg.get("model", {})
    saved_model = model_cfg.get("default", "")
    saved_url = model_cfg.get("base_url", "")
    saved_model_name = model_cfg.get("model_name", "")
    saved_api_key = model_cfg.get("api_key", "")

    for mc in _MODEL_OPTIONS:
        key = os.environ.get(mc["env_key"], "")
        if mc.get("extra_env"):
            key = key and os.environ.get(mc["extra_env"], "")
        if not key:
            continue
        try:
            # 如果是用户保存的模型，传入自定义 URL、模型名、key
            is_saved = mc["name"] == saved_model
            adapter = _create_adapter(
                mc,
                api_key=saved_api_key if is_saved else None,
                base_url=saved_url if is_saved else None,
                model=saved_model_name if is_saved else None,
            )
            adapters[mc["name"]] = adapter
            if default is None:
                default = mc["name"]
        except Exception:
            continue
    if saved_model and saved_model in adapters:
        default = saved_model
    return adapters, default


def _input(prompt, default=""):
    try:
        val = input(prompt).strip()
        return val if val else default
    except EOFError:
        return default


def _print_banner(console):
    console.print()
    console.print("[bright_cyan]  ╔═══════════════════════════════════════════╗[/]")
    console.print("[bright_cyan]  ║[/]                                           [bright_cyan]║[/]")
    console.print("[bright_cyan]  ║[/]  [bold bright_white]ECNUClaw[/]  [dim]v0.1.0[/]                         [bright_cyan]║[/]")
    console.print("[bright_cyan]  ║[/]  [bright_white]你的智能学习伙伴[/]                          [bright_cyan]║[/]")
    console.print("[bright_cyan]  ║[/]                                           [bright_cyan]║[/]")
    console.print("[bright_cyan]  ╚═══════════════════════════════════════════╝[/]")
    console.print()


def _print_step(console, step_num, total, title):
    console.print(f"\n  [bold bright_magenta]━━ 第 {step_num} 步 / 共 {total} 步 ━━  {title}[/]")
    console.print(f"  [dim]{'─' * 40}[/]")


def _print_box(console, lines, color="bright_blue"):
    width = max(len(line) for line in lines) + 4
    console.print(f"  [{color}]╭{'─' * width}╮[/]")
    for line in lines:
        pad = width - len(line) - 2
        console.print(f"  [{color}]│[/]  {line}{' ' * pad}[{color}]│[/]")
    console.print(f"  [{color}]╰{'─' * width}╯[/]")


def _print_ok(console, text):
    console.print(f"  [bold green]✅ {text}[/]")


def _print_hint(console, text):
    console.print(f"  [dim]{text}[/]")


# ── Setup Wizard ──────────────────────────────────────────

def run_setup_wizard(console):
    """完整的初始化向导，Ctrl+C 随时退出"""
    try:
        return _run_setup_wizard_inner(console)
    except KeyboardInterrupt:
        console.print("\n\n  [yellow]已退出设置向导，下次再配置吧～[/]")
        console.print()
        return None


def _run_setup_wizard_inner(console):
    cfg = _load_config()
    total_steps = 4

    console.print()
    _print_box(console, [
        "欢迎来到 ECNUClaw！",
        "",
        "接下来只需要几步，就能开始学习啦～",
        "随时可以按回车跳过不想填的选项",
    ], "bright_magenta")
    console.print()

    # ── Step 1: 选择 AI 大脑 ──
    model_connected = False
    while not model_connected:
        _print_step(console, 1, total_steps, "选择 AI 大脑")
        console.print("  ECNUClaw 需要连接一个 AI 大脑才能回答你的问题")
        _print_hint(console, "（这一步通常由老师或家长帮忙设置）")
        console.print()
        console.print("  可选的 AI 大脑：")
        console.print()
        for i, mc in enumerate(_MODEL_OPTIONS, 1):
            console.print(f"    [bold]{i}.[/] [cyan]{mc['label']}[/]")
            console.print(f"       {mc['desc']}")
        console.print()

        total = len(_MODEL_OPTIONS)
        choice = _input(f"  请输入编号 (1-{total})，直接回车跳过：")
        if not choice:
            console.print("  [yellow]跳过了 AI 大脑设置，稍后可以用 [bold]/设置[/bold] 重新配置[/]")
            break
        try:
            idx = int(choice) - 1
        except ValueError:
            console.print("  [yellow]跳过模型设置[/]")
            break
        if not (0 <= idx < total):
            console.print("  [yellow]编号不对，跳过[/]")
            break

        mc = _MODEL_OPTIONS[idx]

        # 密钥输入 + 验证循环（同一个模型可以重试）
        while not model_connected:
            console.print(f"\n  你选择了 [cyan bold]{mc['label']}[/]")

            # 先问 API 地址（显示默认值，回车用默认）
            default_url = ""
            try:
                module_path, class_name = mc["adapter_class"].rsplit(".", 1)
                import importlib
                cls = getattr(importlib.import_module(module_path), class_name)
                default_url = cls.DEFAULT_BASE_URL
            except Exception:
                pass
            saved_url = cfg.get("model", {}).get("base_url", "")
            hint_url = saved_url or os.environ.get(mc.get("base_env", ""), "") or default_url
            console.print(f"  [dim]默认 API 地址：{hint_url}[/]")
            url_input = _input("  API 地址（回车用默认，输入 n 换模型）：")
            if url_input.strip().lower() == "n":
                break  # 回到模型选择
            if url_input.strip():
                custom_url = url_input.strip()
            else:
                custom_url = hint_url

            # 再问密钥
            key = _input("  请输入密钥（直接回车换一个模型）：")
            if key:
                key = key.encode("ascii", errors="ignore").decode("ascii").strip()
            if not key:
                break  # 回到模型选择

            # 如果 URL 被改过（不是默认），问一下模型名
            custom_model = None
            url_changed = custom_url and custom_url != default_url
            if url_changed:
                saved_model_name = cfg.get("model", {}).get("model_name", "")
                hint_model = saved_model_name or mc.get("default_model", "")
                if hint_model:
                    console.print(f"  [dim]默认模型：{hint_model}[/]")
                model_input = _input("  模型名称（回车用默认）：")
                custom_model = model_input.strip() if model_input.strip() else hint_model

            os.environ[mc["env_key"]] = key
            if custom_url and custom_url != default_url:
                os.environ[mc.get("base_env", "")] = custom_url
            if mc.get("extra_env"):
                extra_label = mc.get("extra_env_label", "终端地址")
                extra = _input(f"  还需要填写{extra_label}（没有可跳过）：")
                if extra:
                    extra = extra.encode("ascii", errors="ignore").decode("ascii").strip()
                    os.environ[mc["extra_env"]] = extra

            # 真实验证：用 key 调一次模型
            console.print("  [dim]正在验证密钥...[/]")
            try:
                adapter = _create_adapter(mc, api_key=key, base_url=custom_url, model=custom_model)
                resp = adapter.generate(
                    messages=[{"role": "user", "content": "hi"}],
                    max_tokens=10,
                )
                verified = bool(resp.content is not None)
            except Exception as e:
                verified = False
                err_msg = str(e)[:120]
                console.print(f"  [red]连接失败：{err_msg}[/]")

            if verified:
                cfg.setdefault("model", {})["default"] = mc["name"]
                cfg.setdefault("model", {})["api_key"] = key
                cfg.setdefault("model", {})["base_url"] = custom_url
                if custom_model:
                    cfg.setdefault("model", {})["model_name"] = custom_model
                env_file = _CONFIG_DIR / ".env"
                _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                env_lines = [f"{mc['env_key']}={key}"]
                if custom_url and custom_url != default_url:
                    env_lines.append(f"ECNUCLAW_BASE_URL={custom_url}")
                if custom_model:
                    env_lines.append(f"ECNUCLAW_MODEL={custom_model}")
                if mc.get("extra_env") and os.environ.get(mc["extra_env"]):
                    env_lines.append(f"{mc['extra_env']}={os.environ[mc['extra_env']]}")
                env_file.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
                _print_ok(console, f"{mc['label']} 已连接！")
                model_connected = True
            else:
                console.print("  [yellow]密钥验证没通过[/]")
                retry = _input("  重新输入按回车，换模型输入 n：")
                if retry.lower() == "n":
                    break  # 回到模型选择

    # ── Step 2: 选择对话风格 ──
    _print_step(console, 2, total_steps, "选择对话风格")
    console.print("  你希望 ECNUClaw 用什么风格和你聊天？")
    console.print()
    for i, style in enumerate(_STYLE_OPTIONS, 1):
        console.print(f"    [bold]{i}.[/] [cyan]{style['label']}[/] — {style['desc']}")
    console.print()

    style_choice = _input("  请输入编号 (1-3)，默认 1：", default="1")
    try:
        style_idx = int(style_choice) - 1
        if not (0 <= style_idx < len(_STYLE_OPTIONS)):
            style_idx = 0
    except ValueError:
        style_idx = 0

    chosen_style = _STYLE_OPTIONS[style_idx]
    cfg["style"] = chosen_style["name"]
    _print_ok(console, f"已选择「{chosen_style['label']}」")

    # ── Step 3: 初始化详细程度 ──
    _print_step(console, 3, total_steps, "初始化详细程度")
    console.print("  你希望 ECNUClaw 了解你多少？")
    console.print()
    console.print("    [bold]1.[/] [cyan]快速模式[/] — 只告诉我你的名字和年级")
    console.print("    [bold]2.[/] [cyan]完整模式[/] — 名字、年级、喜欢的科目、学习习惯等")
    console.print()

    detail_choice = _input("  请输入编号 (1-2)，默认 1：", default="1")
    full_mode = detail_choice.strip() == "2"
    cfg["detail_mode"] = "full" if full_mode else "quick"

    # ── Step 4: 认识你 ──
    _print_step(console, 4, total_steps, "让 ECNUClaw 认识你")
    memory = None
    try:
        from ecnuclaw.core.memory import MemoryStore
        memory = MemoryStore()
    except Exception:
        pass

    student_name = _input("  你叫什么名字呀？", default="同学")
    if not student_name:
        student_name = "同学"
    cfg["student_name"] = student_name

    grade = _input("  你几年级啦？（比如：三年级、初一）")
    if grade:
        cfg["grade"] = grade

    if full_mode:
        console.print()
        favorite = _input("  你最喜欢哪门课？")
        if favorite:
            cfg["favorite_subject"] = favorite

        habit = _input("  你学习时喜欢怎么学？（看视频/做题/讨论/看书）")
        if habit:
            cfg["learning_habit"] = habit

        goal = _input("  最近有什么想提高的吗？（比如：分数运算、写作文）")
        if goal:
            cfg["learning_goal"] = goal

    # 保存到记忆
    if memory:
        memory.save_memory("student_profile", "general", "名字", student_name, ["名字"])
        if grade:
            memory.save_memory("student_profile", "general", "年级", grade, ["年级"])
        if full_mode:
            if favorite:
                memory.save_memory("student_profile", "general", "喜欢的科目", favorite, ["偏好"])
            if habit:
                memory.save_memory("student_profile", "general", "学习习惯", habit, ["习惯"])
            if goal:
                memory.save_memory("student_profile", "general", "学习目标", goal, ["目标"])

    # 保存配置
    cfg["initialized"] = True
    _save_config(cfg)

    # ── 完成 ──
    console.print()
    _print_box(console, [
        f"好哒{student_name}，ECNUClaw 记住你了！",
        "",
        "我准备了四个小伙伴来帮你学习：",
        "  📐 数学小伙伴 — 解题引导",
        "  📝 语文小伙伴 — 阅读和写作",
        "  🔬 科学小伙伴 — 科学探究",
        "  🌟 万能小伙伴 — 什么都能问",
        "",
        "直接输入问题就行，我会自动找最合适的来帮你！",
    ], "bright_cyan")
    console.print()

    return memory


# ── 创建智能体 ──────────────────────────────────────────────

def create_default_registry(model_adapters=None, default_model=None, memory=None, style_extra=""):
    from ecnuclaw.core.agent import Agent, AgentRegistry
    from ecnuclaw.core.memory import MemoryStore
    from ecnuclaw.education.heads import HEADSTemplate
    from ecnuclaw.tools.registry import ToolRegistry
    from ecnuclaw.tools.builtin.calculator import CalculatorTool
    from ecnuclaw.tools.builtin.knowledge import KnowledgeTool
    from ecnuclaw.tools.builtin.dictionary import DictionaryTool
    from ecnuclaw.tools.builtin.timer import TimerTool

    registry = AgentRegistry()
    shared_memory = memory or MemoryStore()

    default_adapter = None
    if model_adapters and default_model:
        default_adapter = model_adapters.get(default_model)
    qwen_adapter = (model_adapters or {}).get("qwen", default_adapter)

    def _make_prompt(base_fn):
        prompt = base_fn()
        if style_extra:
            prompt += f"\n\n{style_extra}"
        return prompt

    # 数学
    math_tools = ToolRegistry()
    math_tools.register(CalculatorTool())
    math_tools.register(KnowledgeTool())
    registry.register(Agent(name="math", system_prompt=_make_prompt(HEADSTemplate.math_prompt),
        tools=math_tools, model_adapter=default_adapter, memory=shared_memory))

    # 语文
    chinese_tools = ToolRegistry()
    chinese_tools.register(DictionaryTool())
    chinese_tools.register(KnowledgeTool())
    registry.register(Agent(name="chinese", system_prompt=_make_prompt(HEADSTemplate.chinese_prompt),
        tools=chinese_tools, model_adapter=qwen_adapter, memory=shared_memory))

    # 科学
    science_tools = ToolRegistry()
    science_tools.register(KnowledgeTool())
    science_tools.register(TimerTool())
    registry.register(Agent(name="science", system_prompt=_make_prompt(HEADSTemplate.science_prompt),
        tools=science_tools, model_adapter=default_adapter, memory=shared_memory))

    # 万能
    general_tools = ToolRegistry()
    general_tools.register(CalculatorTool())
    general_tools.register(DictionaryTool())
    general_tools.register(KnowledgeTool())
    general_tools.register(TimerTool())
    registry.register(Agent(name="general", system_prompt=_make_prompt(HEADSTemplate.general_prompt),
        tools=general_tools, model_adapter=default_adapter, memory=shared_memory))

    return registry


def _get_style_extra(style_name):
    for s in _STYLE_OPTIONS:
        if s["name"] == style_name:
            return s.get("extra", "")
    return _STYLE_OPTIONS[0].get("extra", "")


# ── 主入口 ──────────────────────────────────────────────

def main():
    # 支持 ecnuclaw setup 命令
    if len(sys.argv) > 1 and sys.argv[1] in ("setup", "init", "config"):
        from rich.console import Console
        console = Console()
        _print_banner(console)
        try:
            run_setup_wizard(console)
        except KeyboardInterrupt:
            console.print("\n\n  [yellow]再见！[/]")
            console.print()
        return

    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from rich.console import Console
    from rich.markdown import Markdown

    console = Console()
    cfg = _load_config()

    # ── 1. 欢迎界面 ──
    _print_banner(console)

    # ── 2. 检查是否需要初始化 ──
    needs_setup = not cfg.get("initialized") or not cfg.get("model", {}).get("default")

    memory = None
    if needs_setup:
        try:
            memory = run_setup_wizard(console)
        except KeyboardInterrupt:
            console.print("\n\n  [yellow]再见！[/]")
            console.print()
            return
        cfg = _load_config()

    # ── 3. 扫描模型 ──
    # 先加载 .env 文件
    env_file = _CONFIG_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    model_adapters, default_model = _scan_model_adapters()

    if not model_adapters and not needs_setup:
        console.print("  [yellow]⚠ 还没连上 AI 大脑[/]")
        console.print("  输入 [bold]/设置[/bold] 可以重新配置")
        console.print()

    # ── 4. 创建小伙伴 ──
    style_extra = _get_style_extra(cfg.get("style", "warm"))
    registry = create_default_registry(
        model_adapters=model_adapters,
        default_model=default_model,
        memory=memory,
        style_extra=style_extra,
    )
    router = IntentRouter()

    # ── 5. 欢迎回来 ──
    student_name = cfg.get("student_name", "")
    shared_memory = registry.get("general").memory
    if not needs_setup:
        profile = shared_memory.get_student_profile()
        if profile:
            student_name = profile.get("名字", student_name)
        if student_name:
            console.print(f"  [bright_cyan]{student_name}，欢迎回来！[/]")
        else:
            console.print(f"  [bright_cyan]欢迎回来！[/]")
        console.print()

    # ── 6. 主循环 ──
    prompt_name = student_name if student_name else "你"
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    session = PromptSession(history=FileHistory(str(_CONFIG_DIR / "history")))

    active_agent = registry.get("general")
    registry._active_agent = "general"

    console.print("  [dim]输入问题开始聊天 · 输入 /帮助 查看命令 · 按 Ctrl+C 退出[/]")
    console.print()

    ctrl_c_count = 0

    while True:
        try:
            icons = {"math": "📐", "chinese": "📝", "science": "🔬", "general": "🌟"}
            icon = icons.get(registry._active_agent, "🌟")
            user_input = session.prompt(f"  {icon} {prompt_name} > ")
            if not user_input.strip():
                continue

            stripped = user_input.strip()
            ctrl_c_count = 0  # 正常输入，重置计数

            # ── 命令 ──
            if stripped in ("/quit", "/exit", "/q", "/再见", "/退出"):
                break

            if stripped in ("/help", "/帮助"):
                console.print()
                console.print("  [bold bright_cyan]╭────────── 命令列表 ──────────╮[/]")
                console.print("  [bright_cyan]│[/]")
                console.print("  [bright_cyan]│[/]  [cyan]/帮助[/]         显示这个列表")
                console.print("  [bright_cyan]│[/]  [cyan]/切换 数学[/]     找数学小伙伴来帮忙")
                console.print("  [bright_cyan]│[/]  [cyan]/小伙伴[/]       看看现在有哪些小伙伴")
                console.print("  [bright_cyan]│[/]  [cyan]/我的信息[/]     看看我知道关于你的事")
                console.print("  [bright_cyan]│[/]  [cyan]/设置[/]         重新配置（模型、风格等）")
                console.print("  [bright_cyan]│[/]  [cyan]/重置[/]         清空这轮对话重新开始")
                console.print("  [bright_cyan]│[/]  [cyan]/再见[/]         退出 ECNUClaw")
                console.print("  [bright_cyan]│[/]")
                console.print("  [bright_cyan]│[/]  [dim]也可以直接按 Ctrl+C 退出[/]")
                console.print("  [bright_cyan]╰──────────────────────────────╯[/]")
                console.print()
                continue

            if stripped in ("/小伙伴", "/agents"):
                console.print()
                for name in registry.list_agents():
                    marker = " [bright_cyan]← 当前[/]" if name == registry._active_agent else ""
                    console.print(f"    {_SUBJECT_LABELS.get(name, name)}{marker}")
                console.print()
                continue

            if stripped.startswith("/切换 ") or stripped.startswith("/switch "):
                target = stripped.split(maxsplit=1)[1].strip() if len(stripped.split()) > 1 else ""
                name_map = {"数学": "math", "语文": "chinese", "科学": "science", "通用": "general"}
                agent_key = name_map.get(target, target)
                try:
                    active_agent = registry.switch_to(agent_key)
                    console.print(f"  [green]已切换到 {_SUBJECT_LABELS.get(agent_key, agent_key)}[/]")
                except KeyError:
                    console.print("  [red]没找到，试试：数学、语文、科学、通用[/]")
                continue

            if stripped in ("/我的信息", "/profile"):
                profile = active_agent.memory.get_student_profile()
                if profile:
                    _print_box(console, [f"{k}：{v}" for k, v in profile.items()], "bright_cyan")
                else:
                    console.print("  [dim]还不了解你呢，直接问问题吧～[/]")
                console.print()
                continue

            if stripped in ("/设置", "/setup"):
                console.print()
                try:
                    run_setup_wizard(console)
                    cfg = _load_config()
                    style_extra = _get_style_extra(cfg.get("style", "warm"))
                    if env_file.exists():
                        for line in env_file.read_text(encoding="utf-8").splitlines():
                            if "=" in line and not line.startswith("#"):
                                k, v = line.split("=", 1)
                                os.environ.setdefault(k.strip(), v.strip())
                    model_adapters, default_model = _scan_model_adapters()
                    registry = create_default_registry(
                        model_adapters=model_adapters, default_model=default_model,
                        memory=shared_memory, style_extra=style_extra)
                    active_agent = registry.get(registry._active_agent or "general")
                    _print_ok(console, "设置已更新！继续聊天吧～")
                except Exception as e:
                    console.print(f"  [red]设置过程出了问题：{e}[/]")
                    console.print("  [yellow]可以试试重新输入 /设置[/]")
                console.print()
                continue

            if stripped in ("/重置", "/reset"):
                active_agent.reset()
                _print_ok(console, "对话已清空！")
                continue

            # ── 路由 ──
            context = {"active_agent": registry._active_agent, "history": active_agent._history[-6:]}
            decision = router.classify(user_input, context=context)
            if decision.target_agent != registry._active_agent:
                try:
                    active_agent = registry.switch_to(decision.target_agent)
                    _print_hint(console, f"→ 帮你找来了 {_SUBJECT_LABELS.get(decision.target_agent, '')}")
                except KeyError:
                    pass

            # ── 回复 ──
            if not model_adapters:
                console.print("  [yellow]还没连上 AI 大脑，输入 [bold]/设置[/bold] 来配置[/]")
                console.print()
                continue

            collected = []
            try:
                console.print()
                from rich.live import Live
                from rich.text import Text
                with Live(Text(), console=console, refresh_per_second=8, transient=True) as live:
                    for chunk in active_agent.chat_stream(user_input):
                        collected.append(chunk)
                        live.update(Text("".join(collected)))
                console.print(Markdown("".join(collected)))
                console.print()
            except KeyboardInterrupt:
                if collected:
                    console.print(Markdown("".join(collected)))
                console.print("\n  [yellow]已中断回答[/]")
                console.print()
            except Exception as e:
                if collected:
                    console.print(Markdown("".join(collected)))
                    console.print()
                else:
                    console.print(f"\n  [red]回答出了点问题：{e}[/]")
                    console.print("  [dim]你可以重试、输入 /重置 清空对话、或输入 /设置 换个模型[/]")
                    console.print()

        except KeyboardInterrupt:
            ctrl_c_count += 1
            if ctrl_c_count >= 2:
                # 连按两次 Ctrl+C，直接退出
                console.print()
                break
            else:
                # 第一次 Ctrl+C，提示再按一次退出
                console.print()
                console.print("  [yellow]再按一次 Ctrl+C 退出，或继续输入问题[/]")
                console.print()

        except EOFError:
            break

    # ── 再见 ──
    goodbye = f"再见{prompt_name}！我记住你了，下次见～"
    console.print()
    _print_box(console, [goodbye], "bright_blue")
    console.print()


if __name__ == "__main__":
    main()
