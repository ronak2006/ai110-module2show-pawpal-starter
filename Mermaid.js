classDiagram
    class Priority {
        <<enumeration>>
        LOW
        MEDIUM
        HIGH
        CRITICAL
    }

    class TimeWindow {
        <<enumeration>>
        MORNING
        AFTERNOON
        EVENING
        ANYTIME
    }

    class Task {
        +str title
        +str category
        +int duration_minutes
        +Priority priority
        +TimeWindow preferred_time
        +bool completed
        +str notes
        +str recurrence
        +str next_due
        +mark_complete() Task
        +is_due() bool
        +generate_next_occurrence() Task
    }

    class Pet {
        +str name
        +str species
        +str breed
        +int age
        +list~Task~ tasks
        +add_task(task: Task)
        +remove_task(title: str)
        +pending_tasks() list~Task~
        +complete_task(title: str) bool
    }

    class Owner {
        +str name
        +float available_hours
        +int day_start_hour
        +int day_end_hour
        +list~Pet~ pets
        +available_minutes() int
        +add_pet(pet: Pet)
        +remove_pet(name: str)
        +get_all_tasks() list~Task~
        +get_pending_tasks() list~Task~
        +filter_tasks(pet_name, status) list~Task~
    }

    class ScheduledTask {
        +Task task
        +datetime start_time
        +datetime end_time
        +str reason
        +start_str() str
        +end_str() str
    }

    class SkippedTask {
        +Task task
        +str reason
    }

    class DailyPlan {
        +str date
        +list~ScheduledTask~ scheduled_tasks
        +list~SkippedTask~ skipped_tasks
        +list~str~ conflict_warnings
        +total_scheduled_minutes() int
        +sort_by_time()
        +summary() str
    }

    class Scheduler {
        +Owner owner
        +build_plan(date: str) DailyPlan
        +detect_conflicts(plan: DailyPlan) list~str~
    }

    class sort_tasks_by_time {
        <<function>>
        +tasks list~Task~
        +returns list~Task~
    }

    Owner "1" --> "1..*" Pet
    Pet "1" --> "0..*" Task
    Task --> Priority
    Task --> TimeWindow
    ScheduledTask --> Task
    SkippedTask --> Task
    DailyPlan "1" --> "0..*" ScheduledTask
    DailyPlan "1" --> "0..*" SkippedTask
    Scheduler --> Owner
    Scheduler ..> DailyPlan : builds
    sort_tasks_by_time ..> Task : sorts
