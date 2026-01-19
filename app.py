import streamlit as st
import pandas as pd
from datetime import date

# --- PAGE CONFIG ---
st.set_page_config(page_title="Espresso Wizard V6.0", page_icon="☕", layout="wide")

st.title("☕ Espresso Diagnostic Engine V6.0")
st.markdown("Optimization logic for **Breville Dual Boiler + Niche Zero**.")

# --- SESSION STATE ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("1. Bean Data")
    bean_name = st.text_input("Bean Name", "Onyx Geometry")
    roast_level = st.selectbox("Roast Level", ["Light", "Medium", "Dark"])
    
    know_date = st.checkbox("Know Roast Date?", value=True)
    if know_date:
        roast_date = st.date_input("Roast Date", date.today())
    else:
        roast_date = None
    
    st.markdown("---")
    st.caption("🔧 Calibration")
    use_manual_sens = st.checkbox("Override Sensitivity?")
    manual_sens = 1.0
    if use_manual_sens:
        manual_sens = st.slider("Sensitivity Factor", 0.5, 1.5, 1.0, 0.1)
    
    st.header("2. Shot Parameters")
    # NEW: Added Slayer-lite Option
    shot_style = st.selectbox("Shot Style", ["Normale (1:2)", "Ristretto (1:1.25)", "Lungo (1:3)", "Slayer-lite (Decaf)", "Custom"])
    
    # Defaults
    target_yield = 36.0
    target_time_min, target_time_max = 25, 30
    ratio = 2.0
    
    if shot_style == "Custom":
        target_yield = st.number_input("Target Yield (g)", value=36.0)
        target_time_min = st.number_input("Min Time (s)", value=25.0)
        target_time_max = st.number_input("Max Time (s)", value=30.0)
        target_center = (target_time_min + target_time_max) / 2
        ratio = 0
    elif shot_style == "Slayer-lite (Decaf)":
        # Slayer Defaults
        ratio = 2.0
        target_time_min, target_time_max = 35, 55 # Long shots common with profiling
        target_center = 45
    else:
        # Standard Styles
        if "Ristretto" in shot_style:
            ratio = 1.25
            target_time_min, target_time_max = 15, 20
        elif "Lungo" in shot_style:
            ratio = 3.0
            target_time_min, target_time_max = 35, 45
        else: # Normale
            ratio = 2.0
            target_time_min, target_time_max = 25, 30
        target_center = (target_time_min + target_time_max) / 2

    st.header("3. Shot Results")
    current_grind = st.number_input("Current Grind", value=15.0, step=0.5)
    current_dose = st.number_input("Dose In (g)", value=18.0, step=0.5)
    
    calc_target = current_dose * ratio if shot_style != "Custom" else target_yield
    st.caption(f"🎯 Target Yield: {calc_target}g")
    current_yield = st.number_input("Yield Out (g)", value=0.0, step=0.1)
    
    # CONDITIONAL INPUTS FOR SLAYER
    slayer_stream = False
    slayer_flow_dur = 0
    
    if shot_style == "Slayer-lite (Decaf)":
        st.markdown("🕵️ **Slayer Diagnostics**")
        slayer_stream = st.checkbox("Did stream form BEFORE full pressure ramp?", value=True)
        slayer_flow_dur = st.number_input("Duration of low-bar flow (sec)?", value=10, help="How long did it flow at 6-bar before pump ramped up?")
        current_time = st.number_input("Total Shot Time (s)", value=45.0, step=1.0)
    else:
        current_time = st.number_input("Time Total (s)", value=30.0, step=1.0)

    current_temp = st.number_input("Temp (°C)", value=93, min_value=86, max_value=96)
    
    col_pi1, col_pi2 = st.columns(2)
    with col_pi1:
        current_pi_power = st.number_input("PI Power/PPW (%)", value=65, min_value=50, max_value=99)
    with col_pi2:
        current_pi_time = st.number_input("PI Time/PrE (s)", value=7, step=1)
    
    st.header("4. Sensory Feedback")
    taste = st.selectbox("Taste Balance", ["Balanced", "Sour", "Bitter", "Harsh"])
    texture = st.selectbox("Texture", ["Syrupy", "Watery", "Dry", "Channeling"])
    
    st.markdown("---")
    if st.button("📝 Log This Shot"):
        record = {
            "Bean": bean_name,
            "Style": shot_style,
            "Grind": current_grind,
            "Dose": current_dose,
            "Yield": current_yield,
            "Time": current_time,
            "Temp": current_temp,
            "Taste": taste
        }
        st.session_state.history.append(record)
        st.success("Shot Logged!")

# --- LOGIC ENGINE (V6.0) ---

explanation_log = []
base_adj = 0.0
next_grind = current_grind
dose_adj = 0.0
next_target_yield = calc_target
temp_adj = 0
temp_msg = ""
pi_adj = 0
next_pi = current_pi_power

# 1. Bean Age
age_msg = ""
if know_date and roast_date:
    days_old = (date.today() - roast_date).days
    if days_old < 7:
        age_msg = f"⚠️ **Beans Fresh ({days_old}d).** Rest needed."
    elif days_old > 30:
        age_msg = f"⚠️ **Beans Aging ({days_old}d).** Expect faster flow."

# === BRANCH 1: SLAYER-LITE LOGIC ===
if shot_style == "Slayer-lite (Decaf)":
    
    # A. Machine Config Check
    if current_pi_power < 78 or current_pi_power > 82:
        explanation_log.append(f"• **Machine:** Slayer-lite requires PI Power ~80% to hit 6-bar. You are at {current_pi_power}%.")
        next_pi = 80 # Suggest fix
    
    if current_pi_time < 15:
        explanation_log.append(f"• **Machine:** PrE time is too short ({current_pi_time}s). Slayer-lite needs ~20s to allow for saturation + low-bar flow.")

    # B. Grind Logic (Rule A & B)
    if not slayer_stream:
        # Rule A: No stream before ramp -> Too Fine
        base_adj = +1.0 
        explanation_log.append("• **Grind:** No stream formed during low-pressure phase. Grind is **Too Fine** to permit 6-bar flow.")
    elif slayer_flow_dur < 3:
        # Rule B: Fast stream -> Too Coarse
        base_adj = -0.5
        explanation_log.append("• **Grind:** Low-pressure flow started too fast (<3s). Grind is **Too Coarse**.")
    else:
        explanation_log.append("• **Grind:** Low-pressure flow behavior is optimal.")

    final_grind_adj = base_adj # Sensitivity less relevant here, direct observation rules apply
    next_grind = current_grind + final_grind_adj

    # C. Ratio/Dose Logic (Rule D - Decaf Specific)
    if texture == "Watery": # "Thin"
        # Suggest Tighter Ratio (1:1.75)
        new_ratio_target = current_dose * 1.75
        next_target_yield = new_ratio_target
        explanation_log.append("• **Ratio:** Texture is Thin/Watery. For Decaf Slayer shots, tighten ratio to **1:1.75** to increase body.")
    
    # D. Temp Logic (Calibration Targets)
    # Dark: 91, Med: 93, Light: 94-95
    target_temp_cal = 93
    if roast_level == "Dark": target_temp_cal = 91
    if roast_level == "Light": target_temp_cal = 95
    
    if taste == "Bitter": # "Ashy"
        if current_temp > target_temp_cal:
            temp_adj = target_temp_cal - current_temp
            explanation_log.append(f"• **Temp:** Taste is Bitter/Ashy. For {roast_level} Decaf, reduce temp to **{target_temp_cal}°C**.")
    
    next_temp = current_temp + temp_adj

# === BRANCH 2: STANDARD LOGIC ===
else:
    # Standard Grind Logic
    lower_limit = target_time_min
    upper_limit = target_time_max
    
    if current_time >= lower_limit and current_time <= upper_limit:
        base_adj = 0.0
    elif current_time < (lower_limit - 8):
        base_adj = -2.0
    elif current_time < (lower_limit - 4):
        base_adj = -1.0
    elif current_time < lower_limit:
        base_adj = -0.5
    elif current_time > (upper_limit + 10):
        base_adj = +1.5
    elif current_time > (upper_limit + 5):
        base_adj = +1.0
    elif current_time > upper_limit:
        base_adj = +0.5

    sensitivity = manual_sens if use_manual_sens else (0.6 if roast_level == "Dark" else (0.8 if roast_level == "Medium" else 1.0))
    final_grind_adj = round((base_adj * sensitivity) * 2) / 2
    next_grind = current_grind + final_grind_adj
    
    if final_grind_adj != 0:
        explanation_log.append(f"• **Grind:** Adjusted based on time deviation from {lower_limit}-{upper_limit}s.")

    # Standard Dose Logic
    if texture == "Watery" and final_grind_adj == 0:
        dose_adj = +0.5
        explanation_log.append("• **Dose:** Time is perfect but texture is Watery. Increase mass (+0.5g).")

    # Standard Temp Logic
    min_temp, max_temp = 92, 96
    if roast_level == "Dark": min_temp, max_temp = 86, 91
    if roast_level == "Medium": min_temp, max_temp = 91, 94
    if roast_level == "Light": min_temp, max_temp = 93, 96
    
    # Decaf Check
    is_decaf = "Decaf" in bean_name or "decaf" in bean_name
    if is_decaf: max_temp = min(max_temp, 92)

    # Temp Adjustments
    if taste == "Sour":
        if current_temp < max_temp:
            temp_adj = +1
            explanation_log.append("• **Temp:** Sour -> Increase Temp +1°C.")
        else:
            base_yield = max(calc_target, current_yield)
            next_target_yield = base_yield + 2.0
            explanation_log.append(f"• **Ratio:** Max Temp reached. Extend shot (+2g) to fix sourness.")
    elif taste == "Bitter" and current_temp > min_temp:
        temp_adj = -1
        explanation_log.append("• **Temp:** Bitter -> Reduce Temp -1°C.")
        
    next_temp = current_temp + temp_adj


# --- SHARED OUTPUT DISPLAY ---
st.divider()
st.subheader("🔮 Wizard Diagnosis (V6.0)")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**👉 Next Grind:** `{next_grind}`")
    if next_grind != current_grind:
        st.caption(f"Adjustment: {next_grind - current_grind:+}")
    else:
        st.caption("Grind is Optimal")
    
    st.markdown("---")
    
    # DOSE / RATIO OUTPUT
    if dose_adj != 0:
        st.markdown(f"**⚖️ Next Dose:** `{current_dose + dose_adj}g`")
        st.warning("⚠️ Check Headroom.")
    elif next_target_yield != calc_target:
        st.markdown(f"**🎯 Next Target Yield:** `{round(next_target_yield, 1)}g`")
        if shot_style == "Slayer-lite (Decaf)":
            st.caption("Tightened Ratio (1:1.75) for Body")
        else:
            st.caption("Extended Ratio to fix Sourness")
    else:
        st.caption("Dose & Yield are Optimal")

with col2:
    if temp_msg:
        st.markdown(temp_msg)
    else:
        st.markdown(f"**🌡️ Next Temp:** `{next_temp}°C`")
        if temp_adj != 0: 
            st.caption(f"Adj: {temp_adj:+d}°C")
        else: 
            st.caption("Temp is Optimal")

    st.markdown("---")

    # PI OUTPUT
    if next_pi != current_pi_power:
        st.markdown(f"**💪 Next PI Power:** `{next_pi}%`")
        st.info("Adjust to hit 6-bar target")
    else:
        st.markdown(f"**💪 Next PI Power:** `{current_pi_power}%`")

st.divider()
if age_msg: st.warning(age_msg)
if texture == "Channeling": st.error("🛑 **Channeling Detected:** Fix WDT / Level Tamp.")

# Yield Warning
if current_yield > 0:
    yield_diff = abs(current_yield - calc_target)
    if yield_diff > max(3.0, calc_target * 0.1):
        st.error(f"⚖️ **Yield Miss:** Target {calc_target}g | Actual {current_yield}g")

# --- EXPLANATION SECTION ---
with st.expander("📝 Logic Analysis"):
    for log_item in explanation_log:
        st.markdown(log_item)

# --- HISTORY ---
if len(st.session_state.history) > 0:
    st.divider()
    st.subheader("📜 Session Log")
    st.dataframe(pd.DataFrame(st.session_state.history))
