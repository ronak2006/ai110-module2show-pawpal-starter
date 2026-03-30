"""
main.py — PawPal+ Demo Script
Run: python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler, Priority, TimeWindow


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
# 3. Add tasks to Mochi (dog)
# ---------------------------------------------------------------------------
mochi.add_task(Task(
    title="Morning walk",
    category="walk",
    duration_minutes=30,
    priority=Priority.HIGH,
    preferred_time=TimeWindow.MORNING,
))
mochi.add_task(Task(
    title="Breakfast feeding",
    category="feeding",
    duration_minutes=10,
    priority=Priority.CRITICAL,
    preferred_time=TimeWindow.MORNING,
))
mochi.add_task(Task(
    title="Heartworm medication",
    category="medication",
    duration_minutes=5,
    priority=Priority.CRITICAL,
    preferred_time=TimeWindow.MORNING,
    notes="Give with food",
))
mochi.add_task(Task(
    title="Afternoon walk",
    category="walk",
    duration_minutes=20,
    priority=Priority.MEDIUM,
    preferred_time=TimeWindow.AFTERNOON,
))
mochi.add_task(Task(
    title="Evening play session",
    category="enrichment",
    duration_minutes=25,
    priority=Priority.LOW,
    preferred_time=TimeWindow.EVENING,
))

# ---------------------------------------------------------------------------
# 4. Add tasks to Luna (cat)
# ---------------------------------------------------------------------------
luna.add_task(Task(
    title="Breakfast feeding",
    category="feeding",
    duration_minutes=10,
    priority=Priority.CRITICAL,
    preferred_time=TimeWindow.MORNING,
))
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

# ---------------------------------------------------------------------------
# 6. Build the daily plan
# ---------------------------------------------------------------------------
scheduler = Scheduler(owner=jordan)
plan = scheduler.build_plan(date="2026-03-30")

# ---------------------------------------------------------------------------
# 7. Print Today's Schedule
# ---------------------------------------------------------------------------
print(f"\nOwner  : {jordan}")
print(f"Pets   : {', '.join(str(p) for p in jordan.pets)}")
print()
print(plan.summary())
