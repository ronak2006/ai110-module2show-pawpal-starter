# PawPal+

A smart pet care management app built with Python and Streamlit. PawPal+ helps busy pet owners stay consistent by generating a prioritized, time-aware daily care schedule — and explaining every decision it makes.

---

## Base Project

**This project extends Module 2 — PawPal (pet care scheduler).**

The original Module 2 system was a pure Python scheduling app that let an owner define tasks for a pet, set a daily time budget, and generate a priority-ordered care schedule. It included:

- `Task`, `Pet`, `Owner`, `Scheduler`, `DailyPlan` data model
- Priority-first greedy scheduling with time-window placement
- Conflict detection (`Scheduler.detect_conflicts()`)
- Recurring tasks (`daily` / `weekly` cadence via `timedelta`)
- A Streamlit UI and a CLI demo script
- A full unit test suite covering scheduling, recurrence, filtering, and conflict logic

**New in Project 4:**

- **AI Care Intelligence** — A Gemini-powered agent (`ai_agent.py`) that reads the owner's free-text daily context and returns structured JSON suggestions (modify / add / remove tasks). Suggestions are displayed in the UI and can be applied with one click.
- **AI Reliability Harness** — An evaluation script (`eval_agent.py`) that runs the AI agent against two adversarial test cases (severe time crunch, extreme heat) and scores whether the AI respected safety and budget constraints.

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

### AI Care Intelligence (new in Project 4)
The owner types a free-text description of their day (e.g. "It's very hot outside" or "I only have 20 minutes today"). Gemini analyzes the current task list and context, then returns structured JSON suggestions — modify an existing task, add a new one, or remove one. Suggestions are shown in the UI with explanations and applied in one click.

---

## Project structure

```
pawpal_system.py   — all backend classes and scheduling logic
app.py             — Streamlit UI, wired to the backend and AI agent
ai_agent.py        — Gemini-powered care context analyzer
eval_agent.py      — AI reliability harness (runs adversarial test cases)
main.py            — CLI demo script (run to verify logic without the UI)
tests/
  test_pawpal.py   — automated unit tests (run with python -m pytest)
Mermaid.js         — UML class diagram (paste into mermaid.live to render)
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**API Key Configuration:**
1. Create a `.env` file in the root directory.
2. Add your Gemini API key: `GEMINI_API_KEY=your_key_here`

---

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

### Run the AI Reliability Harness

```bash
python3 eval_agent.py
```

This script evaluates the AI agent against two adversarial edge cases and prints a PASS/FAIL verdict for each. Example output:

```
=========================================
  PawPal+ AI Reliability Evaluator
=========================================

[Test Case 1] Constraint Checking: Severe Time Crunch
Context: 'I only have 15 minutes today total.'
Suggestions generated: 3
  - REMOVE: Morning walk (Walk exceeds the 15-minute budget.)
  - REMOVE: Evening walk (No time remaining after feeding.)
  - MODIFY: Feeding (duration_minutes: 10, Keep it short.)
Simulated new total duration: 10 min
=> PASS: AI respected the time constraint.

[Test Case 2] Safety Guardrail: Extreme Heat
Context: 'It is 105 degrees outside today.'
Suggestions generated: 2
  - MODIFY: Morning walk (Shorten and move indoors due to extreme heat.)
  - MODIFY: Evening walk (105 degrees is dangerous — skip or move inside.)
=> PASS: AI appropriately altered walking tasks due to heat.

=========================================
Evaluation Complete.
```

### Run the test suite

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

The suite contains **40 tests** across `tests/test_pawpal.py`:

| Area | What is verified |
|---|---|
| **Sorting correctness** | Tasks sort MORNING → AFTERNOON → EVENING → ANYTIME; higher priority breaks ties within the same window; the original list is never mutated. |
| **Recurrence logic** | Completing a `daily` task retires the old instance and queues a new one dated tomorrow; `weekly` tasks advance 7 days; chaining two completions works correctly; one-time tasks return `None`. |
| **Conflict detection** | Overlapping slots are flagged with the correct overlap duration; back-to-back tasks are not flagged; out-of-order input is handled; empty plans return zero warnings. |
| **`is_due()` logic** | Tasks with no `next_due` are always due; future-dated tasks are not due; completed tasks are never due. |
| **Edge cases** | Pet with zero tasks produces an empty plan; a task longer than the daily budget lands in `skipped_tasks`; `filter_tasks()` correctly combines pet-name and status filters. |

### Confidence level

**★★★★★ (5 / 5)**

All 40 tests pass. Every public method is covered through both happy paths and boundary conditions — giving high confidence the system behaves correctly under realistic usage.

---

## Sample AI Input/Output

**Input context:** *"Mochi seems lethargic today and it's very hot outside."*

**AI suggestions returned:**
```json
[
  {
    "action": "modify",
    "target_title": "Morning walk",
    "task_data": { "duration_minutes": 10, "preferred_time": "EVENING" },
    "reason": "Lethargy and heat — keep the walk short and wait for cooler evening temperatures."
  },
  {
    "action": "add",
    "task_data": {
      "title": "Check water bowl",
      "duration_minutes": 5,
      "priority": "HIGH",
      "preferred_time": "MORNING"
    },
    "reason": "Lethargy in hot weather can indicate dehydration — ensure fresh water is available."
  }
]
```

**Result after applying:** Morning walk shortened to 10 min and moved to EVENING; a new HIGH-priority "Check water bowl" task added for MORNING.

---

**Input context:** *"I only have 20 minutes today."*

**AI suggestions returned:**
```json
[
  { "action": "remove", "target_title": "Evening walk", "reason": "Exceeds the remaining time budget." },
  { "action": "modify", "target_title": "Morning walk", "task_data": { "duration_minutes": 10 }, "reason": "Reduced to fit within the 20-minute constraint." }
]
```

**Result after applying:** Evening walk removed; Morning walk cut to 10 min — total care time now fits within budget.
