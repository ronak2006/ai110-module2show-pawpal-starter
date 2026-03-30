"""
tests/test_pawpal.py — Unit tests for PawPal+ core logic.
Run with: python -m pytest
"""

from datetime import datetime, timedelta

import pytest

from pawpal_system import (
    DailyPlan, Owner, Pet, Scheduler, ScheduledTask, Task,
    Priority, TimeWindow,
    sort_tasks_by_time,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _task(title="Walk", category="walk", duration=20,
          priority=Priority.MEDIUM, window=TimeWindow.ANYTIME,
          recurrence=None, next_due=None) -> Task:
    return Task(
        title=title, category=category, duration_minutes=duration,
        priority=priority, preferred_time=window,
        recurrence=recurrence, next_due=next_due,
    )


def _scheduled(task, start_h, start_m, duration_min) -> ScheduledTask:
    """Build a ScheduledTask starting at (start_h:start_m) for duration_min."""
    base = datetime(2026, 3, 30, start_h, start_m)
    return ScheduledTask(task=task, start_time=base,
                         end_time=base + timedelta(minutes=duration_min))


# ===========================================================================
# Original tests (kept unchanged)
# ===========================================================================

def test_mark_complete_changes_status():
    """Calling mark_complete() on a one-time task should flip completed to True."""
    task = Task(title="Morning walk", category="walk", duration_minutes=30)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list by one."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Feeding", category="feeding", duration_minutes=10))
    assert len(pet.tasks) == 1


# ===========================================================================
# Recurring tasks — mark_complete() / generate_next_occurrence()
# ===========================================================================

def test_daily_task_mark_complete_returns_new_instance():
    """mark_complete() on a daily task must return a NEW Task object, not None."""
    task = _task(recurrence="daily", next_due="2026-03-30")
    next_task = task.mark_complete()

    assert next_task is not None, "Expected a next occurrence for a daily task"
    assert next_task is not task, "Next occurrence must be a different object"


def test_daily_task_next_due_advances_one_day():
    """Daily recurrence: next_due on the returned instance = original + 1 day."""
    task = _task(recurrence="daily", next_due="2026-03-30")
    next_task = task.mark_complete()

    assert next_task.next_due == "2026-03-31"


def test_weekly_task_next_due_advances_seven_days():
    """Weekly recurrence: next_due on the returned instance = original + 7 days."""
    task = _task(recurrence="weekly", next_due="2026-03-30")
    next_task = task.mark_complete()

    assert next_task.next_due == "2026-04-06"


def test_one_time_task_mark_complete_returns_none():
    """mark_complete() on a one-time task (recurrence=None) must return None."""
    task = _task(recurrence=None)
    result = task.mark_complete()

    assert result is None


def test_recurring_task_completed_flag_set_on_old_instance():
    """The original instance must be retired (completed=True) after mark_complete()."""
    task = _task(recurrence="daily", next_due="2026-03-30")
    task.mark_complete()

    assert task.completed is True, "Old instance should be permanently retired"


def test_new_occurrence_starts_incomplete():
    """The generated next occurrence must have completed=False."""
    task = _task(recurrence="daily", next_due="2026-03-30")
    next_task = task.mark_complete()

    assert next_task.completed is False


def test_new_occurrence_inherits_task_metadata():
    """Title, category, duration, priority and window are copied to the new instance."""
    task = _task(title="Medication", category="medication", duration=5,
                 priority=Priority.CRITICAL, window=TimeWindow.MORNING,
                 recurrence="daily", next_due="2026-03-30")
    next_task = task.mark_complete()

    assert next_task.title == "Medication"
    assert next_task.category == "medication"
    assert next_task.duration_minutes == 5
    assert next_task.priority == Priority.CRITICAL
    assert next_task.preferred_time == TimeWindow.MORNING
    assert next_task.recurrence == "daily"


def test_generate_next_occurrence_without_next_due_uses_today():
    """When next_due is None, generate_next_occurrence() falls back to today."""
    task = _task(recurrence="daily", next_due=None)
    next_task = task.generate_next_occurrence()

    expected = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    assert next_task.next_due == expected


# ===========================================================================
# is_due()
# ===========================================================================

def test_is_due_false_when_completed():
    """A permanently completed task is never due."""
    task = _task()
    task.completed = True
    assert task.is_due() is False


def test_is_due_true_when_next_due_is_today():
    """A recurring task whose next_due == today should be due."""
    today = datetime.today().strftime("%Y-%m-%d")
    task = _task(recurrence="daily", next_due=today)
    assert task.is_due() is True


def test_is_due_true_when_next_due_is_in_the_past():
    """A recurring task overdue from yesterday should still be due."""
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    task = _task(recurrence="daily", next_due=yesterday)
    assert task.is_due() is True


def test_is_due_false_when_next_due_is_in_the_future():
    """A recurring task whose next_due is tomorrow is NOT due today."""
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    task = _task(recurrence="daily", next_due=tomorrow)
    assert task.is_due() is False


def test_is_due_true_when_no_next_due_and_not_completed():
    """A plain pending task with no next_due date is always due."""
    task = _task(recurrence=None, next_due=None)
    assert task.is_due() is True


# ===========================================================================
# Pet.complete_task()
# ===========================================================================

def test_complete_task_recurring_increases_task_count():
    """Completing a recurring task retires the old one and appends a new one."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(_task(title="Feeding", recurrence="daily", next_due="2026-03-30"))

    assert len(pet.tasks) == 1
    pet.complete_task("Feeding")
    assert len(pet.tasks) == 2, "Old instance retired + new instance appended = 2 total"


def test_complete_task_one_time_does_not_increase_count():
    """Completing a one-time task does NOT add a new instance."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(_task(title="Vet visit", recurrence=None))

    pet.complete_task("Vet visit")
    assert len(pet.tasks) == 1, "No new instance for one-time tasks"


def test_complete_task_returns_true_on_success():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(_task(title="Walk"))
    assert pet.complete_task("Walk") is True


def test_complete_task_returns_false_when_title_not_found():
    pet = Pet(name="Mochi", species="dog")
    assert pet.complete_task("NonExistent") is False


def test_complete_task_returns_false_when_already_done():
    """A task already marked complete cannot be completed again."""
    pet = Pet(name="Mochi", species="dog")
    t = _task(title="Walk")
    t.completed = True
    pet.add_task(t)
    assert pet.complete_task("Walk") is False


def test_complete_task_recurring_new_instance_is_pending():
    """The appended next occurrence must be pending (is_due when due date arrives)."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(_task(title="Feeding", recurrence="daily", next_due="2026-03-30"))
    pet.complete_task("Feeding")

    new_instance = next(t for t in pet.tasks if not t.completed)
    assert new_instance.next_due == "2026-03-31"
    assert new_instance.completed is False


# ===========================================================================
# sort_tasks_by_time()
# ===========================================================================

def test_sort_tasks_by_time_orders_windows_correctly():
    """Evening tasks added first must sort after Morning tasks."""
    tasks = [
        _task("Eve",  window=TimeWindow.EVENING),
        _task("Morn", window=TimeWindow.MORNING),
        _task("Aft",  window=TimeWindow.AFTERNOON),
    ]
    result = sort_tasks_by_time(tasks)
    windows = [t.preferred_time for t in result]
    assert windows == [TimeWindow.MORNING, TimeWindow.AFTERNOON, TimeWindow.EVENING]


def test_sort_tasks_by_time_priority_breaks_same_window_tie():
    """Within the same window, higher priority should come first."""
    tasks = [
        _task("Low",  window=TimeWindow.MORNING, priority=Priority.LOW),
        _task("High", window=TimeWindow.MORNING, priority=Priority.HIGH),
        _task("Crit", window=TimeWindow.MORNING, priority=Priority.CRITICAL),
    ]
    result = sort_tasks_by_time(tasks)
    assert result[0].title == "Crit"
    assert result[1].title == "High"
    assert result[2].title == "Low"


def test_sort_tasks_by_time_empty_list():
    """sort_tasks_by_time on an empty list must return an empty list."""
    assert sort_tasks_by_time([]) == []


def test_sort_tasks_by_time_does_not_mutate_original():
    """The original list must be unchanged (sort returns a new list)."""
    tasks = [
        _task("Eve",  window=TimeWindow.EVENING),
        _task("Morn", window=TimeWindow.MORNING),
    ]
    original_order = [t.title for t in tasks]
    sort_tasks_by_time(tasks)
    assert [t.title for t in tasks] == original_order


# ===========================================================================
# DailyPlan.sort_by_time()
# ===========================================================================

def test_daily_plan_sort_by_time_orders_scheduled_tasks():
    """sort_by_time() must reorder scheduled tasks chronologically in-place."""
    t1 = _task("Later")
    t2 = _task("Earlier")

    slot_later   = _scheduled(t1, start_h=10, start_m=0, duration_min=20)
    slot_earlier = _scheduled(t2, start_h=8,  start_m=0, duration_min=20)

    plan = DailyPlan(date="2026-03-30", scheduled_tasks=[slot_later, slot_earlier])
    plan.sort_by_time()

    assert plan.scheduled_tasks[0].task.title == "Earlier"
    assert plan.scheduled_tasks[1].task.title == "Later"


# ===========================================================================
# Owner.filter_tasks()
# ===========================================================================

def _owner_with_two_pets():
    owner = Owner(name="Jordan", available_hours=3.0)
    mochi = Pet(name="Mochi", species="dog")
    luna  = Pet(name="Luna",  species="cat")
    mochi.add_task(_task("Walk",    recurrence=None))
    mochi.add_task(_task("Feed",    recurrence=None))
    luna.add_task(_task("Brushing", recurrence=None))
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna


def test_filter_tasks_by_pet_name():
    owner, _, _ = _owner_with_two_pets()
    result = owner.filter_tasks(pet_name="Luna")
    assert all(t.title == "Brushing" for t in result)
    assert len(result) == 1


def test_filter_tasks_unknown_pet_returns_empty():
    owner, _, _ = _owner_with_two_pets()
    assert owner.filter_tasks(pet_name="Rex") == []


def test_filter_tasks_status_pending_excludes_completed():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.tasks[0].completed = True          # mark Walk as done

    pending = owner.filter_tasks(status="pending")
    titles = [t.title for t in pending]
    assert "Walk" not in titles
    assert "Feed" in titles


def test_filter_tasks_status_done_excludes_pending():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.tasks[0].completed = True

    done = owner.filter_tasks(status="done")
    titles = [t.title for t in done]
    assert "Walk" in titles
    assert "Feed" not in titles


def test_filter_tasks_all_returns_everything():
    owner, _, _ = _owner_with_two_pets()
    result = owner.filter_tasks(status="all")
    assert len(result) == 3


def test_filter_tasks_combined_pet_and_status():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.tasks[0].completed = True          # Walk is done

    result = owner.filter_tasks(pet_name="Mochi", status="pending")
    assert len(result) == 1
    assert result[0].title == "Feed"


def test_filter_tasks_recurring_completed_this_cycle_is_not_pending():
    """After complete_task(), the retired recurring instance must not appear as pending."""
    owner = Owner(name="Jordan", available_hours=2.0)
    mochi = Pet(name="Mochi", species="dog")
    mochi.add_task(_task("Feeding", recurrence="daily", next_due="2026-03-30"))
    owner.add_pet(mochi)

    mochi.complete_task("Feeding")   # retires today's instance, queues tomorrow's

    pending_titles = [t.title for t in owner.filter_tasks(status="pending")]
    # Tomorrow's new instance has next_due in the future → is_due()=False → not pending
    assert "Feeding" not in pending_titles


# ===========================================================================
# Scheduler.detect_conflicts()
# ===========================================================================

def test_detect_conflicts_no_conflicts_returns_empty():
    """Non-overlapping tasks must produce zero warnings."""
    t1 = _task("Walk")
    t2 = _task("Feed")
    plan = DailyPlan(
        date="2026-03-30",
        scheduled_tasks=[
            _scheduled(t1, 8,  0, 30),   # 08:00 – 08:30
            _scheduled(t2, 9,  0, 20),   # 09:00 – 09:20  (gap of 30 min)
        ],
    )
    assert Scheduler.detect_conflicts(plan) == []


def test_detect_conflicts_adjacent_tasks_no_overlap():
    """Back-to-back tasks (end == next start) are NOT a conflict."""
    t1 = _task("A")
    t2 = _task("B")
    plan = DailyPlan(
        date="2026-03-30",
        scheduled_tasks=[
            _scheduled(t1, 8, 0, 30),    # 08:00 – 08:30
            _scheduled(t2, 8, 30, 20),   # 08:30 – 08:50  (exactly adjacent)
        ],
    )
    assert Scheduler.detect_conflicts(plan) == []


def test_detect_conflicts_overlap_returns_warning():
    """Overlapping tasks must produce exactly one warning string."""
    t1 = _task("Walk")
    t2 = _task("Feed")
    plan = DailyPlan(
        date="2026-03-30",
        scheduled_tasks=[
            _scheduled(t1, 8,  0, 30),   # 08:00 – 08:30
            _scheduled(t2, 8, 15, 30),   # 08:15 – 08:45  (15-min overlap)
        ],
    )
    warnings = Scheduler.detect_conflicts(plan)
    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Feed" in warnings[0]
    assert "15 min" in warnings[0]


def test_detect_conflicts_overlap_by_one_minute():
    """Even a 1-minute overlap must be flagged."""
    t1 = _task("A")
    t2 = _task("B")
    plan = DailyPlan(
        date="2026-03-30",
        scheduled_tasks=[
            _scheduled(t1, 8, 0, 30),    # 08:00 – 08:30
            _scheduled(t2, 8, 29, 10),   # 08:29 – 08:39  (1-min overlap)
        ],
    )
    warnings = Scheduler.detect_conflicts(plan)
    assert len(warnings) == 1
    assert "1 min" in warnings[0]


def test_detect_conflicts_multiple_overlaps():
    """Three mutually-overlapping tasks should produce two warnings (A↔B and B↔C)."""
    t1, t2, t3 = _task("A"), _task("B"), _task("C")
    plan = DailyPlan(
        date="2026-03-30",
        scheduled_tasks=[
            _scheduled(t1, 8,  0, 60),   # 08:00 – 09:00
            _scheduled(t2, 8, 20, 60),   # 08:20 – 09:20  (overlaps A)
            _scheduled(t3, 8, 40, 60),   # 08:40 – 09:40  (overlaps B)
        ],
    )
    warnings = Scheduler.detect_conflicts(plan)
    assert len(warnings) == 2


def test_detect_conflicts_empty_plan_returns_empty():
    """An empty plan must never raise and must return an empty list."""
    plan = DailyPlan(date="2026-03-30")
    assert Scheduler.detect_conflicts(plan) == []


def test_build_plan_populates_conflict_warnings_field():
    """build_plan() must auto-run detect_conflicts() and store results on the plan."""
    owner = Owner(name="Jordan", available_hours=3.0)
    pet   = Pet(name="Mochi", species="dog")
    pet.add_task(_task("Walk", duration=20))
    owner.add_pet(pet)

    plan = Scheduler(owner).build_plan(date="2026-03-30")

    # conflict_warnings should be a list (empty here — no real conflicts)
    assert isinstance(plan.conflict_warnings, list)
    assert plan.conflict_warnings == []
