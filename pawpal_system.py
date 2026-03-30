"""
PawPal+ — Logic Layer
All backend classes live here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
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


# Clock boundaries for each window (24-h hours)
_WINDOW_BOUNDS: dict[TimeWindow, tuple[int, int]] = {
    TimeWindow.MORNING:   (6,  12),
    TimeWindow.AFTERNOON: (12, 18),
    TimeWindow.EVENING:   (18, 22),
    TimeWindow.ANYTIME:   (6,  22),
}

# Sort order for time windows: window-specific tasks are placed first so they
# land inside their preferred slot before ANYTIME tasks fill it.
_WINDOW_SORT_ORDER: dict[TimeWindow, int] = {
    TimeWindow.MORNING:   0,
    TimeWindow.AFTERNOON: 1,
    TimeWindow.EVENING:   2,
    TimeWindow.ANYTIME:   3,
}

_BUFFER_MINUTES = 5   # gap inserted between consecutive tasks


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet care activity."""
    title: str
    category: str                           # e.g. "feeding", "walk", "medication"
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    preferred_time: TimeWindow = TimeWindow.ANYTIME
    completed: bool = False
    notes: str = ""

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def is_due(self) -> bool:
        """Return True if the task has not yet been completed."""
        return not self.completed

    def __str__(self) -> str:
        status = "done" if self.completed else "pending"
        return (
            f"[{status}] {self.title} "
            f"({self.duration_minutes} min, {self.priority.name}, {self.preferred_time.value})"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Stores pet details and owns a list of care tasks."""
    name: str
    species: str
    breed: str = ""
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task by title (first match)."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def pending_tasks(self) -> list[Task]:
        """Return only tasks that are not yet completed."""
        return [t for t in self.tasks if t.is_due()]

    def __str__(self) -> str:
        return f"{self.name} ({self.species})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Manages multiple pets and exposes their tasks."""
    name: str
    available_hours: float = 3.0
    day_start_hour: int = 8
    day_end_hour: int = 21
    pets: list[Pet] = field(default_factory=list)

    @property
    def available_minutes(self) -> int:
        """Total care-time budget for the day in minutes."""
        return int(self.available_hours * 60)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove a pet by name (first match)."""
        self.pets = [p for p in self.pets if p.name != name]

    def get_all_tasks(self) -> list[Task]:
        """Collect every task across all pets (completed and pending)."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def get_pending_tasks(self) -> list[Task]:
        """Collect only incomplete tasks across all pets."""
        pending: list[Task] = []
        for pet in self.pets:
            pending.extend(pet.pending_tasks())
        return pending

    def __str__(self) -> str:
        return f"{self.name} ({len(self.pets)} pet(s), {self.available_hours:.1f} h available)"


# ---------------------------------------------------------------------------
# Output data classes
# ---------------------------------------------------------------------------

@dataclass
class ScheduledTask:
    """A Task placed at a concrete time slot with an explanation."""
    task: Task
    start_time: datetime
    end_time: datetime
    reason: str = ""

    @property
    def start_str(self) -> str:
        """Return the start time formatted as a human-readable string."""
        return self.start_time.strftime("%I:%M %p")

    @property
    def end_str(self) -> str:
        """Return the end time formatted as a human-readable string."""
        return self.end_time.strftime("%I:%M %p")


@dataclass
class SkippedTask:
    """A Task that could not be scheduled, with a reason."""
    task: Task
    reason: str = ""


@dataclass
class DailyPlan:
    """The full output of a scheduling run."""
    date: str
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    skipped_tasks: list[SkippedTask] = field(default_factory=list)

    def total_scheduled_minutes(self) -> int:
        """Sum of durations for all scheduled tasks."""
        return sum(st.task.duration_minutes for st in self.scheduled_tasks)

    def summary(self) -> str:
        """Human-readable plan for CLI or display output."""
        lines = [
            "=" * 50,
            f"  PawPal+ Daily Plan  |  {self.date}",
            "=" * 50,
        ]

        if self.scheduled_tasks:
            lines.append("\nSCHEDULED")
            lines.append("-" * 40)
            for st in self.scheduled_tasks:
                lines.append(
                    f"  {st.start_str} – {st.end_str}  "
                    f"[{st.task.priority.name:8s}]  {st.task.title}"
                )
                lines.append(f"    Why: {st.reason}")
        else:
            lines.append("\n  No tasks could be scheduled.")

        if self.skipped_tasks:
            lines.append("\nSKIPPED")
            lines.append("-" * 40)
            for sk in self.skipped_tasks:
                lines.append(f"  - {sk.task.title}  →  {sk.reason}")

        lines.append(f"\n  Total care time: {self.total_scheduled_minutes()} min")
        lines.append("=" * 50)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler — the "brain"
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Retrieves tasks from an Owner's pets, sorts them by priority and preferred
    time window, then fits them into the day within the Owner's time budget.

    How Scheduler talks to Owner
    ----------------------------
    Scheduler calls owner.get_pending_tasks() to collect every incomplete task
    across all pets in one flat list.  It never reaches into pets directly —
    all pet access goes through the Owner interface.

    Algorithm
    ---------
    1. Ask owner for all pending tasks.
    2. Sort: highest Priority first; ties broken by TimeWindow order
       (Morning → Afternoon → Evening → Anytime).
    3. Walk the sorted list with a current_time cursor.
       For each task:
         a. Skip if time budget is exhausted.
         b. If task has a preferred window, start at max(current_time, window_open).
            Fall back to current_time if the window has already passed.
         c. Skip if task doesn't fit before day_end.
         d. Commit the slot; advance current_time by duration + buffer.
    4. Return a DailyPlan with scheduled and skipped lists.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def _sorted_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks: highest priority first, then by preferred window."""
        return sorted(
            tasks,
            key=lambda t: (-t.priority.value, _WINDOW_SORT_ORDER[t.preferred_time]),
        )

    def _window_bounds(self, window: TimeWindow, base: datetime) -> tuple[datetime, datetime]:
        """Return (open, close) datetimes for a time window on a given date."""
        lo, hi = _WINDOW_BOUNDS[window]
        open_dt  = base.replace(hour=lo, minute=0, second=0, microsecond=0)
        close_dt = base.replace(hour=hi, minute=0, second=0, microsecond=0)
        return open_dt, close_dt

    def build_plan(self, date: Optional[str] = None) -> DailyPlan:
        """
        Build and return a DailyPlan for the given date (defaults to today).

        Parameters
        ----------
        date : str, optional
            ISO date string "YYYY-MM-DD".
        """
        if date is None:
            date = datetime.today().strftime("%Y-%m-%d")

        base     = datetime.strptime(date, "%Y-%m-%d")
        day_start = base.replace(hour=self.owner.day_start_hour, minute=0, second=0, microsecond=0)
        day_end   = base.replace(hour=self.owner.day_end_hour,   minute=0, second=0, microsecond=0)

        plan         = DailyPlan(date=date)
        current_time = day_start

        # Retrieve all pending tasks through the Owner interface
        pending = self.owner.get_pending_tasks()

        for task in self._sorted_tasks(pending):

            # ── budget check ──────────────────────────────────────────────
            used = plan.total_scheduled_minutes()
            remaining_budget = self.owner.available_minutes - used

            if task.duration_minutes > remaining_budget:
                plan.skipped_tasks.append(SkippedTask(
                    task=task,
                    reason=(
                        f"Needs {task.duration_minutes} min but only "
                        f"{remaining_budget} min of budget left"
                    ),
                ))
                continue

            # ── time-window placement ─────────────────────────────────────
            if task.preferred_time != TimeWindow.ANYTIME:
                win_open, win_close = self._window_bounds(task.preferred_time, base)
                candidate_start = max(current_time, win_open)
                candidate_end   = candidate_start + timedelta(minutes=task.duration_minutes)

                if candidate_end <= win_close and candidate_end <= day_end:
                    task_start = candidate_start
                    task_end   = candidate_end
                    reason = (
                        f"Fits in preferred {task.preferred_time.value} window "
                        f"({task.priority.name} priority)"
                    )
                else:
                    # Preferred window unavailable — fall back to current pointer
                    task_start = current_time
                    task_end   = task_start + timedelta(minutes=task.duration_minutes)

                    if task_end > day_end:
                        plan.skipped_tasks.append(SkippedTask(
                            task=task,
                            reason=(
                                f"Preferred {task.preferred_time.value} window passed "
                                "and task doesn't fit in remaining day"
                            ),
                        ))
                        continue

                    reason = (
                        f"Preferred {task.preferred_time.value} window unavailable — "
                        f"moved to next open slot ({task.priority.name} priority)"
                    )
            else:
                task_start = current_time
                task_end   = task_start + timedelta(minutes=task.duration_minutes)

                if task_end > day_end:
                    plan.skipped_tasks.append(SkippedTask(
                        task=task,
                        reason="Doesn't fit before end of day",
                    ))
                    continue

                reason = f"Scheduled at next available slot ({task.priority.name} priority)"

            # ── commit slot ───────────────────────────────────────────────
            plan.scheduled_tasks.append(ScheduledTask(
                task=task,
                start_time=task_start,
                end_time=task_end,
                reason=reason,
            ))
            current_time = task_end + timedelta(minutes=_BUFFER_MINUTES)

        return plan