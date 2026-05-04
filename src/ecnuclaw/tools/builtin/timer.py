import time
import uuid

from ecnuclaw.tools.base import Tool, ToolResult

_active_timers: dict[str, dict] = {}


class TimerTool(Tool):
    name = "timer"
    description = "Study timer and pomodoro tool. Actions: start_timer (start counting), stop_timer (stop and return elapsed time), pomodoro (25-minute focused study session), status (check active timer)."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["start_timer", "stop_timer", "pomodoro", "status"],
                "description": "Timer action to perform.",
            },
            "duration_minutes": {
                "type": "integer",
                "description": "Duration in minutes (used with start_timer for custom duration).",
            },
            "label": {
                "type": "string",
                "description": "Optional label for this timer session, e.g. 'math homework'.",
            },
        },
        "required": ["action"],
    }

    def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action", "").strip()
        duration_minutes = kwargs.get("duration_minutes")
        label = kwargs.get("label", "").strip()

        handlers = {
            "start_timer": self._start_timer,
            "stop_timer": self._stop_timer,
            "pomodoro": self._pomodoro,
            "status": self._status,
        }

        handler = handlers.get(action)
        if handler is None:
            return ToolResult(
                success=False, output="",
                error=f"Unknown action '{action}'. Available: {', '.join(handlers.keys())}",
            )

        return handler(duration_minutes=duration_minutes, label=label)

    def _start_timer(self, *, duration_minutes=None, label="") -> ToolResult:
        timer_id = str(uuid.uuid4())[:8]
        now = time.time()
        _active_timers[timer_id] = {
            "start_time": now,
            "label": label or "unnamed",
            "duration_minutes": duration_minutes,
            "pomodoro": False,
        }
        duration_msg = f" for {duration_minutes} minutes" if duration_minutes else ""
        label_msg = f" [{label}]" if label else ""
        return ToolResult(
            success=True,
            output=f"Timer started{label_msg} (id: {timer_id}){duration_msg}.",
            metadata={"timer_id": timer_id, "start_time": now, "label": label},
        )

    def _stop_timer(self, *, duration_minutes=None, label="") -> ToolResult:
        if not _active_timers:
            return ToolResult(success=False, output="", error="No active timers to stop.")

        target_id = None
        if label:
            for tid, info in _active_timers.items():
                if info["label"] == label:
                    target_id = tid
                    break
        if target_id is None:
            target_id = list(_active_timers.keys())[-1]

        timer_info = _active_timers.pop(target_id)
        elapsed_seconds = time.time() - timer_info["start_time"]
        elapsed_minutes = elapsed_seconds / 60
        elapsed_display = self._format_duration(elapsed_seconds)

        timer_label = timer_info["label"]
        pomodoro_tag = " (pomodoro)" if timer_info.get("pomodoro") else ""

        was_target_duration = timer_info.get("duration_minutes")
        hint = ""
        if was_target_duration:
            target_seconds = was_target_duration * 60
            if elapsed_seconds >= target_seconds:
                hint = " Target reached!"
            else:
                remaining = target_seconds - elapsed_seconds
                hint = f" {self._format_duration(remaining)} remaining of {was_target_duration}min target."

        return ToolResult(
            success=True,
            output=f"Timer '{timer_label}'{pomodoro_tag} stopped. Elapsed: {elapsed_display}.{hint}",
            metadata={
                "timer_id": target_id,
                "elapsed_seconds": round(elapsed_seconds, 1),
                "elapsed_minutes": round(elapsed_minutes, 2),
                "label": timer_label,
                "pomodoro": timer_info.get("pomodoro", False),
            },
        )

    def _pomodoro(self, *, duration_minutes=None, label="") -> ToolResult:
        timer_id = str(uuid.uuid4())[:8]
        now = time.time()
        pomodoro_minutes = 25
        pomodoro_label = label or "pomodoro"

        _active_timers[timer_id] = {
            "start_time": now,
            "label": pomodoro_label,
            "duration_minutes": pomodoro_minutes,
            "pomodoro": True,
        }

        return ToolResult(
            success=True,
            output=f"Pomodoro started [{pomodoro_label}] (id: {timer_id}): 25 minutes of focused study. Call stop_timer when done or after 25 minutes.",
            metadata={
                "timer_id": timer_id,
                "start_time": now,
                "duration_minutes": pomodoro_minutes,
                "label": pomodoro_label,
                "pomodoro": True,
            },
        )

    def _status(self, *, duration_minutes=None, label="") -> ToolResult:
        if not _active_timers:
            return ToolResult(success=True, output="No active timers.", metadata={"active_count": 0})

        now = time.time()
        lines = [f"Active timers ({len(_active_timers)}):"]
        for tid, info in _active_timers.items():
            elapsed = now - info["start_time"]
            elapsed_str = self._format_duration(elapsed)
            pomo_tag = " [POMODORO]" if info.get("pomodoro") else ""
            duration_info = f" (target: {info['duration_minutes']}min)" if info.get("duration_minutes") else ""
            lines.append(f"  - {tid}: '{info['label']}'{pomo_tag} — elapsed {elapsed_str}{duration_info}")

        return ToolResult(
            success=True,
            output="\n".join(lines),
            metadata={"active_count": len(_active_timers)},
        )

    @staticmethod
    def _format_duration(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        if mins >= 60:
            hours = mins // 60
            mins = mins % 60
            return f"{hours}h {mins}m {secs}s"
        return f"{mins}m {secs}s"
