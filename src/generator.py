"""
generator.py
-------------
Controlled Generative Engine.
Builds structured prompts from user constraints and dataset data,
then calls an open-source LLM (via HuggingFace or Groq API) to generate
personalized workout and diet plans.
"""

import os
import random

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from transformers import pipeline as hf_pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


# ─── Prompt Builder ────────────────────────────────────────────────────────────

def build_prompt(user_profile, constraints, exercise_suggestions):
    """
    Constructs a structured prompt that embeds all constraints for the LLM.
    Returns a string prompt.
    """
    name   = user_profile.get("name", "User")
    goal   = constraints["goal"].replace("_", " ").title()
    diet   = constraints["diet_preference"].title()
    cal    = constraints["target_calories_kcal"]
    prot   = constraints["min_protein_g"]
    w_time = constraints["workout"]["session_duration_min"]

    # Build exercise hint string
    exercise_hint = ""
    for muscle, exlist in exercise_suggestions.items():
        if exlist:
            sample = exlist[:constraints["workout"]["exercises_per_muscle"]]
            exercise_hint += f"  - {muscle.title()}: {', '.join(sample)}\n"

    prompt = f"""
You are a certified fitness and nutrition expert AI.

Generate a personalized 7-day fitness and nutrition plan for the following user:

USER PROFILE:
- Name: {name}
- Goal: {goal}
- Diet Preference: {diet}
- Target Calories per Day: {cal} kcal
- Minimum Protein per Day: {prot} g
- Workout Duration per Session: {w_time} minutes

AVAILABLE EXERCISES (use these categories):
{exercise_hint}

INSTRUCTIONS:
1. Create a 7-day WORKOUT PLAN:
   - Label each day (Day 1, Day 2, ... Day 7)
   - Day 7 is a rest/active recovery day
   - Include exercise name, sets, and reps for each exercise
   - Balance muscle groups across the week
   - Keep session within {w_time} minutes

2. Create a DAILY DIET PLAN (same plan repeated daily or with variation):
   - Include Breakfast, Mid-Morning Snack, Lunch, Evening Snack, Dinner
   - Match the {diet} preference
   - Stay close to {cal} kcal total
   - Ensure at least {prot} g of protein

3. At the end, provide a SUMMARY with:
   - Estimated daily calories
   - Estimated daily protein
   - Key fitness tip for this goal

Keep the output structured and clearly formatted.
"""
    return prompt.strip()


# ─── LLM Call ─────────────────────────────────────────────────────────────────

def call_llm_groq(prompt, api_key=None):
    """
    Calls Groq API (free, fast) with llama3-8b-8192 model.
    Requires GROQ_API_KEY environment variable or passed api_key.
    """
    if not GROQ_AVAILABLE:
        raise ImportError("groq package not installed. Run: pip install groq")

    key = api_key or os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY not set. Set it as environment variable or pass api_key.")

    client = Groq(api_key=key)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1500,
    )
    return completion.choices[0].message.content


def call_llm_huggingface(prompt, model_name="mistralai/Mistral-7B-Instruct-v0.1"):
    """
    Calls a local HuggingFace model.
    Requires transformers and enough RAM/GPU.
    """
    if not TRANSFORMERS_AVAILABLE:
        raise ImportError("transformers package not installed. Run: pip install transformers")

    generator = hf_pipeline("text-generation", model=model_name, max_new_tokens=1000)
    result = generator(prompt, temperature=0.7, do_sample=True)
    return result[0]["generated_text"][len(prompt):].strip()


def call_llm_mock(prompt):
    """
    MOCK LLM — returns a hardcoded sample plan.
    Used for testing without API keys or local models.
    """
    return """
=== 7-DAY WORKOUT PLAN ===

Day 1 - Chest & Triceps
- Push Ups: 3 sets x 15 reps
- Bench Press: 3 sets x 10 reps
- Tricep Dips: 3 sets x 12 reps

Day 2 - Back & Biceps
- Pull Ups: 3 sets x 8 reps
- Lat Pulldown: 3 sets x 12 reps
- Bicep Curls: 3 sets x 12 reps

Day 3 - Legs
- Squats: 3 sets x 15 reps
- Lunges: 3 sets x 12 reps per leg
- Leg Press: 3 sets x 15 reps

Day 4 - Shoulders & Core
- Shoulder Press: 3 sets x 10 reps
- Lateral Raise: 3 sets x 15 reps
- Plank: 3 sets x 45 seconds

Day 5 - Full Body + Cardio
- Jumping Jacks: 10 minutes
- Push Ups: 2 sets x 15 reps
- Squats: 2 sets x 15 reps

Day 6 - Cardio
- Treadmill Run: 30 minutes moderate pace

Day 7 - Rest / Active Recovery
- Light stretching or yoga

=== DAILY DIET PLAN ===

Breakfast:
- Oats with milk and banana — ~400 kcal, ~18g protein

Mid-Morning Snack:
- Almonds (30g) + curd — ~200 kcal, ~10g protein

Lunch:
- Brown rice + lentils + spinach sabzi — ~500 kcal, ~22g protein

Evening Snack:
- Peanut butter (2 tbsp) + whole wheat bread — ~250 kcal, ~12g protein

Dinner:
- Paneer curry + quinoa — ~550 kcal, ~28g protein

=== SUMMARY ===
Estimated Daily Calories: ~1900 kcal
Estimated Daily Protein: ~90g
Key Tip: Stay consistent with your meals and get 7-8 hours of sleep for optimal recovery.
"""


# ─── Main Generator Function ──────────────────────────────────────────────────

def generate_plan(user_profile, constraints, exercise_suggestions,
                  mode="mock", groq_api_key=None):
    """
    Main function to generate the fitness and diet plan.

    mode options:
        'mock'         - returns demo output (no API required)
        'groq'         - uses Groq API (free, recommended)
        'huggingface'  - uses local HuggingFace model

    Returns: (prompt_used, generated_plan_text)
    """
    prompt = build_prompt(user_profile, constraints, exercise_suggestions)

    if mode == "groq":
        plan = call_llm_groq(prompt, api_key=groq_api_key)
    elif mode == "huggingface":
        plan = call_llm_huggingface(prompt)
    else:
        # Default: mock
        plan = call_llm_mock(prompt)

    return prompt, plan
