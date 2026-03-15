"""
app/app.py
-----------
Streamlit Web Interface for the Constraint-Aware Generative Fitness & Nutrition System.
Run with: streamlit run app/app.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
from dataset_loader    import load_nutrition_data, load_exercise_data, get_exercises_by_muscle
from constraint_engine import build_constraints, validate_inputs
from generator         import generate_plan
from validator         import validate_plan
from evaluator         import evaluate_single

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Fitness Planner",
    page_icon="💪",
    layout="wide",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background-color: #FAF8F5;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hero Section */
    .hero-container {
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #1B7A5A 0%, #12543E 100%);
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(27, 122, 90, 0.2);
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 400;
    }

    /* Cards */
    .how-it-works-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #E0DCD8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        transition: transform 0.2s ease;
        height: 100%;
    }
    .how-it-works-card:hover {
        transform: translateY(-5px);
        border-color: #1B7A5A;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #F0EDE8;
        border-right: 1px solid #E0DCD8;
    }
    .sidebar-header {
        font-weight: 700;
        color: #1B7A5A;
        font-size: 1.1rem;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        border-bottom: 2px solid #E0DCD8;
        padding-bottom: 5px;
    }

    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1B7A5A;
    }
    
    /* Button enhancement */
    div.stButton > button {
        background-color: #1B7A5A !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        background-color: #12543E !important;
        box-shadow: 0 5px 15px rgba(27, 122, 90, 0.4) !important;
        transform: scale(1.02);
    }

    /* Plan Container */
    .plan-box {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #E0DCD8;
        line-height: 1.6;
    }
    
    /* Custom Info Box */
    .custom-info {
        background-color: #E7F3EF;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1B7A5A;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ─── Hero Section ────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-title">💪 AI Fitness Planner</div>
    <div class="hero-subtitle">
        Your hand-crafted personal journey to a healthier lifestyle, 
        powered by constraint-aware intelligence.
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Load Datasets ────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    return load_nutrition_data(), load_exercise_data()

df_nutrition, df_exercise = load_data()

# ─── Sidebar — User Input ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-header">🧑 User Profile</div>', unsafe_allow_html=True)

    name   = st.text_input("Name", value="Vijay")
    age    = st.slider("Age", 15, 70, 22)
    gender = st.selectbox("Gender", ["male", "female"])
    weight = st.slider("Weight (kg)", 40, 150, 70)
    height = st.slider("Height (cm)", 140, 210, 170)

    st.markdown('<div class="sidebar-header">🎯 Fitness Settings</div>', unsafe_allow_html=True)
    goal = st.selectbox("Goal", ["fat_loss", "muscle_gain", "maintenance"],
                        format_func=lambda x: x.replace("_", " ").title())
    diet = st.selectbox("Diet Preference", ["vegetarian", "non-vegetarian"])
    workout_time = st.slider("Workout Time (min/session)", 20, 90, 45)
    activity = st.selectbox("Activity Level",
                            ["sedentary", "light", "moderate", "active", "very_active"],
                            index=2)

    st.markdown('<div class="sidebar-header">⚙️ Generator Settings</div>', unsafe_allow_html=True)
    gen_mode = st.selectbox("Generation Mode",
                            ["mock", "groq"],
                            help="'mock' = demo output. 'groq' = real LLM (free API key needed).")
    groq_key = ""
    if gen_mode == "groq":
        groq_key = st.text_input("Groq API Key", type="password",
                                  help="Get free key at console.groq.com")

    generate_btn = st.button("🚀 Generate My Plan", type="primary", use_container_width=True)

# ─── Main Content ─────────────────────────────────────────────────────────────
if generate_btn:
    user_profile = {
        "name": name, "age": age, "gender": gender,
        "weight_kg": weight, "height_cm": height,
        "goal": goal, "diet_preference": diet,
        "workout_time_minutes": workout_time,
        "activity_level": activity,
    }

    # Validate
    ok, msg = validate_inputs(user_profile)
    if not ok:
        st.error(f"❌ Input Error: {msg}")
        st.stop()

    # Compute constraints
    with st.spinner("Computing constraints..."):
        constraints = build_constraints(user_profile)

    # Exercise suggestions
    exercise_suggestions = {}
    for muscle in constraints["workout"]["muscle_groups"]:
        exercise_suggestions[muscle] = get_exercises_by_muscle(df_exercise, muscle)[:5]

    # Generate plan
    with st.spinner("Generating your personalized plan with AI..."):
        try:
            prompt, plan_text = generate_plan(
                user_profile, constraints, exercise_suggestions,
                mode=gen_mode, groq_api_key=groq_key if groq_key else None
            )
        except Exception as e:
            st.error(f"Generation error: {e}")
            st.stop()

    # Validate
    val_report = validate_plan(plan_text, constraints)
    metrics    = evaluate_single(val_report)

    # ── Display ────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📋 Generated Plan", "✅ Validation", "📊 Metrics"])

    with tab1:
        st.markdown(f'<div class="sidebar-header">📋 Personalized Plan for {name}</div>', unsafe_allow_html=True)
        st.markdown('<div class="plan-box">', unsafe_allow_html=True)
        st.markdown(plan_text)
        st.markdown('</div>', unsafe_allow_html=True)

        st.download_button(
            label="⬇️ Download Plan as Text",
            data=plan_text,
            file_name=f"fitness_plan_{name.lower()}.txt",
            mime="text/plain",
        )

    with tab2:
        st.subheader("Constraint Validation Results")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Target Calories",    f"{constraints['target_calories_kcal']} kcal")
            st.metric("Min Protein Target", f"{constraints['min_protein_g']} g")

        with col2:
            cal_data = val_report["calorie"]
            gen_cal  = cal_data.get("generated_kcal")
            st.metric("Generated Calories",
                      f"{gen_cal} kcal" if gen_cal else "Not detected",
                      delta=f"{gen_cal - constraints['target_calories_kcal']:.0f}" if gen_cal else None)

        st.subheader("Workout Balance")
        balance = val_report["workout_balance"]["muscle_coverage"]
        cols = st.columns(len(balance))
        for i, (muscle, found) in enumerate(balance.items()):
            with cols[i]:
                st.metric(muscle.title(), "✅" if found else "❌")

        st.subheader("Diet Preference")
        dp = val_report["diet_preference"]
        if dp["passed"]:
            st.success(f"✅ {dp['preference'].title()} preference satisfied")
        else:
            st.warning(f"⚠️ {dp['note']}")

    with tab3:
        st.subheader("Quantitative Evaluation Metrics")

        col1, col2, col3, col4 = st.columns(4)

        ccss = metrics.get("ccss")
        par  = metrics.get("par")
        wbs  = metrics.get("wbs")
        ccr  = metrics.get("compliance_rate")

        with col1:
            st.metric("CCSS", f"{ccss:.2%}" if ccss is not None else "N/A",
                      help="Calorie Constraint Satisfaction Score. Higher = better calorie adherence.")
        with col2:
            st.metric("PAR", f"{par:.2f}" if par is not None else "N/A",
                      help="Protein Adequacy Ratio. ≥1.0 = adequate protein.")
        with col3:
            st.metric("WBS", f"{wbs:.2%}" if wbs is not None else "N/A",
                      help="Workout Balance Score. Higher = better muscle group coverage.")
        with col4:
            st.metric("Overall Compliance", f"{ccr:.2%}" if ccr is not None else "N/A",
                      help="Overall Constraint Compliance Rate.")

        if val_report["needs_regeneration"]:
            st.warning("⚠️ Compliance below 75%. Consider regenerating.")
        else:
            st.success("✅ Plan meets all constraint requirements.")

        st.subheader("Metric Explanations")
        st.info("""
**CCSS (Calorie Constraint Satisfaction Score)**
Formula: `1 - |C_generated - C_target| / C_target`
Measures how closely generated calories match the target.

**PAR (Protein Adequacy Ratio)**
Formula: `P_generated / P_minimum`
Values ≥ 1.0 indicate sufficient protein intake.

**WBS (Workout Balance Score)**
Formula: `covered_muscle_groups / required_muscle_groups`
Measures completeness of muscle group coverage.

**CCR (Constraint Compliance Rate)**
Average of all binary pass/fail constraint checks.
        """)

else:
    st.markdown("""
    <div class="custom-info">
        👈 <b>Get Started:</b> Fill in your profile in the sidebar and click <b>Generate My Plan</b> to begin your personal wellness journey.
    </div>
    """, unsafe_allow_html=True)

    st.subheader("How it works")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="how-it-works-card">
            <h3>1️⃣ Input</h3>
            <p>Enter your age, weight, goal, diet and available workout time in the sidebar.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="how-it-works-card">
            <h3>2️⃣ Generate</h3>
            <p>The AI generates a personalized 7-day workout and daily diet plan tailored to you.</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="how-it-works-card">
            <h3>3️⃣ Validate</h3>
            <p>The plan is checked against calorie, protein and workout constraints for safety.</p>
        </div>
        """, unsafe_allow_html=True)
