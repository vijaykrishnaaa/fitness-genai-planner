"""
prepare_data.py
---------------
Merges the FoodData Central relational CSV files (from Kaggle) into
a single flat nutrition_dataset.csv that dataset_loader.py expects.

Usage:
    python prepare_data.py

It reads from ~/Downloads/archive/ and writes to data/nutrition_dataset.csv
"""

import pandas as pd
import os

# ─── Paths ─────────────────────────────────────────────────────────────────────
ARCHIVE_DIR = os.path.expanduser("~/Downloads/archive")
OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), "data")

# Input files from the Kaggle download
FOOD_FILE     = os.path.join(ARCHIVE_DIR, "food.csv")
NUTRIENT_FILE = os.path.join(ARCHIVE_DIR, "food_nutrient.csv")
NUTRIENT_DEF  = os.path.join(ARCHIVE_DIR, "nutrient.csv")

# Nutrient IDs we need
NUTRIENT_IDS = {
    1008: "calories",    # Energy (KCAL)
    1003: "protein",     # Protein (G)
    1005: "carbs",       # Carbohydrate, by difference (G)
    1004: "fat",         # Total lipid / fat (G)
}

def main():
    # ── Check files exist ───────────────────────────────────────────────────
    for path, label in [(FOOD_FILE, "food.csv"),
                        (NUTRIENT_FILE, "food_nutrient.csv"),
                        (NUTRIENT_DEF, "nutrient.csv")]:
        if not os.path.exists(path):
            print(f"[ERROR] {label} not found at: {path}")
            print(f"        Make sure the Kaggle archive is extracted in ~/Downloads/archive/")
            return

    # ── Load ────────────────────────────────────────────────────────────────
    print("[1/5] Loading food.csv ...")
    df_food = pd.read_csv(FOOD_FILE, usecols=["fdc_id", "description"])
    print(f"       → {len(df_food)} food entries")

    print("[2/5] Loading food_nutrient.csv (this may take a moment) ...")
    df_fn = pd.read_csv(NUTRIENT_FILE, usecols=["fdc_id", "nutrient_id", "amount"])
    print(f"       → {len(df_fn)} nutrient records")

    # ── Filter only the 4 nutrients we care about ───────────────────────────
    print("[3/5] Filtering nutrients (calories, protein, carbs, fat) ...")
    df_fn = df_fn[df_fn["nutrient_id"].isin(NUTRIENT_IDS.keys())].copy()
    df_fn["nutrient_name"] = df_fn["nutrient_id"].map(NUTRIENT_IDS)
    print(f"       → {len(df_fn)} relevant records")

    # ── Pivot: one row per food, columns = calories/protein/carbs/fat ──────
    print("[4/5] Pivoting into flat table ...")
    df_pivot = df_fn.pivot_table(
        index="fdc_id",
        columns="nutrient_name",
        values="amount",
        aggfunc="first"
    ).reset_index()

    # ── Merge with food names ───────────────────────────────────────────────
    df_merged = df_food.merge(df_pivot, on="fdc_id", how="inner")
    df_merged = df_merged.rename(columns={"description": "name"})
    df_merged = df_merged[["name", "calories", "protein", "carbs", "fat"]]
    df_merged = df_merged.dropna(subset=["calories"])
    df_merged = df_merged.drop_duplicates(subset=["name"])
    df_merged = df_merged.sort_values("name").reset_index(drop=True)

    # ── Save ────────────────────────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "nutrition_dataset.csv")
    df_merged.to_csv(out_path, index=False)
    print(f"[5/5] Saved {len(df_merged)} entries → {out_path}")
    print()
    print("Sample rows:")
    print(df_merged.head(10).to_string(index=False))
    print()
    print("✅ nutrition_dataset.csv is ready!")


if __name__ == "__main__":
    main()
