import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, TimeWindow, sort_tasks_by_time
from ai_agent import analyze_care_context

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.markdown("Plan and track daily care tasks for your pet.")

st.divider()

# ---------------------------------------------------------------------------
# Session state — initialize once, persist across reruns
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_hours=3.0)

if "pet" not in st.session_state:
    st.session_state.pet = Pet(name="Mochi", species="dog")
    st.session_state.owner.add_pet(st.session_state.pet)

# ---------------------------------------------------------------------------
# Owner & Pet Info
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet Info")
col_a, col_b = st.columns(2)
with col_a:
    owner_name      = st.text_input("Owner name", value=st.session_state.owner.name)
    available_hours = st.number_input("Hours available today", min_value=0.5, max_value=12.0,
                                       value=st.session_state.owner.available_hours, step=0.5)
with col_b:
    pet_name = st.text_input("Pet name", value=st.session_state.pet.name)
    species  = st.selectbox("Species", ["dog", "cat", "other"],
                             index=["dog", "cat", "other"].index(st.session_state.pet.species)
                             if st.session_state.pet.species in ["dog", "cat", "other"] else 2)

st.session_state.owner.name            = owner_name
st.session_state.owner.available_hours = available_hours
st.session_state.pet.name              = pet_name
st.session_state.pet.species           = species

# ---------------------------------------------------------------------------
# AI Care Intelligence — Context-aware adjustments
# ---------------------------------------------------------------------------
st.divider()
st.subheader("🤖 AI Care Intelligence")
st.markdown(
    "Provide context about your day or your pet's condition. "
    "The AI will suggest schedule adjustments or new tasks based on this context."
)

daily_context = st.text_area(
    "Daily Context",
    placeholder="e.g., 'Mochi seems a bit lethargic today' or 'It's very hot outside' or 'I have a late meeting today'",
    help="Describe anything unusual about today that might affect your pet's care."
)

if st.button("Analyze Context & Suggest Adjustments"):
    if not daily_context:
        st.warning("Please provide some context first.")
    else:
        with st.spinner("AI is analyzing context and your current plan..."):
            result = analyze_care_context(daily_context, st.session_state.pet, st.session_state.owner)

        if "error" in result:
            st.error(f"AI Error: {result['error']}")
        else:
            suggestions = result.get("suggestions", [])
            if not suggestions:
                st.info("AI analyzed your context and found no adjustments needed.")
            else:
                st.session_state["ai_suggestions"] = suggestions
                st.success(f"AI found {len(suggestions)} suggestion(s):")
                for s in suggestions:
                    action = s.get("action", "?").upper()
                    target = s.get("target_title") or s.get("task_data", {}).get("title", "new task")
                    reason = s.get("reason", "")
                    st.markdown(f"- **{action}** `{target}` — {reason}")

if "ai_suggestions" in st.session_state and st.session_state["ai_suggestions"]:
    if st.button("Apply AI Suggestions"):
        pet = st.session_state.pet
        applied = []
        for s in st.session_state["ai_suggestions"]:
            action = s.get("action")
            target = s.get("target_title", "")
            task_data = s.get("task_data", {})

            if action == "remove":
                pet.remove_task(target)
                applied.append(f"Removed: {target}")

            elif action == "modify":
                for t in pet.tasks:
                    if t.title == target and not t.completed:
                        if "duration_minutes" in task_data:
                            t.duration_minutes = int(task_data["duration_minutes"])
                        if "priority" in task_data:
                            t.priority = Priority[task_data["priority"]]
                        if "preferred_time" in task_data:
                            t.preferred_time = TimeWindow[task_data["preferred_time"]]
                        if "notes" in task_data:
                            t.notes = task_data["notes"]
                        break
                applied.append(f"Modified: {target}")

            elif action == "add":
                new_task = Task(
                    title=task_data.get("title", "AI Task"),
                    category="ai_suggested",
                    duration_minutes=int(task_data.get("duration_minutes", 15)),
                    priority=Priority[task_data.get("priority", "MEDIUM")],
                    preferred_time=TimeWindow[task_data.get("preferred_time", "ANYTIME")],
                    notes=task_data.get("notes", ""),
                )
                pet.add_task(new_task)
                applied.append(f"Added: {new_task.title}")

        del st.session_state["ai_suggestions"]
        st.success("Applied: " + ", ".join(applied))
        st.rerun()

# ---------------------------------------------------------------------------
# Add a Task
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Add a Task")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority_str = st.selectbox("Priority", ["LOW", "MEDIUM", "HIGH", "CRITICAL"], index=2)
with col4:
    window_str = st.selectbox("Time window", ["MORNING", "AFTERNOON", "EVENING", "ANYTIME"], index=3)

if st.button("Add task"):
    new_task = Task(
        title=task_title,
        category="general",
        duration_minutes=int(duration),
        priority=Priority[priority_str],
        preferred_time=TimeWindow[window_str],
    )
    st.session_state.pet.add_task(new_task)
    st.success(f"Added: {new_task.title}")

# ---------------------------------------------------------------------------
# Task List — sorted by time window using sort_tasks_by_time()
# ---------------------------------------------------------------------------
st.divider()
st.subheader(f"Tasks for {st.session_state.pet.name}")

all_tasks = st.session_state.pet.tasks
if all_tasks:
    sorted_tasks = sort_tasks_by_time(all_tasks)   # algorithmic sort

    st.caption("Sorted by preferred time window, then priority.")
    st.table([
        {
            "Title":         t.title,
            "Window":        t.preferred_time.value.capitalize(),
            "Priority":      t.priority.name,
            "Duration (min)": t.duration_minutes,
            "Status":        "Done" if t.completed else "Pending",
        }
        for t in sorted_tasks
    ])

    # Mark a task complete
    pending_titles = [t.title for t in all_tasks if not t.completed]
    if pending_titles:
        st.markdown("**Mark a task complete:**")
        col_m1, col_m2 = st.columns([3, 1])
        with col_m1:
            task_to_complete = st.selectbox("Select task", pending_titles, label_visibility="collapsed")
        with col_m2:
            if st.button("Mark done"):
                st.session_state.pet.complete_task(task_to_complete)
                st.success(f"Marked '{task_to_complete}' as done.")
                st.rerun()
else:
    st.info("No tasks yet. Add one above.")

# ---------------------------------------------------------------------------
# Filter tasks using Owner.filter_tasks()
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Filter Tasks")

filter_status = st.radio("Show", ["all", "pending", "done"], horizontal=True)

filter_map = {"all": None, "pending": "pending", "done": "done"}
filtered = st.session_state.owner.filter_tasks(status=filter_map[filter_status])

if filtered:
    st.table([
        {
            "Title":    t.title,
            "Priority": t.priority.name,
            "Window":   t.preferred_time.value.capitalize(),
            "Status":   "Done" if t.completed else "Pending",
        }
        for t in filtered
    ])
else:
    st.info(f"No {filter_status} tasks found.")

# ---------------------------------------------------------------------------
# Generate Schedule — with conflict warnings
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Build Today's Schedule")

budget_pct = (
    sum(t.duration_minutes for t in st.session_state.pet.pending_tasks())
    / st.session_state.owner.available_minutes * 100
    if st.session_state.owner.available_minutes > 0 else 0
)
st.caption(
    f"Budget: {st.session_state.owner.available_minutes} min available — "
    f"pending tasks total ~{budget_pct:.0f}% of that."
)

if st.button("Generate schedule"):
    pending = st.session_state.pet.pending_tasks()
    if not pending:
        st.warning("No pending tasks to schedule. Add some tasks first.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner)
        plan      = scheduler.build_plan()

        # ── Conflict warnings — shown before the plan so owner sees them first
        if plan.conflict_warnings:
            for warning in plan.conflict_warnings:
                st.warning(f"Scheduling conflict: {warning}")

        # ── Budget summary
        used = plan.total_scheduled_minutes()
        budget = st.session_state.owner.available_minutes
        if used <= budget:
            st.success(
                f"Scheduled {len(plan.scheduled_tasks)} task(s) — "
                f"{used} of {budget} min used."
            )
        else:
            st.error(f"Over budget! {used} min scheduled vs {budget} min available.")

        # ── Scheduled tasks
        if plan.scheduled_tasks:
            st.markdown("#### Scheduled")
            for s in plan.scheduled_tasks:
                priority_color = {
                    "CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"
                }.get(s.task.priority.name, "⚪")
                st.markdown(
                    f"{priority_color} **{s.start_str} – {s.end_str}** &nbsp; "
                    f"`{s.task.priority.name}` &nbsp; {s.task.title}  \n"
                    f"&nbsp;&nbsp;&nbsp; *{s.reason}*"
                )

        # ── Skipped tasks
        if plan.skipped_tasks:
            st.markdown("#### Skipped")
            for sk in plan.skipped_tasks:
                st.warning(f"**{sk.task.title}** was skipped — {sk.reason}")