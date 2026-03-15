"""
dataset_loader.py
-----------------
Loads and preprocesses the Nutrition and Exercise datasets.
Datasets:
  - FoodData Central (Kaggle)
  - Gym Exercise Dataset (Kaggle)
"""

import pandas as pd
import os

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
NUTRITION_FILE = os.path.join(DATA_DIR, "nutrition_dataset.csv")
EXERCISE_FILE  = os.path.join(DATA_DIR, "exercise_dataset.csv")


# ─── Nutrition Dataset ────────────────────────────────────────────────────────
def load_nutrition_data():
    """
    Loads and preprocesses the FoodData Central nutrition dataset.
    Returns a cleaned DataFrame with: name, calories, protein, carbs, fat
    """
    if not os.path.exists(NUTRITION_FILE):
        print("[WARNING] nutrition_dataset.csv not found. Using built-in sample data.")
        return _sample_nutrition_data()

    df = pd.read_csv(NUTRITION_FILE)

    # Step 1: Rename columns to standard names (adjust if column names differ)
    col_map = {}
    for col in df.columns:
        cl = col.lower()
        if "name" in cl or "food" in cl or "descrip" in cl:
            col_map[col] = "name"
        elif "calor" in cl or "energy" in cl or "kcal" in cl:
            col_map[col] = "calories"
        elif "protein" in cl:
            col_map[col] = "protein"
        elif "carb" in cl:
            col_map[col] = "carbs"
        elif "fat" in cl and "saturated" not in cl:
            col_map[col] = "fat"
    df = df.rename(columns=col_map)

    # Step 2: Keep only needed columns
    needed = [c for c in ["name", "calories", "protein", "carbs", "fat"] if c in df.columns]
    df = df[needed].copy()

    # Step 3: Drop duplicates and missing calorie/protein rows
    df.drop_duplicates(subset=["name"], inplace=True)
    df.dropna(subset=["calories"], inplace=True)

    # Step 4: Convert numeric columns
    for col in ["calories", "protein", "carbs", "fat"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(subset=["calories"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    print(f"[INFO] Nutrition dataset loaded: {len(df)} entries")
    return df


def _sample_nutrition_data():
    """Fallback sample nutrition data (per 100g)"""
    data = {
        "name":     ["Oats", "Brown Rice", "Chicken Breast", "Paneer", "Egg",
                     "Banana", "Whole Milk", "Lentils", "Quinoa", "Almonds",
                     "Spinach", "Sweet Potato", "Tofu", "Curd / Yogurt", "Peanut Butter"],
        "calories": [389, 216, 165, 265, 155, 89, 61, 116, 120, 579,
                     23, 86, 76, 59, 588],
        "protein":  [17, 5, 31, 18, 13, 1.1, 3.2, 9, 4.4, 21,
                     2.9, 1.6, 8, 3.5, 25],
        "carbs":    [66, 45, 0, 3.6, 1.1, 23, 4.8, 20, 22, 22,
                     3.6, 20, 2, 3.6, 20],
        "fat":      [7, 1.8, 3.6, 20, 11, 0.3, 3.3, 0.4, 1.9, 50,
                     0.4, 0.1, 4.8, 3.3, 50],
    }
    return pd.DataFrame(data)


# ─── Exercise Dataset ─────────────────────────────────────────────────────────
def load_exercise_data():
    """
    Loads and preprocesses the Gym Exercise Dataset.
    Returns a cleaned DataFrame with: name, muscle_group, type, difficulty, equipment
    """
    if not os.path.exists(EXERCISE_FILE):
        print("[WARNING] exercise_dataset.csv not found. Using built-in sample data.")
        return _sample_exercise_data()

    df = pd.read_csv(EXERCISE_FILE)

    # Drop any unnamed index columns
    df = df.loc[:, ~df.columns.str.startswith('Unnamed')]

    # Step 1: Standardize column names
    col_map = {}
    for col in df.columns:
        cl = col.lower()
        if "title" in cl or "name" in cl or "exercise" in cl:
            col_map[col] = "name"
        elif "muscle" in cl or "bodypart" in cl or "target" in cl:
            col_map[col] = "muscle_group"
        elif "type" in cl or "category" in cl:
            col_map[col] = "type"
        elif "level" in cl or "diffic" in cl:
            col_map[col] = "difficulty"
        elif "equip" in cl:
            col_map[col] = "equipment"
    df = df.rename(columns=col_map)

    # Step 2: Keep relevant columns
    needed = [c for c in ["name", "muscle_group", "type", "difficulty", "equipment"] if c in df.columns]
    df = df[needed].copy()

    # Step 3: Clean
    df.drop_duplicates(subset=["name"], inplace=True)
    df.dropna(subset=["muscle_group"], inplace=True)
    df["muscle_group"] = df["muscle_group"].str.strip().str.lower()
    df.reset_index(drop=True, inplace=True)

    print(f"[INFO] Exercise dataset loaded: {len(df)} entries")
    return df


def _sample_exercise_data():
    """Fallback sample exercise data"""
    data = {
        "name": [
            "Push Ups", "Bench Press", "Incline Dumbbell Press",
            "Pull Ups", "Lat Pulldown", "Bent Over Row",
            "Squats", "Lunges", "Leg Press",
            "Shoulder Press", "Lateral Raise",
            "Bicep Curls", "Tricep Dips",
            "Plank", "Crunches",
            "Treadmill Run", "Jumping Jacks", "Cycling"
        ],
        "muscle_group": [
            "chest", "chest", "chest",
            "back", "back", "back",
            "legs", "legs", "legs",
            "shoulders", "shoulders",
            "arms", "arms",
            "core", "core",
            "cardio", "cardio", "cardio"
        ],
        "type": [
            "strength"] * 15 + ["cardio"] * 3,
        "difficulty": [
            "beginner", "intermediate", "intermediate",
            "intermediate", "beginner", "intermediate",
            "beginner", "beginner", "intermediate",
            "intermediate", "beginner",
            "beginner", "intermediate",
            "beginner", "beginner",
            "beginner", "beginner", "beginner"
        ],
        "equipment": [
            "none", "barbell", "dumbbell",
            "none", "machine", "barbell",
            "none", "none", "machine",
            "dumbbell", "dumbbell",
            "dumbbell", "none",
            "none", "none",
            "treadmill", "none", "cycle"
        ]
    }
    return pd.DataFrame(data)


# ─── Muscle group alias mapping ───────────────────────────────────────────────
# The Kaggle exercise dataset uses specific names (e.g. "quadriceps", "lats")
# but our constraint engine uses generic names (e.g. "legs", "back").
# This mapping bridges the two.

MUSCLE_ALIASES = {
    "legs":     ["quadriceps", "hamstrings", "glutes", "calves", "abductors", "adductors"],
    "back":     ["lats", "middle back", "lower back", "traps"],
    "arms":     ["biceps", "triceps", "forearms"],
    "core":     ["abdominals"],
    "cardio":   ["cardio"],
    "chest":    ["chest"],
    "shoulders":["shoulders"],
}


# ─── Categorized exercise lookup ──────────────────────────────────────────────
def get_exercises_by_muscle(df_exercise, muscle, difficulty=None, equipment=None):
    """
    Returns a filtered list of exercises by muscle group.
    Uses MUSCLE_ALIASES to map generic names to dataset-specific names.
    Optionally filter by difficulty or equipment.
    """
    # Expand generic muscle name to all matching specific names
    aliases = MUSCLE_ALIASES.get(muscle.lower(), [muscle.lower()])

    result = df_exercise[df_exercise["muscle_group"].str.lower().isin(aliases)]
    if difficulty:
        result = result[result["difficulty"].str.lower() == difficulty.lower()]
    if equipment == "none":
        result = result[result["equipment"].str.lower().isin(["none", "bodyweight"])]
    return result["name"].values.tolist()


# ─── Calorie lookup ───────────────────────────────────────────────────────────
def lookup_calories(df_nutrition, food_name):
    """Returns calories (per 100g) for a food item. Returns None if not found."""
    match = df_nutrition[df_nutrition["name"].str.lower() == food_name.lower()]
    if not match.empty:
        return float(match.iloc[0]["calories"])
    return None


def lookup_protein(df_nutrition, food_name):
    """Returns protein (per 100g) for a food item."""
    match = df_nutrition[df_nutrition["name"].str.lower() == food_name.lower()]
    if not match.empty and "protein" in match.columns:
        return float(match.iloc[0]["protein"])
    return None
