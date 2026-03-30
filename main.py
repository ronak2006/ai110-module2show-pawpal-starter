"""
main.py — PawPal+ Demo Script
Run: python3 main.py

Demonstrates:
  1. sort_tasks_by_time()       — chronological ordering of raw Task objects
  2. Owner.filter_tasks()       — filtering by pet name and completion status
  3. Recurring tasks            — daily / weekly tasks auto-advance with timedelta
"""

from datetime import datetime, timedelta

from pawpal_system import (
    Owner, Pet, Task, Scheduler,
    Priority, TimeWindow,
    DailyPlan, ScheduledTask,
    sort_tasks_by_time,
)


# ---------------------------------------------------------------------------
# 1. Create owner
# ---------------------------------------------------------------------------
jordan = Owner(
    name="Jordan",
    available_hours=3.0,
    day_start_hour=8,
    day_end_hour=21,
)

# ---------------------------------------------------------------------------
# 2. Create pets
# ---------------------------------------------------------------------------
mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3)
luna  = Pet(name="Luna",  species="cat", breed="Tabby",     age=5)

# ---------------------------------------------------------------------------
# 3. Add tasks to Mochi (intentionally OUT OF TIME ORDER to test sorting)
# ---------------------------------------------------------------------------
mochi.add_task(Task(                        # evening — added first
    title="Evening play session",
    category="enrichment",
    duration_minutes=25,
    priority=Priority.LOW,
    preferred_time=TimeWindow.EVENING,
))
mochi.add_task(Task(                        # afternoon — added second
    title="Afternoon walk",
    category="walk",
    duration_minutes=20,
    priority=Priority.MEDIUM,
    preferred_time=TimeWindow.AFTERNOON,
))
mochi.add_task(Task(                        # morning — added last
    title="Morning walk",
    category="walk",
    duration_minutes=30,
    priority=Priority.HIGH,
    preferred_time=TimeWindow.MORNING,
))

# ── Recurring tasks ──────────────────────────────────────────────────────────
mochi.add_task(Task(
    title="Breakfast feeding",
    category="feeding",
    duration_minutes=10,
    priority=Priority.CRITICAL,
    preferred_time=TimeWindow.MORNING,
    recurrence="daily",                     # repeats every day
    next_due="2026-03-30",
))
mochi.add_task(Task(
    title="Heartworm medication",
    category="medication",
    duration_minutes=5,
    priority=Priority.CRITICAL,
    preferred_time=TimeWindow.MORNING,
    notes="Give with food",
    recurrence="weekly",                    # repeats every 7 days
    next_due="2026-03-30",
))

# ---------------------------------------------------------------------------
# 4. Add tasks to Luna
# ---------------------------------------------------------------------------
luna_breakfast = Task(
    title="Breakfast feeding",
    category="feeding",
    duration_minutes=10,
    priority=Priority.CRITICAL,
    preferred_time=TimeWindow.MORNING,
    recurrence="daily",
    next_due="2026-03-30",
)
luna_breakfast.mark_complete()              # already done — used for filter demo

luna.add_task(luna_breakfast)
luna.add_task(Task(
    title="Litter box clean",
    category="grooming",
    duration_minutes=10,
    priority=Priority.HIGH,
    preferred_time=TimeWindow.ANYTIME,
))
luna.add_task(Task(
    title="Brushing",
    category="grooming",
    duration_minutes=15,
    priority=Priority.LOW,
    preferred_time=TimeWindow.EVENING,
))

# ---------------------------------------------------------------------------
# 5. Register pets with owner
# ---------------------------------------------------------------------------
jordan.add_pet(mochi)
jordan.add_pet(luna)


# ===========================================================================
# DEMO A — sort_tasks_by_time()
# ===========================================================================
print("\n" + "=" * 55)
print("  DEMO A — sort_tasks_by_time()")
print("=" * 55)

print("\nMochi's tasks AS ADDED (out of time order):")
for t in mochi.tasks:
    print(f"  [{t.preferred_time.value:9s}]  {t.title}")

print("\nMochi's tasks AFTER sort_tasks_by_time():")
for t in sort_tasks_by_time(mochi.tasks):
    print(f"  [{t.preferred_time.value:9s}]  {t.priority.name:8s}  {t.title}")


# ===========================================================================
# DEMO B — filter_tasks()
# ===========================================================================
print("\n" + "=" * 55)
print("  DEMO B — filter_tasks()")
print("=" * 55)

print("\nOnly Luna's tasks  (pet_name='Luna'):")
for t in jordan.filter_tasks(pet_name="Luna"):
    status = "done" if t.completed else "pending"
    print(f"  [{status:7s}]  {t.title}")

print("\nAll pending tasks across both pets  (status='pending'):")
for t in jordan.filter_tasks(status="pending"):
    recur = f"  [{t.recurrence}]" if t.recurrence else ""
    print(f"  {t.title}{recur}")

print("\nCompleted tasks across both pets  (status='done'):")
done = jordan.filter_tasks(status="done")
for t in done:
    print(f"  {t.title}  (next_due advanced to {t.next_due})")
if not done:
    print("  (none)")


# ===========================================================================
# DEMO C — Recurring tasks: complete_task() retires old instance and
#           automatically appends a brand-new one via generate_next_occurrence()
# ===========================================================================
print("\n" + "=" * 55)
print("  DEMO C — Recurring tasks (new-instance model)")
print("=" * 55)

print(f"\nMochi's task count BEFORE completing recurring tasks: {len(mochi.tasks)}")

# complete_task() calls mark_complete() → generate_next_occurrence() → appends new Task
mochi.complete_task("Breakfast feeding")   # daily  → new instance for 2026-03-31
mochi.complete_task("Heartworm medication") # weekly → new instance for 2026-04-06

print(f"Mochi's task count AFTER  completing recurring tasks: {len(mochi.tasks)}")
print("  (count increased: old instances retired, new instances appended)\n")

# Show all Mochi tasks — old ones completed=True, new ones completed=False
for t in mochi.tasks:
    flag = "[DONE — retired]" if t.completed else "[ACTIVE]        "
    due  = f"  next_due={t.next_due}" if t.next_due else ""
    recr = f"  recurs={t.recurrence}" if t.recurrence else ""
    print(f"  {flag}  {t.title}{recr}{due}")

print(f"\nIs the OLD breakfast instance still due today?")
old_breakfast = next(t for t in mochi.tasks
                     if t.title == "Breakfast feeding" and t.completed)
print(f"  is_due() → {old_breakfast.is_due()}  (completed=True — permanently retired)")

print(f"\nIs the NEW breakfast instance due today?")
new_breakfast = next(t for t in mochi.tasks
                     if t.title == "Breakfast feeding" and not t.completed)
print(f"  is_due() → {new_breakfast.is_due()}  "
      f"(next_due={new_breakfast.next_due} — appears tomorrow)")

print(f"\nPending tasks remaining for today (both pets):")
for t in jordan.filter_tasks(status="pending"):
    print(f"  {t.title}")


# ===========================================================================
# DEMO D — Build the daily plan (DailyPlan.sort_by_time() for display order)
# ===========================================================================
print("\n" + "=" * 55)
print("  DEMO D — Daily Plan")
print("=" * 55)

scheduler = Scheduler(owner=jordan)
plan = scheduler.build_plan(date="2026-03-30")
plan.sort_by_time()                         # guarantee chronological display

print(f"\nOwner  : {jordan}")
print(f"Pets   : {', '.join(str(p) for p in jordan.pets)}")
print()
print(plan.summary())

# ===========================================================================
# DEMO E — Conflict detection
#   The standard scheduler never double-books (linear cursor + buffer).
#   To prove detect_conflicts() fires, we manually build a plan where two
#   tasks share an overlapping window, then call detect_conflicts() directly.
# ===========================================================================
print("\n" + "=" * 55)
print("  DEMO E — detect_conflicts() conflict detection")
print("=" * 55)

# Craft two tasks whose time slots intentionally overlap
base_dt   = datetime(2026, 3, 30, 8, 0)   # 08:00 AM

walk_task = Task("Morning walk",    "walk",     30, Priority.HIGH,   TimeWindow.MORNING)
feed_task = Task("Breakfast feeding","feeding", 20, Priority.CRITICAL, TimeWindow.MORNING)

# Slot A: 08:00 – 08:30   Slot B: 08:15 – 08:35  → 15-minute overlap
slot_a = ScheduledTask(
    task=walk_task,
    start_time=base_dt,
    end_time=base_dt + timedelta(minutes=30),
    reason="manually placed",
)
slot_b = ScheduledTask(
    task=feed_task,
    start_time=base_dt + timedelta(minutes=15),   # starts while walk is still running
    end_time=base_dt + timedelta(minutes=35),
    reason="manually placed",
)

conflict_plan = DailyPlan(date="2026-03-30", scheduled_tasks=[slot_a, slot_b])
conflict_plan.conflict_warnings = Scheduler.detect_conflicts(conflict_plan)

print(f"\nSlot A: {slot_a.start_str} – {slot_a.end_str}  →  {walk_task.title}")
print(f"Slot B: {slot_b.start_str} – {slot_b.end_str}  →  {feed_task.title}")

if conflict_plan.conflict_warnings:
    print("\nWarnings returned (no crash — just messages):")
    for w in conflict_plan.conflict_warnings:
        print(f"  ⚠  {w}")
else:
    print("\n  No conflicts detected.")
