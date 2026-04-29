# PawPal+

🎥 **Video Walkthrough:** [Watch on Loom](https://www.loom.com/share/ccfe8916395246bcbcaa03ca07094f42)

---

PawPal+ is a pet care scheduling app that I built in Module 2 and extended for the final project by adding a Gemini AI layer. The idea is simple: you tell it what tasks your pet needs done today, how much time you have, and it builds a schedule. The new part is that you can also just describe your day in plain English — "it's really hot outside" or "I only have 20 minutes" — and the AI will adjust the schedule for you.

---

## Original Project — Module 2: PawPal

The base project was **Module 2 — PawPal**, a pure Python scheduling app with no AI at all. I built a system where a pet owner could define care tasks (walks, feedings, medications), set a daily time budget, and get back a prioritized schedule. The scheduler sorted tasks by urgency (CRITICAL → HIGH → MEDIUM → LOW), tried to fit each one into its preferred time window (MORNING, AFTERNOON, EVENING), and explained every decision it made — why a task was placed where it was, and why something got skipped. It also handled recurring tasks (daily/weekly) and detected scheduling conflicts. The whole thing ran in a Streamlit UI with a full test suite.

What it couldn't do: react to anything. If it was 100 degrees outside, the schedule didn't care. That's what this extension fixes.

---

## What PawPal+ Does and Why It Matters

The problem with most pet care apps is they're just glorified to-do lists. They don't know that your dog probably shouldn't go on a 30-minute walk when it's 95 degrees, or that if you only have 15 minutes today the evening walk should probably be the first thing cut.

PawPal+ tries to fix that by combining a rule-based scheduler (which handles the hard constraints like time budget and priority) with an AI layer (which handles the fuzzy real-world stuff like weather, illness, and schedule pressure). You type what's going on, and it gives you specific suggestions — shorten this task, add this one, remove that one — that you can apply in one click.

---

## Architecture Overview

The system has four main pieces:

1. **`app.py` (Streamlit UI)** — This is what the owner actually sees and interacts with. It holds session state (the owner, the pet, the task list) and has two main workflows: the original scheduling flow and the new AI suggestions flow.

2. **`ai_agent.py` (AI layer)** — This takes the owner's free-text context and the current task list, builds a prompt, sends it to Gemini, and parses the response back into a structured list of actions. It returns JSON — either `{"suggestions": [...]}` or `{"error": "..."}` — so the UI always knows what it's getting.

3. **`pawpal_system.py` (backend logic)** — All the original classes live here: `Task`, `Pet`, `Owner`, `Scheduler`, `DailyPlan`. The AI suggestions are applied directly to these objects — modify a task's duration, add a new task to the pet, remove one — and then the scheduler rebuilds the plan from scratch.

4. **`eval_agent.py` (reliability harness)** — A separate script that tests the AI against two adversarial scenarios (extreme time crunch, extreme heat) and prints PASS/FAIL based on whether the AI respected the constraints.

The full data flow diagram is in `Mermaid.js` — paste it into [mermaid.live](https://mermaid.live) to see it rendered.

---

## Project Structure

```
pawpal_system.py   — backend classes (Task, Pet, Owner, Scheduler, DailyPlan)
app.py             — Streamlit UI
ai_agent.py        — Gemini AI agent
eval_agent.py      — reliability harness
main.py            — CLI demo (no UI needed)
tests/
  test_pawpal.py   — 47 unit tests
Mermaid.js         — architecture diagram (paste into mermaid.live)
reflection.md      — design and AI collaboration reflection
```

---

## Setup Instructions

**Step 1 — Clone the repo and set up a virtual environment:**
```bash
git clone <repo-url>
cd pawpal-starter
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

**Step 2 — Install dependencies:**
```bash
pip install -r requirements.txt
```

**Step 3 — Add your Gemini API key:**

Create a file called `.env` in the root of the project:
```
GEMINI_API_KEY=your_key_here
```
You can get a free key at [aistudio.google.com](https://aistudio.google.com). Note: the free tier has a daily request limit, so if you see a 429 error just wait until the next day.

**Step 4 — Run the app:**
```bash
streamlit run app.py
```

**Step 5 — (Optional) Run the CLI demo to see the scheduler work without the UI:**
```bash
python3 main.py
```

**Step 6 — (Optional) Run the AI reliability harness:**
```bash
python3 eval_agent.py
```

**Step 7 — Run the tests:**
```bash
python -m pytest tests/test_pawpal.py -v
```

---

## Sample Interactions

### Example 1 — Hot weather

**What I typed:** *"It's 95 degrees outside and Mochi seems really tired today."*

**Tasks before:** Morning walk (30 min, HIGH, MORNING), Evening walk (30 min, MEDIUM, EVENING), Feeding (10 min, CRITICAL, ANYTIME)

**What the AI returned:**
```json
[
  {
    "action": "modify",
    "target_title": "Morning walk",
    "task_data": { "duration_minutes": 10, "preferred_time": "EVENING" },
    "reason": "Extreme heat and lethargy — shorten the walk and move it to cooler evening hours."
  },
  {
    "action": "add",
    "task_data": {
      "title": "Check water bowl",
      "duration_minutes": 5,
      "priority": "HIGH",
      "preferred_time": "MORNING"
    },
    "reason": "Lethargy in hot weather can mean dehydration — make sure fresh water is available."
  }
]
```
**Result:** Morning walk shortened to 10 min and moved to EVENING. A new "Check water bowl" task added for MORNING.

---

### Example 2 — Short on time

**What I typed:** *"I only have about 20 minutes today, really busy with work."*

**What the AI returned:**
```json
[
  {
    "action": "remove",
    "target_title": "Evening walk",
    "reason": "Removing the lower-priority walk to stay within your 20-minute budget."
  },
  {
    "action": "modify",
    "target_title": "Morning walk",
    "task_data": { "duration_minutes": 10 },
    "reason": "Shortened to fit alongside feeding within your available time."
  }
]
```
**Result:** Evening walk removed, morning walk cut to 10 min — total now fits within 20 minutes.

---

### Example 3 — Sick pet

**What I typed:** *"Mochi threw up this morning and seems really off."*

**What the AI returned:**
```json
[
  {
    "action": "modify",
    "target_title": "Morning walk",
    "task_data": { "duration_minutes": 5, "priority": "LOW" },
    "reason": "Sick pets need rest — keep activity minimal until she feels better."
  },
  {
    "action": "add",
    "task_data": {
      "title": "Monitor symptoms",
      "duration_minutes": 10,
      "priority": "CRITICAL",
      "preferred_time": "MORNING"
    },
    "reason": "Track how often she's vomiting and call the vet if it continues."
  }
]
```
**Result:** Walk shortened and deprioritized. A CRITICAL "Monitor symptoms" task added for the morning.

---

## Design Decisions

**Why a greedy scheduler instead of something smarter?**
The scheduler works by going through tasks one at a time, highest priority first, and placing each one without going back to reconsider earlier decisions. This means it can make suboptimal choices — like filling the morning window with medium-priority tasks and then not having room for a high-priority one that shows up later. But every decision it makes comes with a plain-English explanation, which I think matters more for a care app than squeezing in one extra task. Simple and explainable beat clever and opaque.

**Why does the AI return JSON instead of just text?**
I tried having the AI return a text description of what to change, but then you still have to parse it and figure out what "shorten the walk" actually means in code. By constraining the response to a typed JSON schema (`action`, `target_title`, `task_data`, `reason`), the output can be applied directly to the task objects without any interpretation. It also makes failures obvious — if the JSON is malformed, you get a clean error message instead of silently doing the wrong thing.

**Why no conversation history?**
Every call to `analyze_care_context` is completely independent — it sends the current task list and context with no memory of what was suggested before. This keeps things simple and predictable. The owner can apply suggestions, then analyze again and get fresh advice on the updated state. The downside is that the AI can't say things like "well, I already suggested shortening that walk." That would be a good next feature.

---

## Reliability and Evaluation

**Summary:** 47 out of 47 unit tests pass. The AI reliability harness ran 2 adversarial test cases — both passed when the API was available. The AI correctly handled constraint violations (time crunch) and safety concerns (extreme heat) in every manual test. Error handling catches malformed JSON and missing API keys gracefully without crashing. The main reliability weakness is the eval harness uses keyword matching to score AI reasons, which occasionally flags a correct suggestion as a FAIL if the wording doesn't contain expected terms like "heat" or "temperature."

The system includes four reliability mechanisms:
- **Automated unit tests** — 47 tests covering all core logic and the full AI pipeline (mocked), run with `python -m pytest`
- **AI reliability harness** — `eval_agent.py` feeds adversarial inputs to the AI and scores the output for safety and budget compliance
- **Error handling** — `analyze_care_context` catches malformed JSON and API failures and returns a clean `{"error": "..."}` dict instead of crashing the UI
- **Structured output constraint** — the prompt forces the AI to return a typed JSON schema, making unexpected or unsafe outputs easy to detect and reject

---

## Testing Summary

**What worked well:**
- All 47 tests pass. The core scheduler logic (sorting, recurrence, conflict detection, filtering) is well-covered and I'm confident in it.
- Mocking the Gemini API with `unittest.mock` was really useful — it meant I could test all the AI parsing and apply logic without needing a live key or internet connection. Every CI run just works.
- The eval harness caught a real issue: the AI sometimes gives correct suggestions but phrases the reason in a way that doesn't include keywords like "heat" or "temperature," which caused false FAILs. That made me realize keyword-matching is a fragile evaluation strategy.

**What didn't:**
- The Gemini free tier rate limits were painful during development. I kept hitting daily quotas and had to switch between models (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`) to find one with remaining quota. It made iterating on the prompt slow.
- The eval harness only has 2 test cases, which isn't enough to feel confident about reliability across the full range of possible inputs.

**What I learned:**
- Mock external APIs as early as possible. I wrote the live tests first and wasted a lot of time on rate limit errors before switching to mocks.
- Structured prompting (asking for a specific JSON schema) is the right approach when you need AI output to be machine-readable. Free-form text responses are fine for humans but hard to act on in code.

---

## Reflection

The biggest thing this project taught me is that AI is most useful at the boundary between structured rules and messy human input. The scheduling logic — sort by priority, fit into time windows, check the budget — is straightforward code. What's hard is handling "it's hot" or "I'm exhausted today." That's where language models genuinely help, and trying to do it with if/else logic would be both brittle and way more work.

The experience that stuck with me most was the AI-generated placeholder code. It looked right — there was a spinner, a success message, a button — but the button was permanently disabled and the message was hardcoded. It passed a quick glance. The lesson is that you have to actually read AI-generated code, not just run it and assume it works because it didn't throw an error.

If I had more time I'd add persistent storage (so the schedule survives a page refresh), expand the eval harness to at least 10 test cases with numeric outcome checks instead of keyword matching, and add conversation history so the AI can remember what it already suggested in a session.
