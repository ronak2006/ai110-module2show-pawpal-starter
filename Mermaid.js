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
          +str notes
      }

      class Pet {
          +str name
          +str species
          +str breed
          +int age
      }

      class Owner {
          +str name
          +float available_hours
          +int day_start_hour
          +int day_end_hour
          +available_minutes() int
      }

      class ScheduledTask {
          +Task task
          +datetime start_time
          +datetime end_time
          +str reason
      }

      class SkippedTask {
          +Task task
          +str reason
      }

      class DailyPlan {
          +str date
          +list~ScheduledTask~ scheduled_tasks
          +list~SkippedTask~ skipped_tasks
          +total_scheduled_minutes() int
          +summary() str
      }

      class Scheduler {
          +Owner owner
          +list~Task~ tasks
          +add_task(task: Task)
          +build_plan(date: str) DailyPlan
      }

      Owner "1" --> "1..*" Pet
      Task --> Priority
      Task --> TimeWindow
      ScheduledTask --> Task
      SkippedTask --> Task
      DailyPlan "1" --> "0..*" ScheduledTask
      DailyPlan "1" --> "0..*" SkippedTask
      Scheduler --> Owner
      Scheduler "1" --> "0..*" Task
      Scheduler ..> DailyPlan : builds
