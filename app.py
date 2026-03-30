import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, TimeWindow

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

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
owner_name    = st.text_input("Owner name", value=st.session_state.owner.name)
available_hours = st.number_input("Hours available today", min_value=0.5, max_value=12.0,
                                   value=st.session_state.owner.available_hours, step=0.5)
pet_name = st.text_input("Pet name", value=st.session_state.pet.name)
species  = st.selectbox("Species", ["dog", "cat", "other"],
                         index=["dog", "cat", "other"].index(st.session_state.pet.species)
                         if st.session_state.pet.species in ["dog", "cat", "other"] else 2)

# Sync form values back into the session state objects on every rerun
st.session_state.owner.name            = owner_name
st.session_state.owner.available_hours = available_hours
st.session_state.pet.name              = pet_name
st.session_state.pet.species           = species

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
    # Wire to backend: Pet.add_task() stores the Task object on the pet
    st.session_state.pet.add_task(new_task)
    st.success(f"Added: {new_task.title}")

# Display current task list sourced from the pet object
current_tasks = st.session_state.pet.tasks
if current_tasks:
    st.write(f"Tasks for {st.session_state.pet.name}:")
    st.table([
        {
            "Title": t.title,
            "Duration (min)": t.duration_minutes,
            "Priority": t.priority.name,
            "Window": t.preferred_time.value,
            "Done": t.completed,
        }
        for t in current_tasks
    ])
else:
    st.info("No tasks yet. Add one above.")

# ---------------------------------------------------------------------------
# Generate Schedule
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not st.session_state.pet.pending_tasks():
        st.warning("No pending tasks to schedule. Add some tasks first.")
    else:
        # Wire to backend: Scheduler.build_plan() does the work
        scheduler = Scheduler(owner=st.session_state.owner)
        plan = scheduler.build_plan()

        st.success(
            f"Scheduled {len(plan.scheduled_tasks)} task(s) — "
            f"{plan.total_scheduled_minutes()} min of {st.session_state.owner.available_minutes} min budget used."
        )

        if plan.scheduled_tasks:
            st.markdown("#### Scheduled")
            for st_task in plan.scheduled_tasks:
                st.markdown(
                    f"**{st_task.start_str} – {st_task.end_str}** &nbsp; "
                    f"`{st_task.task.priority.name}` &nbsp; {st_task.task.title}  \n"
                    f"*Why: {st_task.reason}*"
                )

        if plan.skipped_tasks:
            st.markdown("#### Skipped")
            for sk in plan.skipped_tasks:
                st.markdown(f"- **{sk.task.title}** — {sk.reason}")
