flowchart TD
    subgraph UI["Streamlit UI (app.py)"]
        A[Owner & Pet Info Form]
        B[AI Care Intelligence Panel]
        C[Add Task Form]
        D[Task List & Complete]
        E[Filter Tasks]
        F[Generate Schedule]
    end

    subgraph Agent["AI Agent (ai_agent.py)"]
        G[analyze_care_context]
        H[Gemini 2.5 Flash API]
    end

    subgraph Eval["Reliability Harness (eval_agent.py)"]
        I[Test Case 1: Time Crunch]
        J[Test Case 2: Extreme Heat]
        K[PASS / FAIL Verdict]
    end

    subgraph Core["Backend Logic (pawpal_system.py)"]
        L[Owner]
        M[Pet]
        N[Task]
        O[Scheduler]
        P[DailyPlan]
        Q[ScheduledTask]
        R[SkippedTask]
    end

    %% UI → Core
    A -->|sets name, hours| L
    A -->|sets name, species| M
    C -->|add_task| M
    D -->|complete_task| M
    E -->|filter_tasks| L
    F -->|build_plan| O

    %% UI → AI Agent
    B -->|daily context + pet + owner| G
    G -->|prompt| H
    H -->|JSON suggestions| G
    G -->|suggestions list| B
    B -->|apply: modify/add/remove| M

    %% Core data flow
    L -->|get_pending_tasks| O
    M -->|tasks| L
    O -->|DailyPlan| P
    P --> Q
    P --> R
    O -->|detect_conflicts| P

    %% Eval → Agent
    I -->|analyze_care_context| G
    J -->|analyze_care_context| G
    G -->|suggestions| K
