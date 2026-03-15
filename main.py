"""
main.py
--------
Main entry point for the Constraint-Aware Generative AI Fitness & Nutrition System.
Runs the complete pipeline:
  1. Load datasets
  2. Get user profile
  3. Compute constraints
  4. Generate plan (LLM)
  5. Validate plan
  6. Evaluate metrics
  7. Save results
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dataset_loader    import load_nutrition_data, load_exercise_data, get_exercises_by_muscle
from constraint_engine import build_constraints, validate_inputs
from generator         import generate_plan
from validator         import validate_plan, print_validation_report
from evaluator         import evaluate_single, save_results_csv, save_results_json, \
                              print_evaluation_summary, evaluate_experiments, print_aggregate_summary


# ─── Sample User Profiles (for experiments) ───────────────────────────────────

SAMPLE_PROFILES = [
    {
        "name": "Aditya",
        "age": 22, "gender": "male",
        "weight_kg": 75, "height_cm": 175,
        "goal": "muscle_gain",
        "diet_preference": "vegetarian",
        "workout_time_minutes": 60,
        "activity_level": "moderate",
    },
    {
        "name": "Priya",
        "age": 28, "gender": "female",
        "weight_kg": 60, "height_cm": 160,
        "goal": "fat_loss",
        "diet_preference": "vegetarian",
        "workout_time_minutes": 40,
        "activity_level": "light",
    },
    {
        "name": "Rahul",
        "age": 35, "gender": "male",
        "weight_kg": 85, "height_cm": 178,
        "goal": "fat_loss",
        "diet_preference": "non-vegetarian",
        "workout_time_minutes": 45,
        "activity_level": "moderate",
    },
    {
        "name": "Sneha",
        "age": 24, "gender": "female",
        "weight_kg": 55, "height_cm": 162,
        "goal": "maintenance",
        "diet_preference": "vegetarian",
        "workout_time_minutes": 30,
        "activity_level": "light",
    },
    {
        "name": "Vikram",
        "age": 42, "gender": "male",
        "weight_kg": 90, "height_cm": 172,
        "goal": "fat_loss",
        "diet_preference": "non-vegetarian",
        "workout_time_minutes": 50,
        "activity_level": "sedentary",
    },
]


# ─── Pipeline for a Single Profile ────────────────────────────────────────────

def run_pipeline(user_profile, df_nutrition, df_exercise,
                 gen_mode="mock", groq_api_key=None, verbose=True):
    """
    Full end-to-end pipeline for one user profile.
    Returns a dict with plan, validation report, and evaluation metrics.
    """

    # Step 1: Validate inputs
    ok, msg = validate_inputs(user_profile)
    if not ok:
        print(f"[ERROR] Invalid inputs for {user_profile.get('name', 'User')}: {msg}")
        return None

    # Step 2: Compute constraints
    constraints = build_constraints(user_profile)
    if verbose:
        print(f"\n[Constraints for {user_profile['name']}]")
        print(f"  Target Calories : {constraints['target_calories_kcal']} kcal")
        print(f"  Min Protein     : {constraints['min_protein_g']} g")
        print(f"  Muscle Groups   : {constraints['workout']['muscle_groups']}")

    # Step 3: Prepare exercise suggestions
    exercise_suggestions = {}
    for muscle in constraints["workout"]["muscle_groups"]:
        ex_list = get_exercises_by_muscle(df_exercise, muscle)
        exercise_suggestions[muscle] = ex_list[:5]  # top 5 per muscle

    # Step 4: Generate plan
    prompt, plan_text = generate_plan(
        user_profile, constraints, exercise_suggestions,
        mode=gen_mode, groq_api_key=groq_api_key
    )
    if verbose:
        print(f"\n{'─'*55}")
        print(f"  GENERATED PLAN FOR: {user_profile['name'].upper()}")
        print(f"{'─'*55}")
        print(plan_text)

    # Step 5: Validate
    val_report = validate_plan(plan_text, constraints)
    if verbose:
        print_validation_report(val_report)

    # Step 6: Evaluate
    metrics = evaluate_single(val_report)
    metrics["profile_name"] = user_profile["name"]
    metrics["goal"]         = user_profile["goal"]
    metrics["diet"]         = user_profile["diet_preference"]
    if verbose:
        print_evaluation_summary(metrics, profile_name=user_profile["name"])

    return {
        "profile":     user_profile,
        "constraints": constraints,
        "plan_text":   plan_text,
        "validation":  val_report,
        "metrics":     metrics,
    }


# ─── Run All Experiments ──────────────────────────────────────────────────────

def run_all_experiments(gen_mode="mock", groq_api_key=None):
    print("\n" + "=" * 60)
    print("  Constraint-Aware Generative Fitness & Nutrition System")
    print("=" * 60)

    # Load datasets
    df_nutrition = load_nutrition_data()
    df_exercise  = load_exercise_data()

    all_results  = []
    all_metrics  = []

    for profile in SAMPLE_PROFILES:
        result = run_pipeline(
            profile, df_nutrition, df_exercise,
            gen_mode=gen_mode, groq_api_key=groq_api_key,
            verbose=True
        )
        if result:
            all_results.append(result)
            all_metrics.append(result["metrics"])

    # Aggregate evaluation
    summary = evaluate_experiments(all_metrics)
    print_aggregate_summary(summary)

    # Save outputs
    os.makedirs("experiments", exist_ok=True)
    save_results_csv(all_metrics,      "experiments/results.csv")
    save_results_json(summary,         "experiments/summary.json")
    save_results_json(
        [{"profile": r["profile"]["name"], "plan": r["plan_text"]} for r in all_results],
        "experiments/generated_plans.json"
    )

    print("\n✅ All experiments complete. Results saved in experiments/")


# ─── Interactive Mode ─────────────────────────────────────────────────────────

def interactive_mode(gen_mode="mock", groq_api_key=None):
    print("\n" + "=" * 55)
    print("   AI Fitness Plan Generator — Interactive Mode")
    print("=" * 55)

    df_nutrition = load_nutrition_data()
    df_exercise  = load_exercise_data()

    profile = {}
    profile["name"]  = input("Enter your name           : ").strip() or "User"
    profile["age"]   = int(input("Enter your age            : "))
    profile["gender"]= input("Gender (male/female)      : ").strip().lower()
    profile["weight_kg"]   = float(input("Weight (kg)               : "))
    profile["height_cm"]   = float(input("Height (cm)               : "))

    print("Goals: fat_loss | muscle_gain | maintenance")
    profile["goal"] = input("Your goal                 : ").strip().lower()

    print("Diet: vegetarian | non-vegetarian")
    profile["diet_preference"] = input("Diet preference           : ").strip().lower()

    profile["workout_time_minutes"] = int(input("Available workout time (min): "))

    print("Activity: sedentary | light | moderate | active | very_active")
    profile["activity_level"] = input("Activity level            : ").strip().lower()

    run_pipeline(profile, df_nutrition, df_exercise,
                 gen_mode=gen_mode, groq_api_key=groq_api_key, verbose=True)


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fitness GenAI System")
    parser.add_argument("--mode",    default="mock",
                        choices=["mock", "groq", "huggingface"],
                        help="LLM generation mode")
    parser.add_argument("--groq-key", default=None,
                        help="Groq API key (for --mode groq)")
    parser.add_argument("--interactive", action="store_true",
                        help="Run in interactive mode")
    args = parser.parse_args()

    if args.interactive:
        interactive_mode(gen_mode=args.mode, groq_api_key=args.groq_key)
    else:
        run_all_experiments(gen_mode=args.mode, groq_api_key=args.groq_key)
