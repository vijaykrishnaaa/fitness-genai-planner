# Project Details: Constraint-Aware Fitness & Nutrition GenAI

This document provides a technical overview of the system architecture, core logic, and technical stack.

---

### 1️⃣ How are you generating the fitness plan?
The system uses **Controlled Generation** through a structured prompt-engineering layer. It supports three execution modes:
- **`mode: mock`** (Default): Uses a template-based plan for zero-dependency testing.
- **`mode: groq`**: Connects to the **Groq Cloud API** using the **Meta LLaMA 3 8B** model for high-speed generation.
- **`mode: huggingface`**: Uses a local **Mistral-7B-Instruct** model via the Transformers library.

### 2️⃣ Are you using a local LLM or API?
The project is built to be **hybrid**:
- **API-based** via **Groq** (best for speed and quality).
- **Local-only** via **HuggingFace** (best for privacy and offline use).
- **Hardcoded Fallback** for development without any model connectivity.

### 3️⃣ What libraries are you using?
The technical stack is built on Python 3.12:
- **`pandas`**: High-performance data processing for food (275K rows) and exercise (2.9K rows) datasets.
- **`streamlit`**: Interactive web interface with real-time plan visualization.
- **`groq`**: Lightweight client for LLaMA 3 API integration.
- **`transformers` & `torch`**: Support for local Mistral / LLaMA model inference.
- **`argparse`**: Core CLI infrastructure in `main.py`.

### 4️⃣ Do you have a UI?
Yes, the system is **dual-interface**:
1. **Web UI**: Run `streamlit run app/app.py` for a modern, slider-based dashboard.
2. **CLI**: Run `python main.py` for automated experiments or `python main.py --interactive` for a text-based wizard.

### 5️⃣ What files exist in your project?
The project follows a **Modular Layered Architecture**:
- `src/dataset_loader.py`: Handles CSV parsing and cleaning.
- `src/constraint_engine.py`: Encapsulates the core math (BMR, TDEE, Protein targets).
- `src/generator.py`: Bridges the data layer with the LLM.
- `src/validator.py`: Parses LLM output into structured data for checking.
- `src/evaluator.py`: Computes 4 unique metrics (CCSS, PAR, WBS, CCR).
- `app/app.py`: Streamlit frontend.
- `main.py`: Main entry point and experiment runner.
- `prepare_data.py`: Helper script to merge Kaggle FoodData datasets.

### 6️⃣ How do you calculate calories or constraints?
The system uses medical-standard formulas:
- **Basal Metabolic Rate (BMR)**: Mifflin-St Jeor Equation.
- **Total Daily Energy Expenditure (TDEE)**: BMR × Activity Multiplier (1.2 to 1.9).
- **Target Calories**: TDEE modified by Goal (Gain: +300, Loss: -500, Maintain: 0).
- **Protein Targets**: 
  - Fat Loss: 2.0g per kg
  - Muscle Gain: 2.2g per kg
  - Maintenance: 1.6g per kg

### 7️⃣ What output does your system generate?
Each generation results in a complete **Constraint-Verified Plan**:
- **7-Day Workout Schedule**: Specific exercises mapped to muscle groups (Chest, Back, Legs, etc.) based on available gym equipment.
- **Daily Diet Plan**: Breakdown of Breakfast, Lunch, Dinner, and Snacks matching dietary preferences (Veg/Non-Veg).
- **Quantitative Summary**:
  - Estimated Daily Calories (Kcal)
  - Estimated Daily Protein (G)
  - Validation metrics (passing/failing thresholds)
