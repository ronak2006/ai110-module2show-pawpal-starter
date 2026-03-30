"""
PawPal+ — Logic Layer
All backend classes live here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TimeWindow(Enum):
    MORNING = "morning"      # 06:00 – 12:00
    AFTERNOON = "afternoon"  # 12:00 – 18:00
    EVENING = "evening"      # 18:00 – 22:00
    ANYTIME = "anytime"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    breed: str = ""
    age: int = 0


@dataclass
class Owner:
    name: str
    available_hours: float = 3.0
    day_start_hour: int = 8
    day_end_hour: int = 21

    @property
    def available_minutes(self) -> int:
        pass  # TODO


@dataclass
class Task:
    title: str
    category: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    preferred_time: TimeWindow = TimeWindow.ANYTIME
    notes: str = ""


@dataclass
class ScheduledTask:
    task: Task
    start_time: datetime
    end_time: datetime
    reason: str = ""


@dataclass
class SkippedTask:
    task: Task
    reason: str = ""


@dataclass
class DailyPlan:
    date: str
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    skipped_tasks: list[SkippedTask] = field(default_factory=list)

    def total_scheduled_minutes(self) -> int:
        pass  # TODO

    def summary(self) -> str:
        pass  # TODO


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        pass  # TODO

    def build_plan(self, date: Optional[str] = None) -> DailyPlan:
        pass  # TODO