# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

Phase 4 extended the core scheduler with four algorithmic improvements.
All logic lives in `pawpal_system.py` and is verified by 40 automated tests.

### Sort by time — `sort_tasks_by_time()` and `DailyPlan.sort_by_time()`

Tasks entered in any order can be sorted chronologically before display.

* **`sort_tasks_by_time(tasks)`** — module-level function that sorts raw
  `Task` objects by their preferred window's opening hour (MORNING → AFTERNOON
  → EVENING), with priority as a tiebreaker within the same window.
  Returns a new list; the original is never mutated.
* **`DailyPlan.sort_by_time()`** — sorts already-scheduled `ScheduledTask`
  entries by their concrete `start_time` (a `datetime`), guaranteeing correct
  display order even when slots are injected manually.

### Filter by pet and status — `Owner.filter_tasks()`

```python
owner.filter_tasks(pet_name="Luna", status="pending")
```

| Parameter | Values | Effect |
|---|---|---|
| `pet_name` | any pet name / `None` | Restrict to one pet or include all |
| `status` | `"all"` · `"pending"` · `"done"` | Filter by completion state |

Recurring tasks are evaluated with `Task.is_due()` so an instance that was
completed today (and whose `next_due` is tomorrow) correctly appears as
`"done"` even though its `completed` flag is `False`.

### Recurring tasks — `Task.generate_next_occurrence()` and `Pet.complete_task()`

Tasks can repeat on a `"daily"` or `"weekly"` cadence.

```python
Task(title="Feeding", category="feeding", duration_minutes=10,
     recurrence="daily", next_due="2026-03-30")
```

When `pet.complete_task("Feeding")` is called:

1. The current instance is **retired** (`completed = True`).
2. `generate_next_occurrence()` constructs a **brand-new `Task`** with
   `next_due` advanced by `timedelta(days=1)` (daily) or `timedelta(days=7)`
   (weekly) — Python's `dataclasses.replace()` copies all other fields
   automatically, so adding new fields to `Task` never breaks recurrence.
3. The new instance is **appended** to the pet's task list and surfaces
   automatically in the next day's `build_plan()` call.

### Conflict detection — `Scheduler.detect_conflicts()`

```python
warnings = Scheduler.detect_conflicts(plan)
# e.g. ["CONFLICT: 'Walk' (08:00–08:30) overlaps 'Feed' (08:15–08:45) by 15 min"]
```

After every `build_plan()` call, the scheduler scans all scheduled slots for
time overlaps and stores any warnings in `plan.conflict_warnings`.  The check
is **non-raising and non-blocking** — the plan is always returned, and an empty
list means the schedule is clean.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
