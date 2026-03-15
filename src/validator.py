"""
validator.py
-------------
Constraint Validation Layer.
Parses the generated plan text and validates it against the computed constraints.
Flags violations and computes per-constraint pass/fail status.
"""

import re


# ─── Calorie Parser ───────────────────────────────────────────────────────────

def parse_estimated_calories(plan_text):
    """
    Extracts the estimated TOTAL daily calorie value from the generated plan.
    Prioritizes summary/total lines over individual meal entries.
    Returns float or None.
    """
    # Priority 1: Look for explicit summary/total lines (most reliable)
    summary_patterns = [
        r"estimated daily calories[:\s~*]*([\d,]+(?:\.\d+)?)",
        r"total\s+calories[:\s~*]*([\d,]+(?:\.\d+)?)\s*kcal",
        r"total\s+calories[:\s~*]*([\d,]+(?:\.\d+)?)",
        r"daily\s+calories[:\s~*]*([\d,]+(?:\.\d+)?)",
    ]
    for pat in summary_patterns:
        match = re.search(pat, plan_text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))

    # Priority 2: Find all kcal mentions and prefer ones near summary context
    all_kcal = list(re.finditer(r"([\d,]+(?:\.\d+)?)\s*kcal", plan_text, re.IGNORECASE))
    if all_kcal:
        for m in all_kcal:
            start = max(0, m.start() - 60)
            context = plan_text[start:m.start()].lower()
            if any(kw in context for kw in ["total", "summary", "estimated", "daily"]):
                return float(m.group(1).replace(",", ""))
        # Fallback: use the LAST kcal value (usually the total in summary)
        return float(all_kcal[-1].group(1).replace(",", ""))

    return None


def parse_estimated_protein(plan_text):
    """
    Extracts the estimated TOTAL daily protein value from the generated plan.
    Prioritizes summary/total lines over individual meal entries.
    Returns float or None.
    """
    # Priority 1: Look for explicit summary/total lines
    summary_patterns = [
        r"estimated daily protein[:\s~*]*([\d,]+(?:\.\d+)?)\s*g",
        r"total\s+protein[:\s~*]*([\d,]+(?:\.\d+)?)\s*g",
        r"total\s+protein[:\s~*]*([\d,]+(?:\.\d+)?)",
        r"daily\s+protein[:\s~*]*([\d,]+(?:\.\d+)?)\s*g",
    ]
    for pat in summary_patterns:
        match = re.search(pat, plan_text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))

    # Priority 2: Look for protein values near summary context
    all_protein = list(re.finditer(r"([\d,]+(?:\.\d+)?)\s*g\s*(?:of\s+)?protein", plan_text, re.IGNORECASE))
    if not all_protein:
        all_protein = list(re.finditer(r"protein[:\s~]*([\d,]+(?:\.\d+)?)\s*g", plan_text, re.IGNORECASE))
    if all_protein:
        for m in all_protein:
            start = max(0, m.start() - 60)
            context = plan_text[start:m.start()].lower()
            if any(kw in context for kw in ["total", "summary", "estimated", "daily"]):
                return float(m.group(1).replace(",", ""))
        # Fallback: use the LAST protein value
        return float(all_protein[-1].group(1).replace(",", ""))

    return None


# ─── Calorie Constraint Satisfaction Score ────────────────────────────────────

def calorie_constraint_satisfaction_score(generated_calories, target_calories):
    """
    CCSS = 1 - |generated - target| / target
    Score of 1.0 = perfect adherence. Lower = larger deviation.
    Returns float in [0, 1].
    """
    if target_calories <= 0:
        return 0.0
    score = 1.0 - abs(generated_calories - target_calories) / target_calories
    return round(max(0.0, score), 4)


# ─── Protein Adequacy Ratio ───────────────────────────────────────────────────

def protein_adequacy_ratio(generated_protein, min_protein):
    """
    PAR = generated_protein / min_protein
    PAR >= 1.0 means the plan meets or exceeds minimum protein.
    Returns float.
    """
    if min_protein <= 0:
        return 1.0
    return round(generated_protein / min_protein, 4)


# ─── Workout Balance Checker ──────────────────────────────────────────────────

def check_workout_balance(plan_text, required_muscles):
    """
    Checks if each required muscle group appears at least once in the plan text.
    Returns a dict: {muscle: True/False}
    """
    balance = {}
    for muscle in required_muscles:
        # Check if any synonym of the muscle is mentioned
        synonyms = {
            "chest":     ["chest", "pectoral", "bench"],
            "back":      ["back", "lat", "row", "pulldown"],
            "legs":      ["leg", "squat", "lunge", "quad", "hamstring"],
            "shoulders": ["shoulder", "delt", "lateral raise"],
            "arms":      ["bicep", "tricep", "arm curl", "dip"],
            "core":      ["core", "plank", "crunch", "ab"],
            "cardio":    ["cardio", "run", "treadmill", "jump", "cycle"],
        }
        keys = synonyms.get(muscle.lower(), [muscle.lower()])
        found = any(k in plan_text.lower() for k in keys)
        balance[muscle] = found
    return balance


def workout_balance_score(balance_dict):
    """
    Fraction of required muscle groups that are present in the plan.
    Returns float in [0, 1].
    """
    if not balance_dict:
        return 1.0
    covered = sum(1 for v in balance_dict.values() if v)
    return round(covered / len(balance_dict), 4)


# ─── Diet Preference Check ────────────────────────────────────────────────────

def check_diet_preference(plan_text, diet_preference):
    """
    Checks if non-vegetarian items appear in a vegetarian plan.
    Returns (passed: bool, note: str)
    """
    veg_violations = ["chicken", "beef", "mutton", "pork", "fish", "salmon", "tuna",
                      "shrimp", "prawn", "egg"]  # egg is optional, kept as flag only
    if diet_preference.lower() == "vegetarian":
        for item in veg_violations:
            if item in plan_text.lower():
                return False, f"Non-vegetarian item detected: '{item}'"
    return True, "Diet preference satisfied"


# ─── Main Validation Function ─────────────────────────────────────────────────

def validate_plan(plan_text, constraints):
    """
    Runs all validation checks on the generated plan.
    Returns a structured validation report dict.
    """
    target_cal  = constraints["target_calories_kcal"]
    min_protein = constraints["min_protein_g"]
    muscles     = constraints["workout"]["muscle_groups"]
    diet_pref   = constraints["diet_preference"]

    # Parse generated values
    gen_cal  = parse_estimated_calories(plan_text)
    gen_prot = parse_estimated_protein(plan_text)

    # Calorie check
    if gen_cal is not None:
        ccss = calorie_constraint_satisfaction_score(gen_cal, target_cal)
        calorie_ok = ccss >= 0.85   # allow ±15% deviation
    else:
        gen_cal, ccss, calorie_ok = None, None, None

    # Protein check
    if gen_prot is not None:
        par = protein_adequacy_ratio(gen_prot, min_protein)
        protein_ok = par >= 0.90
    else:
        gen_prot, par, protein_ok = None, None, None

    # Workout balance check
    balance_dict  = check_workout_balance(plan_text, muscles)
    wbs           = workout_balance_score(balance_dict)
    balance_ok    = wbs >= 0.75

    # Diet preference check
    diet_ok, diet_note = check_diet_preference(plan_text, diet_pref)

    # Overall compliance
    checks = [calorie_ok, protein_ok, balance_ok, diet_ok]
    checks_bool = [c for c in checks if c is not None]
    overall_rate = round(sum(checks_bool) / len(checks_bool), 4) if checks_bool else 0

    report = {
        "calorie": {
            "target_kcal":    target_cal,
            "generated_kcal": gen_cal,
            "ccss":           ccss,
            "passed":         calorie_ok,
        },
        "protein": {
            "min_required_g": min_protein,
            "generated_g":    gen_prot,
            "par":            par,
            "passed":         protein_ok,
        },
        "workout_balance": {
            "muscle_coverage": balance_dict,
            "wbs":             wbs,
            "passed":          balance_ok,
        },
        "diet_preference": {
            "preference": diet_pref,
            "passed":     diet_ok,
            "note":       diet_note,
        },
        "overall_compliance_rate": overall_rate,
        "needs_regeneration": overall_rate < 0.75,
    }
    return report


# ─── Pretty Print Validation Report ──────────────────────────────────────────

def print_validation_report(report):
    print("\n" + "=" * 55)
    print("       CONSTRAINT VALIDATION REPORT")
    print("=" * 55)

    # Calories
    c = report["calorie"]
    cal_str = f"{c['generated_kcal']} kcal" if c['generated_kcal'] else "Not detected"
    ccss_str = f"{c['ccss']:.2%}" if c['ccss'] is not None else "N/A"
    print(f"\n[Calories]")
    print(f"  Target  : {c['target_kcal']} kcal")
    print(f"  Generated: {cal_str}")
    print(f"  CCSS    : {ccss_str}  {'✅' if c['passed'] else '❌' if c['passed'] is not None else '⚠️  (not parsed)'}")

    # Protein
    p = report["protein"]
    prot_str = f"{p['generated_g']} g" if p['generated_g'] else "Not detected"
    par_str  = f"{p['par']:.2f}" if p['par'] is not None else "N/A"
    print(f"\n[Protein]")
    print(f"  Minimum : {p['min_required_g']} g")
    print(f"  Generated: {prot_str}")
    print(f"  PAR     : {par_str}  {'✅' if p['passed'] else '❌' if p['passed'] is not None else '⚠️  (not parsed)'}")

    # Workout balance
    wb = report["workout_balance"]
    print(f"\n[Workout Balance]")
    for muscle, found in wb["muscle_coverage"].items():
        print(f"  {muscle.title():<12} : {'✅ Found' if found else '❌ Missing'}")
    print(f"  WBS     : {wb['wbs']:.2%}  {'✅' if wb['passed'] else '❌'}")

    # Diet preference
    dp = report["diet_preference"]
    print(f"\n[Diet Preference: {dp['preference'].title()}]")
    print(f"  Status  : {'✅ OK' if dp['passed'] else '❌ ' + dp['note']}")

    # Overall
    print(f"\n{'─'*55}")
    print(f"  Overall Compliance Rate : {report['overall_compliance_rate']:.2%}")
    if report["needs_regeneration"]:
        print("  ⚠️  Regeneration recommended (compliance < 75%)")
    else:
        print("  ✅ Plan meets constraint requirements")
    print("=" * 55 + "\n")
