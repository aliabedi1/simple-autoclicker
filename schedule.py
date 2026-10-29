"""Click timing independent of the desktop and mouse backend."""

from dataclasses import dataclass
from datetime import datetime
import math


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

    def __post_init__(self):
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

    def __post_init__(self):
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
