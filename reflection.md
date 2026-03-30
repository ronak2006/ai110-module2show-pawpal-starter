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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
