"""
constraint_engine.py
---------------------
Computes structured fitness and nutritional constraints from user profile inputs.
This is the core constraint engineering layer of the system.
"""

# ─── BMR and Calorie Estimation ───────────────────────────────────────────────

def compute_bmr(weight_kg, height_cm, age, gender):
    """
    Mifflin-St Jeor Equation for Basal Metabolic Rate (BMR).
    weight_kg  : body weight in kilograms
    height_cm  : height in centimetres
    age        : age in years
    gender     : 'male' or 'female'
    Returns BMR in kcal/day.
    """
    if gender.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return round(bmr, 1)


def compute_tdee(bmr, activity_level="moderate"):
    """
    Total Daily Energy Expenditure (TDEE) = BMR × activity multiplier.
    activity_level options:
        'sedentary'   → 1.2
        'light'       → 1.375
        'moderate'    → 1.55
        'active'      → 1.725
        'very_active' → 1.9
    """
    multipliers = {
        "sedentary":   1.2,
        "light":       1.375,
        "moderate":    1.55,
        "active":      1.725,
        "very_active": 1.9,
    }
    mult = multipliers.get(activity_level.lower(), 1.55)
    return round(bmr * mult, 1)


def compute_target_calories(tdee, goal):
    """
    Adjusts TDEE based on fitness goal.
    goal options: 'fat_loss', 'muscle_gain', 'maintenance'
    """
    adjustments = {
        "fat_loss":    -500,
        "muscle_gain": +300,
        "maintenance":    0,
    }
    delta = adjustments.get(goal.lower(), 0)
    return round(tdee + delta, 1)


# ─── Protein Requirement ─────────────────────────────────────────────────────

def compute_protein_requirement(weight_kg, goal):
    """
    Recommended daily protein intake in grams.
    goal: 'fat_loss' → 2.0 g/kg  |  'muscle_gain' → 2.2 g/kg  |  'maintenance' → 1.6 g/kg
    """
    protein_per_kg = {
        "fat_loss":    2.0,
        "muscle_gain": 2.2,
        "maintenance": 1.6,
    }
    factor = protein_per_kg.get(goal.lower(), 1.8)
    return round(weight_kg * factor, 1)


# ─── Workout Constraints ──────────────────────────────────────────────────────

def compute_workout_constraints(workout_time_minutes, goal):
    """
    Returns a dict of workout structure constraints.
    workout_time_minutes : available workout time per session
    goal : 'fat_loss', 'muscle_gain', 'maintenance'
    """
    # Muscle groups to hit per session (push-pull-legs split)
    muscle_split = {
        "fat_loss":    ["chest", "back", "legs", "cardio"],
        "muscle_gain": ["chest", "back", "legs", "shoulders", "arms"],
        "maintenance": ["chest", "back", "legs", "cardio"],
    }

    # Sets per muscle group depending on available time
    if workout_time_minutes <= 30:
        sets_per_muscle = 2
        exercises_per_muscle = 1
    elif workout_time_minutes <= 45:
        sets_per_muscle = 3
        exercises_per_muscle = 2
    else:
        sets_per_muscle = 3
        exercises_per_muscle = 3

    return {
        "muscle_groups":       muscle_split.get(goal.lower(), muscle_split["maintenance"]),
        "sets_per_muscle":     sets_per_muscle,
        "exercises_per_muscle": exercises_per_muscle,
        "session_duration_min": workout_time_minutes,
    }


# ─── Main: Build Full Constraint Profile ─────────────────────────────────────

def build_constraints(user_profile):
    """
    Accepts a user_profile dict and returns a full constraints dict.

    user_profile keys:
        name, age, gender, weight_kg, height_cm,
        goal, diet_preference, workout_time_minutes, activity_level
    """
    weight     = user_profile["weight_kg"]
    height     = user_profile["height_cm"]
    age        = user_profile["age"]
    gender     = user_profile.get("gender", "male")
    goal       = user_profile["goal"]
    activity   = user_profile.get("activity_level", "moderate")
    workout_t  = user_profile.get("workout_time_minutes", 45)

    bmr      = compute_bmr(weight, height, age, gender)
    tdee     = compute_tdee(bmr, activity)
    calories = compute_target_calories(tdee, goal)
    protein  = compute_protein_requirement(weight, goal)
    workout  = compute_workout_constraints(workout_t, goal)

    constraints = {
        "bmr_kcal":              bmr,
        "tdee_kcal":             tdee,
        "target_calories_kcal":  calories,
        "min_protein_g":         protein,
        "workout":               workout,
        "goal":                  goal,
        "diet_preference":       user_profile.get("diet_preference", "non-vegetarian"),
    }
    return constraints


# ─── Validation Helper ────────────────────────────────────────────────────────

def validate_inputs(user_profile):
    """
    Validates user profile inputs. Returns (is_valid, error_message).
    """
    required_keys = ["age", "weight_kg", "height_cm", "goal"]
    for key in required_keys:
        if key not in user_profile:
            return False, f"Missing required field: {key}"

    if not (10 <= user_profile["age"] <= 100):
        return False, "Age must be between 10 and 100."
    if not (30 <= user_profile["weight_kg"] <= 250):
        return False, "Weight must be between 30 and 250 kg."
    if not (100 <= user_profile["height_cm"] <= 250):
        return False, "Height must be between 100 and 250 cm."
    valid_goals = ["fat_loss", "muscle_gain", "maintenance"]
    if user_profile["goal"].lower() not in valid_goals:
        return False, f"Goal must be one of: {valid_goals}"

    return True, "OK"
