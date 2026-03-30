# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
=> The initial UML design uses six classes split across three layers. A data layer of pure dataclasses — Pet, Owner, and Task — stores who the plan is for and what needs to be done. A plan layer of ScheduledTask, SkippedTask, and DailyPlan  
  represents the output, wrapping tasks with concrete times and explanations. A Scheduler class ties everything together, holding an Owner, a Pet, and a task pool, and producing a DailyPlan via build_plan(). Two enums, Priority and         
  TimeWindow, drive the ordering logic.

- What classes did you include, and what responsibilities did you assign to each?
-> Pet and Owner hold profile data with no behavior — Owner also carries the day's time constraints. Task describes a single care activity including its duration, priority, and preferred time of day. ScheduledTask and SkippedTask are output
  wrappers that pair a task with either a concrete time slot or a reason it was skipped. DailyPlan collects those two lists and exposes a summary() method for display. Scheduler is the only class with real logic — it owns the task pool and
  runs the scheduling algorithm inside build_plan(), returning a DailyPlan.  
**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
=> We dropped Owner and Pet from DailyPlan after realizing Scheduler already owns them (redundancy)  

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

=> The scheduler looks at three things: how much time the owner has in the day, how urgent each task is, and when the pet prefers to have it done (morning, afternoon, or evening).

Time budget came first because it's a hard limit — if there's no time left, nothing else matters. Priority came second because some tasks like medication really can't wait, while a grooming session can. Time-of-day preference came last because it's a "nice to have" — the scheduler tries to respect it, but if the preferred window is already full, it finds the next open slot rather than skipping the task entirely.

Basically I ranked them by consequence: running out of time is a crisis, missing a CRITICAL task is a problem, getting the walk done at 2pm instead of 9am is just a mild inconvenience.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

=> One tradeoff the scheduler makes is that it places tasks one at a time, from top to bottom, and never goes back to reconsider earlier decisions. So if a high-priority task gets placed in the morning and takes up most of the available window, a shorter task that would have fit perfectly gets pushed out — even though swapping the order would have worked.

I kept this approach because it makes the schedule easy to explain. Every task has a clear "why" message, and the owner can follow the logic without needing a computer science degree. A smarter algorithm might squeeze in one extra task, but it would be much harder to trust or debug. For a pet care app where predictability matters more than perfection, simple and transparent beats clever and opaque.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

=> I used AI at basically every stage, but in different ways depending on what I was doing. Early on it was mostly brainstorming — I'd describe the problem and ask things like "what classes would make sense here" or "how should Owner talk to Scheduler." That was genuinely useful because it pushed me to think about boundaries between classes before writing a single line of code.

For implementation, the most useful prompts were specific ones. Vague prompts like "write a scheduler" gave back bloated code I didn't want. But asking something like "given this Task dataclass with a recurrence field, how should mark_complete() return the next occurrence using dataclasses.replace()" gave me something I could actually use. The more context I gave, the better the output.

I also used it for review — pasting in a method and asking "does this have any edge cases I'm missing" caught a few things, like the fact that is_due() needed to handle the case where next_due is None differently from when it's a future date.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

=> When I asked for help with the Scheduler, the first suggestion came back with Scheduler owning its own task list and an add_task() method — basically making it a second place where tasks lived alongside Pet. I pushed back on that because it created two sources of truth: you'd have to remember to add tasks to both the Pet and the Scheduler, and they could easily get out of sync.

I kept the design where tasks live only on Pet and Scheduler always fetches them fresh through owner.get_pending_tasks(). It meant deleting the add_task() method the AI suggested, but the result was cleaner and less error-prone. I verified it was the right call by tracing through what would happen if someone added a task mid-session — with the AI's version, the Scheduler's internal list would be stale. With my version, it always reflects current state.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

=> I focused testing on the parts of the code where bugs would be invisible until something broke in production. The two original tests — task completion changing status, and adding a task increasing the pet's task count — were basic sanity checks, but the more important ones came later when I added recurrence.

Recurring tasks were the trickiest part of the system because mark_complete() now has to do two things at once: retire the old instance and create a new one with the right date. So I wrote tests for each case separately — does the daily task advance by one day, does the weekly task advance by seven, does the old instance get marked completed, does the new instance start as incomplete, does it copy all the metadata correctly. Each of those could fail independently, so testing them separately made it much easier to pinpoint problems.

I also tested is_due() with future dates, past dates, and no date at all, because that method gates everything — if it returns the wrong value, tasks either never show up or never go away.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

=> Pretty confident on the happy path. The core scheduling loop — sort by priority, fit into time windows, respect the budget, explain every decision — works reliably and the tests back it up.

Where I'm less confident is around edge cases I haven't explicitly tested yet. The one I'd go after first is what happens when two CRITICAL tasks both want the same morning window and there's only time for one. Right now the second one falls back to the next open slot, which is probably fine, but I haven't written a test that asserts exactly what the output should look like in that scenario. I'd also want to test what happens when the owner sets available_hours to something tiny like 0.5 — does every task get skipped gracefully, or does something break? And I'd test recurring tasks that were created with no next_due date, just to make sure the "fall back to today" logic actually works end to end and not just in isolation.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

=> The recurring task system. It's the part where the design really had to be thought through carefully — you can't just flip a boolean, you need a whole new object. Using dataclasses.replace() to copy all the fields automatically was a clean solution, and the fact that Pet.complete_task() handles everything (retire the old instance, append the new one) means the rest of the code doesn't have to know anything about recurrence at all. It just calls pending_tasks() and gets back whatever is due today.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

=> I'd add support for multiple pets in the UI properly. Right now the session state only holds one pet, and while the backend fully supports multiple pets through Owner, the Streamlit UI doesn't let you add a second one. That gap between what the backend can do and what the UI exposes is a bit frustrating.

I'd also reconsider the greedy scheduling algorithm. It works and it's easy to explain, but there are situations where it makes obviously suboptimal choices — like filling up the morning window with medium-priority tasks and then having no room for a high-priority task that arrives later in the sort. A smarter approach would look at all the tasks together before committing any of them.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

=> Design on paper first, then code. I went into this thinking the UML was just a formality, but it genuinely saved time. When I had a clear picture of which class owned what, decisions during implementation were fast — I didn't have to stop and wonder "where does this method go?" because the diagram had already answered it. The times I ran into confusion were usually when I hadn't thought through a relationship clearly enough before starting to type.

On the AI side: it's a great first draft machine, but a bad decision maker. It will generate working code that violates your own design principles if you let it. The value isn't in accepting what it gives you — it's in using the output as a starting point and then pushing back when something doesn't fit.
