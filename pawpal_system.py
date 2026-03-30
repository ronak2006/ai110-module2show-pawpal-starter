"""
PawPal+ — Logic Layer
All backend classes live here.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
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


def sort_tasks_by_time(tasks: list["Task"]) -> list["Task"]:
    """Return a new list of tasks sorted chronologically by preferred time window.

    Uses Python's built-in ``sorted()`` with a two-element tuple key so the
    ordering is stable and the original list is never mutated.

    Sort keys
    ---------
    1. **Window open hour** *(primary)* — maps each ``TimeWindow`` to its
       opening clock hour via ``_WINDOW_BOUNDS``:
       MORNING → 6, AFTERNOON → 12, EVENING → 18, ANYTIME → 6.
    2. **Priority descending** *(secondary)* — within the same window,
       higher-priority tasks appear first (``-t.priority.value``).

    Parameters
    ----------
    tasks : list[Task]
        Any flat list of ``Task`` objects, in any order.

    Returns
    -------
    list[Task]
        A new sorted list; the input list is unchanged.
    """
    return sorted(
        tasks,
        key=lambda t: (
            _WINDOW_BOUNDS[t.preferred_time][0],   # open hour, e.g. 6 / 12 / 18
            -t.priority.value,                      # higher priority first within window
        ),
    )


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
    recurrence: Optional[str] = None        # None | "daily" | "weekly"
    next_due: Optional[str] = None          # "YYYY-MM-DD"; None means always due today

    def generate_next_occurrence(self) -> Optional["Task"]:
        """Create and return a new Task instance for the next recurrence cycle.

        Uses ``timedelta`` to advance the due date:

        * ``"daily"``  → ``next_due + timedelta(days=1)``
        * ``"weekly"`` → ``next_due + timedelta(days=7)``
        * ``None``     → returns ``None`` (one-time task, no next occurrence)

        The returned Task is a fresh object — the original task remains
        unchanged — so callers can choose where and when to queue it.
        """
        if self.recurrence is None:
            return None
        base = (
            datetime.strptime(self.next_due, "%Y-%m-%d")
            if self.next_due
            else datetime.today()
        )
        days_ahead = 1 if self.recurrence == "daily" else 7
        new_due = (base + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        # dataclasses.replace() copies every field from self automatically;
        # only the two changed fields need to be named explicitly.
        # Benefit: adding a new field to Task never breaks this method.
        return replace(self, completed=False, next_due=new_due)

    def mark_complete(self) -> Optional["Task"]:
        """Mark this occurrence as done and return the next instance if recurring.

        Always sets ``completed = True`` on the current Task so it is
        permanently retired from the active queue.  For recurring tasks a brand-
        new Task object is returned with ``next_due`` advanced via ``timedelta``
        — callers (typically ``Pet.complete_task()``) are responsible for
        appending it to the pet's task list so future schedules pick it up.

        Returns
        -------
        Task | None
            Next occurrence for recurring tasks; ``None`` for one-time tasks.
        """
        self.completed = True
        return self.generate_next_occurrence()

    def is_due(self) -> bool:
        """Return True if the task is pending and due on or before today.

        * One-time tasks: active while ``completed=False``.
        * Recurring tasks: a fresh instance has ``completed=False`` and a
          concrete ``next_due``; it becomes active once that date arrives.
        """
        if self.completed:
            return False
        if self.next_due is None:
            return True
        today = datetime.today().strftime("%Y-%m-%d")
        return self.next_due <= today

    def __str__(self) -> str:
        status = "done" if self.completed else "pending"
        recur_label = f", recurs {self.recurrence}" if self.recurrence else ""
        due_label   = f", next due {self.next_due}" if self.next_due else ""
        return (
            f"[{status}] {self.title} "
            f"({self.duration_minutes} min, {self.priority.name}, "
            f"{self.preferred_time.value}{recur_label}{due_label})"
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

    def complete_task(self, title: str) -> bool:
        """Mark the first pending task with this title as done.

        If the task recurs, ``Task.mark_complete()`` returns a brand-new Task
        instance with ``next_due`` advanced by the appropriate ``timedelta``
        (1 day for daily, 7 days for weekly).  That instance is automatically
        appended here so future calls to ``pending_tasks()`` and
        ``build_plan()`` will pick it up without any extra wiring.

        Parameters
        ----------
        title : str
            Title of the task to complete (first pending match wins).

        Returns
        -------
        bool
            ``True`` if a matching pending task was found and completed;
            ``False`` if no such task exists.
        """
        for task in self.tasks:
            if task.title == title and not task.completed:
                next_occurrence = task.mark_complete()  # retires this instance
                if next_occurrence is not None:
                    self.tasks.append(next_occurrence)  # queue the new instance
                return True
        return False                                     # title not found / already done

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

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        status: str = "all",
    ) -> list[Task]:
        """Return tasks filtered by pet name and/or completion status.

        Combines both filters with logical AND — e.g. passing both ``pet_name``
        and ``status="pending"`` returns only tasks for that pet that are still
        outstanding.  Recurring tasks are evaluated with ``Task.is_due()`` so
        an instance whose ``next_due`` date is in the future is treated as
        "done for today" even though its ``completed`` flag is ``False``.

        Parameters
        ----------
        pet_name : str, optional
            When provided, only tasks belonging to the pet with this exact name
            are included.  ``None`` (default) includes all pets.
        status : str
            ``"all"``     — every task regardless of state (default).
            ``"pending"`` — only tasks where ``Task.is_due()`` returns ``True``.
            ``"done"``    — only tasks where ``Task.is_due()`` returns ``False``
                            (permanently completed or recurring-but-done-today).

        Returns
        -------
        list[Task]
            Flat list of matching tasks across all qualifying pets.
        """
        result: list[Task] = []
        for pet in self.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for t in pet.tasks:
                # is_due() handles both one-time (completed flag) and recurring
                # (next_due date check) tasks in a single, consistent call.
                if status == "pending" and not t.is_due():
                    continue
                if status == "done" and t.is_due():
                    continue
                result.append(t)
        return result

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
    conflict_warnings: list[str] = field(default_factory=list)

    def total_scheduled_minutes(self) -> int:
        """Sum of durations for all scheduled tasks."""
        return sum(st.task.duration_minutes for st in self.scheduled_tasks)

    def sort_by_time(self) -> None:
        """Sort ``scheduled_tasks`` in-place by concrete start time (earliest first).

        Uses a ``lambda`` key on ``start_time`` (a ``datetime`` object) so that
        any tasks added to the plan out of chronological order are corrected
        before display — e.g. an 08:00 task always appears before 10:30.

        The standard ``Scheduler.build_plan()`` already places tasks in order,
        so this method is most useful when ``ScheduledTask`` entries are
        injected manually or when two plans are merged.

        Modifies the list in-place; returns ``None``.
        """
        self.scheduled_tasks.sort(key=lambda st: st.start_time)

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

        if self.conflict_warnings:
            lines.append("\nCONFLICTS DETECTED")
            lines.append("-" * 40)
            for w in self.conflict_warnings:
                lines.append(f"  ⚠  {w}")

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

    @staticmethod
    def detect_conflicts(plan: DailyPlan) -> list[str]:
        """Scan a ``DailyPlan`` for overlapping time slots and return warning strings.

        This is a **lightweight, non-raising** validator: it never modifies the
        plan, never throws an exception, and returns an empty list when the
        schedule is clean.  Callers choose how (and whether) to surface the
        warnings — the scheduler itself stores them in ``plan.conflict_warnings``
        after every ``build_plan()`` call.

        Algorithm
        ---------
        1. Sort ``scheduled_tasks`` by ``start_time`` (ascending).
        2. Walk adjacent pairs ``(A, B)`` using ``zip(slots, slots[1:])``.
        3. If ``A.end_time > B.start_time`` the slots overlap; compute the
           overlap duration in minutes and append a human-readable warning.
        4. Return the complete warning list (may be empty).

        Note: the standard scheduler uses a linear time cursor that naturally
        prevents double-booking, so conflicts appear only when tasks are injected
        manually or when window fall-back logic places two tasks in the same slot.

        Parameters
        ----------
        plan : DailyPlan
            The completed plan to validate.

        Returns
        -------
        list[str]
            Zero or more warning strings describing each overlap.
            An empty list means no conflicts were detected.
        """
        warnings: list[str] = []
        slots = sorted(plan.scheduled_tasks, key=lambda s: s.start_time)
        for i in range(len(slots) - 1):
            a, b = slots[i], slots[i + 1]
            if a.end_time > b.start_time:               # overlap detected
                overlap_min = int((a.end_time - b.start_time).total_seconds() / 60)
                warnings.append(
                    f"CONFLICT: '{a.task.title}' ({a.start_str}–{a.end_str}) "
                    f"overlaps '{b.task.title}' ({b.start_str}–{b.end_str}) "
                    f"by {overlap_min} min"
                )
        return warnings

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

        # Run conflict scan after all slots are committed.
        # Stores warnings on the plan — never raises, never blocks scheduling.
        plan.conflict_warnings = self.detect_conflicts(plan)
        return plan