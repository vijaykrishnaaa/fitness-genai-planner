# 01_Evolution_of_Workflow

This document outlines the development phases of the Constraint-Aware Fitness AI system, from initial data engineering to the final generative interface.

## Phase 1: Data Engineering
- **Objective**: Load and clean high-fidelity datasets.
- **Outcome**: `src/dataset_loader.py` successfully parses Kaggle datasets for FoodData Central (275K+ rows) and Gym Exercises (2.9K+ rows).

## Phase 2: Constraint Engineering
- **Objective**: Encode scientific biological logic.
- **Core Formulas**:
  - **BMR**: Mifflin-St Jeor Equation (using **10 × weight**)
  - **Protein Targets**: 
    - **Muscle Gain**: 2.2g/kg
    - **Fat Loss**: 2.0g/kg
    - **Maintenance**: 1.6g/kg
- **Module**: `src/constraint_engine.py`

## Phase 3: Generative Intelligence
- **Objective**: Integrate LLMs as reasoning engines.
- **Outcome**: `src/generator.py` bridges user data with LLaMA 3 (via Groq) and Mistral (via HuggingFace).

## Phase 4: Validation & Evaluation
- **Objective**: Solve the hallucination problem.
- **Outcome**: 
  - `src/validator.py`: Parses AI text back into raw numerical data.
  - `src/evaluator.py`: Computes 4 mathematical metrics (CCSS, PAR, WBS, CCR) to verify accuracy.

## Phase 5: Interface Development
- **Outcome**:
  - **CLI**: `main.py` for automated batch experiments.
  - **Web UI**: `app/app.py` for a premium, interactive user dashboard.
