## DEMO SECTION
<a href="/course_images/screenshot.png" target="_blank">




# PawPal+

A smart pet care management app built with Python and Streamlit. PawPal+ helps busy pet owners stay consistent by generating a prioritized, time-aware daily care schedule — and explaining every decision it makes.

---

## Features

### Priority-first scheduling
Tasks are ranked by urgency (CRITICAL → HIGH → MEDIUM → LOW). The scheduler always places the most important tasks first, ensuring critical care — medications, feedings — is never bumped by lower-priority activities.

### Time-window placement
Each task can declare a preferred time of day: MORNING, AFTERNOON, EVENING, or ANYTIME. The scheduler attempts to honor that preference and explains when it can't, falling back gracefully to the next open slot rather than skipping the task.

### Daily time budget
The owner sets a total number of care hours available for the day. The scheduler tracks cumulative minutes and skips any task that would exceed the budget, reporting exactly how many minutes were available vs. used.

### Sorting by time — `sort_tasks_by_time()`
Tasks entered in any order can be sorted chronologically by their preferred window (MORNING first, then AFTERNOON, EVENING, ANYTIME), with priority as a tiebreaker within the same window. The original list is never mutated.

### Filtering by pet and status — `Owner.filter_tasks()`
Tasks across all pets can be filtered by pet name and/or completion status (`"pending"` / `"done"` / `"all"`). Recurring tasks are evaluated with `Task.is_due()` so a task completed today correctly shows as done even before its `completed` flag is set on the next instance.

### Recurring tasks — `"daily"` and `"weekly"` cadence
Tasks can repeat automatically. When a recurring task is marked complete, the old instance is retired and a brand-new instance is appended with `next_due` advanced by 1 day (daily) or 7 days (weekly) via Python's `timedelta`. Future schedules pick it up automatically — no manual re-adding required.

### Conflict detection — `Scheduler.detect_conflicts()`
After every scheduling run, the scheduler scans all placed tasks for overlapping time slots and stores human-readable warnings on the plan. Warnings appear prominently in the UI before the schedule so the owner can act on them. The check is non-raising and non-blocking — a clean schedule returns an empty list.

### Explainable plans
Every scheduled task includes a plain-English reason (e.g. *"Fits in preferred morning window (CRITICAL priority)"* or *"Preferred afternoon window unavailable — moved to next open slot"*). Skipped tasks include a reason too, so the owner always knows why something was left out.

---

## Project structure

```
pawpal_system.py   — all backend classes and scheduling logic
app.py             — Streamlit UI, wired to the backend
main.py            — CLI demo script (run to verify logic without the UI)
tests/
  test_pawpal.py   — automated tests (run with python -m pytest)
Mermaid.js         — UML class diagram (paste into mermaid.live to render)
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the app

```bash
streamlit run app.py
```

## Run the CLI demo

```bash
python3 main.py
```

## Run tests

```bash
python -m pytest
```

---

## Testing PawPal+

### Run the test suite

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

The suite contains **48 tests** across `tests/test_pawpal.py`:

| Area | What is verified |
|---|---|
| **Sorting correctness** | Tasks sort MORNING → AFTERNOON → EVENING → ANYTIME; higher priority breaks ties within the same window; the original list is never mutated. |
| **Recurrence logic** | Completing a `daily` task retires the old instance and queues a new one dated tomorrow; `weekly` tasks advance 7 days; chaining two completions works correctly; one-time tasks return `None`. |
| **Conflict detection** | Overlapping slots are flagged with the correct overlap duration; back-to-back tasks are not flagged; out-of-order input is handled; empty plans return zero warnings. |
| **`is_due()` logic** | Tasks with no `next_due` are always due; future-dated tasks are not due; completed tasks are never due. |
| **Edge cases** | Pet with zero tasks produces an empty plan; a task longer than the daily budget lands in `skipped_tasks`; `filter_tasks()` correctly combines pet-name and status filters. |

### Confidence level

**★★★★★ (5 / 5)**

All 48 tests pass. Every public method is covered through both happy paths and boundary conditions — giving high confidence the system behaves correctly under realistic usage.
