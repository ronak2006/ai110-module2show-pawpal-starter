"""
tests/test_pawpal.py — Unit tests for PawPal+ core logic.
Run with: python -m pytest
"""

from pawpal_system import Pet, Task, Priority, TimeWindow


def test_mark_complete_changes_status():
    """Calling mark_complete() should flip completed from False to True."""
    task = Task(title="Morning walk", category="walk", duration_minutes=30)

    assert task.completed is False  # starts incomplete

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list by one."""
    pet = Pet(name="Mochi", species="dog")

    assert len(pet.tasks) == 0  # starts empty

    pet.add_task(Task(title="Feeding", category="feeding", duration_minutes=10))

    assert len(pet.tasks) == 1