import os
import json
from dotenv import load_dotenv
from pawpal_system import Owner, Pet, Task, Priority, TimeWindow
from ai_agent import analyze_care_context

load_dotenv()

def run_evaluation():
    print("=========================================")
    print("  PawPal+ AI Reliability Evaluator")
    print("=========================================")

    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
        print("[ERROR] GEMINI_API_KEY is not set. Please set it in your .env file.")
        return

    # Base setup
    test_owner = Owner(name="Test Owner", available_hours=1.0) # 60 minutes
    test_pet = Pet(name="Max", species="dog")
    test_owner.add_pet(test_pet)
    
    base_task_1 = Task(title="Morning walk", category="walk", duration_minutes=45, priority=Priority.HIGH, preferred_time=TimeWindow.MORNING)
    base_task_2 = Task(title="Evening walk", category="walk", duration_minutes=45, priority=Priority.MEDIUM, preferred_time=TimeWindow.EVENING)
    base_task_3 = Task(title="Feeding", category="feeding", duration_minutes=10, priority=Priority.CRITICAL, preferred_time=TimeWindow.ANYTIME)

    # --- Test Case 1: Over Budget Constraint ---
    print("\n[Test Case 1] Constraint Checking: Severe Time Crunch")
    print("Context: 'I only have 15 minutes today total.'")
    test_owner.available_hours = 0.25 # 15 minutes
    test_pet.tasks = [base_task_1, base_task_2, base_task_3]
    
    result_1 = analyze_care_context("I only have 15 minutes today total.", test_pet, test_owner)
    
    if "error" in result_1:
        print(f"FAILED: API Error - {result_1['error']}")
    else:
        suggestions = result_1.get("suggestions", [])
        # We expect the AI to remove or severely reduce the walks so the total time <= 15
        print(f"Suggestions generated: {len(suggestions)}")
        for s in suggestions:
            action = s.get("action", "unknown")
            target = s.get("target_title", s.get("task_data", {}).get("title", "unknown"))
            print(f"  - {action.upper()}: {target} ({s.get('reason')})")
        
        # Calculate simulated new duration
        simulated_time = 0
        removed = [s["target_title"] for s in suggestions if s["action"] == "remove"]
        modified = {s["target_title"]: s["task_data"].get("duration_minutes", 0) for s in suggestions if s["action"] == "modify"}
        
        for t in test_pet.tasks:
            if t.title in removed:
                continue
            simulated_time += modified.get(t.title, t.duration_minutes)
            
        print(f"Simulated new total duration: {simulated_time} min")
        if simulated_time <= 15:
            print("=> PASS: AI respected the time constraint.")
        else:
            print("=> FAIL: AI suggested tasks exceeding the time limit.")

    # --- Test Case 2: Health/Safety Context ---
    print("\n[Test Case 2] Safety Guardrail: Extreme Heat")
    print("Context: 'It is 105 degrees outside today.'")
    test_owner.available_hours = 3.0 # Plenty of time
    test_pet.tasks = [base_task_1, base_task_2, base_task_3]

    result_2 = analyze_care_context("It is 105 degrees outside today.", test_pet, test_owner)
    
    if "error" in result_2:
        print(f"FAILED: API Error - {result_2['error']}")
    else:
        suggestions = result_2.get("suggestions", [])
        print(f"Suggestions generated: {len(suggestions)}")
        
        addressed_heat = False
        for s in suggestions:
            reason = s.get("reason", "").lower()
            action = s.get("action", "unknown")
            target = s.get("target_title", "")
            print(f"  - {action.upper()}: {target} ({s.get('reason')})")
            
            if "walk" in target.lower():
                if action in ["remove", "modify"] and ("hot" in reason or "heat" in reason or "temperature" in reason or "105" in reason):
                    addressed_heat = True

        if addressed_heat:
            print("=> PASS: AI appropriately altered walking tasks due to heat.")
        else:
            print("=> FAIL: AI did not alter walks or cite the extreme heat as a reason.")

    print("\n=========================================")
    print("Evaluation Complete.")

if __name__ == "__main__":
    run_evaluation()
