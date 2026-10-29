"""Click timing independent of the desktop and mouse backend."""

from dataclasses import dataclass
from datetime import datetime
import math

MOUSE_ACTIONS = ('left', 'right', 'middle')
KEY_NAMES = frozenset(('enter', 'space', 'tab', 'esc', 'backspace', 'delete', 'insert',
                       'home', 'end', 'page_up', 'page_down', 'up', 'down', 'left', 'right',
                       'ctrl', 'alt', 'shift', 'cmd', 'caps_lock') + tuple(f'f{i}' for i in range(1, 25)))
KEY_ALIASES = {'escape': 'esc', 'return': 'enter', 'spacebar': 'space', 'control': 'ctrl',
               'windows': 'cmd', 'win': 'cmd', 'super': 'cmd', 'pgup': 'page_up', 'pgdn': 'page_down',
               'arrowup': 'up', 'arrowdown': 'down', 'arrowleft': 'left', 'arrowright': 'right', 'plus': '+'}


def parse_keys(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Enter a keyboard key or shortcut, such as enter, space, or ctrl+s.')
    parts = tuple(KEY_ALIASES.get(p.strip().lower(), p.strip().lower()) for p in value.split('+'))
    if (len(parts) > 5 or len(set(parts)) != len(parts)
            or any(p not in ('ctrl', 'alt', 'shift', 'cmd') for p in parts[:-1])
            or not (parts[-1] in KEY_NAMES or (len(parts[-1]) == 1 and parts[-1].isprintable() and not parts[-1].isspace()))):
        raise ValueError('Use a character, a named key (enter, space, arrows, F1-F24), or a shortcut like ctrl+shift+s.')
    return parts


def validate_action(action, key):
    if action not in (*MOUSE_ACTIONS, 'key'):
        raise ValueError('Choose left, right, middle, or keyboard as the action.')
    if not isinstance(key, str):
        raise ValueError('The keyboard key must be text.')
    if action == 'key':
        parse_keys(key)


def read_datetime(date, clock, label):
    try:
        return datetime.strptime(f"{date.strip()} {clock.strip()}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError(f"{label}: use YYYY-MM-DD and HH:MM:SS (24-hour time).") from None


def read_seconds(value, label, multiplier=1, minimum=0):
    try:
        seconds = float(value) * multiplier
    except ValueError:
        raise ValueError(f"{label}: enter a number.") from None
    if not math.isfinite(seconds) or seconds < minimum or seconds > 315360000:
        raise ValueError(f"{label}: enter a value between {minimum:g} and 315360000 seconds.")
    return seconds


@dataclass(frozen=True)
class ClickStep:
    x: int
    y: int
    delay: float = 1
    action: str = 'left'
    key: str = ''

    def __post_init__(self):
        validate_action(self.action, self.key)
        if type(self.x) is not int or type(self.y) is not int:
            raise ValueError('Step coordinates must be whole numbers.')
        if not math.isfinite(self.delay) or not 0.05 <= self.delay <= 315360000:
            raise ValueError('Each step delay must be between 0.05 and 315360000 seconds.')

    @property
    def point(self):
        return self.x, self.y


@dataclass(frozen=True)
class ClickPlan:
    start_at: datetime
    interval: float
    limit: int | None = 1
    end_at: datetime | None = None
    pattern: tuple[ClickStep, ...] = ()
    action: str = 'left'
    key: str = ''

    def __post_init__(self):
        validate_action(self.action, self.key)
        if not math.isfinite(self.interval) or self.interval < 0.05:
            raise ValueError("Delay between clicks must be at least 0.05 seconds.")
        if self.limit is not None and (not isinstance(self.limit, int) or self.limit < 1):
            raise ValueError("Click count must be a whole number of at least 1.")
        if self.end_at is not None and self.end_at <= self.start_at:
            raise ValueError("End date and time must be later than the start.")
        if self.limit is None and self.end_at is None:
            raise ValueError("Choose a click count or an end date and time.")


class ClickRun:
    def __init__(self, plan):
        self.plan = plan
        self.completed = 0
        self.next_due = None
        self.active = True

    @property
    def current_step(self):
        if self.plan.pattern:
            return self.plan.pattern[self.completed % len(self.plan.pattern)]
        return None

    def ready(self, now, monotonic):
        # End time is exclusive: no click may start at or after it.
        if self.plan.end_at is not None and now >= self.plan.end_at:
            self.active = False
        if not self.active:
            return False
        if self.next_due is None:
            return now >= self.plan.start_at
        return monotonic >= self.next_due

    def record_click(self, monotonic):
        delay = self.current_step.delay if self.current_step is not None else self.plan.interval
        self.completed += 1
        if self.plan.limit is not None and self.completed >= self.plan.limit:
            self.active = False
        # Delay from completion; never replay a backlog after a busy UI or sleep.
        self.next_due = monotonic + delay

    def remaining(self, now, monotonic):
        if self.next_due is None:
            return max(0, (self.plan.start_at - now).total_seconds())
        return max(0, self.next_due - monotonic)
