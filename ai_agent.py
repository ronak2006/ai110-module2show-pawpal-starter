import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
from pawpal_system import Task, Priority, TimeWindow

load_dotenv()

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

def analyze_care_context(context, pet, owner):
    """
    Uses Gemini to analyze the context and suggest task modifications or additions.
    Returns a list of suggested changes.
    """
    model = get_gemini_client()
    if not model:
        return {"error": "API Key not configured. Please set GEMINI_API_KEY in .env"}

    # Prepare the prompt
    current_tasks = [
        f"- {t.title} ({t.duration_minutes} min, {t.priority.name}, {t.preferred_time.value})"
        for t in pet.tasks if not t.completed
    ]
    
    prompt = f"""
    You are an expert pet care assistant. 
    Pet: {pet.name} ({pet.species})
    Owner's Daily Budget: {owner.available_minutes} minutes
    User's Context: "{context}"
    Current Pending Tasks:
    {chr(10).join(current_tasks)}

    Based on the context, suggest adjustments. You can:
    1. Modify an existing task (e.g., reduce duration, change window, change priority).
    2. Suggest a new task.
    3. Suggest skipping/removing a task.

    Response MUST be a JSON list of actions. Each action has:
    - action: "modify", "add", or "remove"
    - target_title: (for modify/remove)
    - task_data: (for add/modify) a dictionary matching Task fields: 
        {{ "title": str, "duration_minutes": int, "priority": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL", "preferred_time": "MORNING"|"AFTERNOON"|"EVENING"|"ANYTIME", "notes": str }}
    - reason: A short explanation for the user.

    Example:
    [
      {{ "action": "modify", "target_title": "Morning walk", "task_data": {{ "duration_minutes": 10, "notes": "Keep it short due to heat" }}, "reason": "It's too hot for a long walk." }}
    ]
    """

    try:
        response = model.generate_content(prompt)
        # Clean the response to ensure it's valid JSON
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        
        suggestions = json.loads(text)
        return {"suggestions": suggestions}
    except Exception as e:
        return {"error": f"Failed to get AI suggestions: {str(e)}"}
