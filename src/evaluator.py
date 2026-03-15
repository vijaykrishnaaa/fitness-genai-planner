"""
evaluator.py
-------------
Evaluation Layer.
Computes all quantitative metrics for the generated plans and
aggregates results across multiple test profiles.
"""

import json
import csv
import os
from datetime import datetime


# ─── Individual Metrics ───────────────────────────────────────────────────────

def compute_ccss(generated_kcal, target_kcal):
    """
    Calorie Constraint Satisfaction Score (CCSS)
    Formula: CCSS = 1 - |C_gen - C_target| / C_target
    Range: [0, 1]  — higher is better
    """
    if generated_kcal is None or target_kcal is None or target_kcal == 0:
        return None
    score = 1.0 - abs(generated_kcal - target_kcal) / target_kcal
    return round(max(0.0, score), 4)


def compute_par(generated_protein_g, min_protein_g):
    """
    Protein Adequacy Ratio (PAR)
    Formula: PAR = P_gen / P_min
    PAR >= 1.0 → adequate  |  PAR < 1.0 → deficient
    """
    if generated_protein_g is None or min_protein_g is None or min_protein_g == 0:
        return None
    return round(generated_protein_g / min_protein_g, 4)


def compute_wbs(balance_dict):
    """
    Workout Balance Score (WBS)
    Formula: WBS = number_of_covered_muscle_groups / total_required_groups
    Range: [0, 1]
    """
    if not balance_dict:
        return None
    covered = sum(1 for v in balance_dict.values() if v)
    return round(covered / len(balance_dict), 4)


def compute_overall_compliance_rate(ccss, par, wbs, diet_ok):
    """
    Overall Constraint Compliance Rate (CCR)
    Formula: CCR = (binary_ccss + binary_par + binary_wbs + binary_diet) / 4
    Each metric is binarized using its threshold.
    """
    components = []
    if ccss is not None:
        components.append(1 if ccss >= 0.85 else 0)
    if par is not None:
        components.append(1 if par >= 0.90 else 0)
    if wbs is not None:
        components.append(1 if wbs >= 0.75 else 0)
    if diet_ok is not None:
        components.append(1 if diet_ok else 0)
    if not components:
        return None
    return round(sum(components) / len(components), 4)


# ─── Single Profile Evaluation ────────────────────────────────────────────────

def evaluate_single(validation_report):
    """
    Extracts metrics from a validation report and computes evaluation scores.
    Returns a flat metrics dict.
    """
    cal_block  = validation_report["calorie"]
    prot_block = validation_report["protein"]
    wb_block   = validation_report["workout_balance"]
    diet_block = validation_report["diet_preference"]

    ccss = compute_ccss(cal_block["generated_kcal"], cal_block["target_kcal"])
    par  = compute_par(prot_block["generated_g"], prot_block["min_required_g"])
    wbs  = compute_wbs(wb_block["muscle_coverage"])
    diet_ok = diet_block["passed"]

    ccr = compute_overall_compliance_rate(ccss, par, wbs, diet_ok)

    return {
        "ccss":             ccss,
        "par":              par,
        "wbs":              wbs,
        "diet_ok":          diet_ok,
        "compliance_rate":  ccr,
        "timestamp":        datetime.now().isoformat(),
    }


# ─── Multi-Profile Evaluation ─────────────────────────────────────────────────

def evaluate_experiments(results_list):
    """
    Aggregates evaluation metrics across multiple experiment runs.
    results_list: list of dicts, each from evaluate_single().
    Returns an aggregated summary dict.
    """
    keys = ["ccss", "par", "wbs", "compliance_rate"]
    summary = {}

    for key in keys:
        vals = [r[key] for r in results_list if r.get(key) is not None]
        if vals:
            summary[f"avg_{key}"] = round(sum(vals) / len(vals), 4)
            summary[f"min_{key}"] = min(vals)
            summary[f"max_{key}"] = max(vals)
        else:
            summary[f"avg_{key}"] = None

    diet_ok_list = [r["diet_ok"] for r in results_list if r.get("diet_ok") is not None]
    summary["diet_ok_rate"] = round(sum(diet_ok_list) / len(diet_ok_list), 4) if diet_ok_list else None
    summary["num_profiles_tested"] = len(results_list)

    return summary


# ─── Save Results ─────────────────────────────────────────────────────────────

def save_results_csv(results_list, output_path):
    """Saves per-profile evaluation results to a CSV file."""
    if not results_list:
        return
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    keys = list(results_list[0].keys())
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results_list)
    print(f"[INFO] Results saved to: {output_path}")


def save_results_json(data, output_path):
    """Saves any dict/list to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[INFO] JSON saved to: {output_path}")


# ─── Pretty Print Evaluation ──────────────────────────────────────────────────

def print_evaluation_summary(metrics, profile_name=""):
    label = f" Profile: {profile_name} " if profile_name else ""
    print("\n" + "=" * 55)
    print(f"      EVALUATION METRICS{label}")
    print("=" * 55)
    print(f"  CCSS (Calorie Satisfaction) : {metrics['ccss']:.2%}" if metrics['ccss'] is not None else "  CCSS : N/A")
    print(f"  PAR  (Protein Adequacy)     : {metrics['par']:.2f}" if metrics['par'] is not None else "  PAR  : N/A")
    print(f"  WBS  (Workout Balance)      : {metrics['wbs']:.2%}" if metrics['wbs'] is not None else "  WBS  : N/A")
    print(f"  Diet Preference Satisfied   : {'✅ Yes' if metrics['diet_ok'] else '❌ No'}")
    print(f"  Overall Compliance Rate     : {metrics['compliance_rate']:.2%}" if metrics['compliance_rate'] is not None else "  CCR  : N/A")
    print("=" * 55 + "\n")


def print_aggregate_summary(summary):
    print("\n" + "=" * 55)
    print("     AGGREGATE EVALUATION SUMMARY")
    print("=" * 55)
    print(f"  Profiles Tested       : {summary['num_profiles_tested']}")
    for key in ["avg_ccss", "avg_par", "avg_wbs", "avg_compliance_rate"]:
        val = summary.get(key)
        print(f"  {key:<28}: {val:.4f}" if val is not None else f"  {key:<28}: N/A")
    rate = summary.get("diet_ok_rate")
    print(f"  diet_ok_rate          : {rate:.2%}" if rate is not None else "  diet_ok_rate          : N/A")
    print("=" * 55 + "\n")
