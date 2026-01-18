import streamlit as st
from datetime import date
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="Espresso Wizard V5.4", page_icon="☕")

st.title("☕ Espresso Diagnostic Engine V5.4")
st.markdown("Optimization logic for **Breville Dual Boiler + Niche Zero**.")

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("1. Bean Data")
    bean_name = st.text_input("Bean Name", "Onyx Geometry")
    roast_level = st.selectbox("Roast Level", ["Light", "Medium", "Dark"])
    
    # NEW: Optional Roast Date
    know_date = st.checkbox("Know Roast Date?", value=True)
    if know_date:
        roast_date = st.date_input("Roast Date", date.today())
    else:
        roast_date = None
    
    # Sensitivity Override
    st.markdown("---")
    st.caption("🔧 Advanced Calibration")
    use_manual_sens = st.checkbox("Override Sensitivity?")
    manual_sens = 1.0
    if use_manual_sens:
        manual_sens = st.slider("Sensitivity Factor", 0.5, 1.5, 1.0, 0.1)
    
    st.header("2. Shot Parameters")
    shot_style = st.selectbox("Shot Style", ["Ristretto (1:1.25)", "Normale (1:2)", "Lungo (1:3)", "Custom"])
    
    # Calculate Targets
    if shot_style == "Custom":
        target_yield = st.number_input("Target Yield (g)", value=36.0)
        target_time_min = st.number_input("Min Time (s)", value=25.0)
        target_time_max = st.number_input("Max Time (s)", value=30.0)
        target_center = (target_time_min + target_time_max) / 2
        ratio = 0 # Not used in custom
    else:
        if "Ristretto" in shot_style:
            ratio = 1.25
            target_time_min, target_time_max = 15, 20
        elif "Lungo" in shot_style:
            ratio = 3.0
            target_time_min, target_time_max = 35, 45
        else: # Normale
            ratio = 2.0
            target_time_min, target_time_max = 25, 30
        target_center = 27.5 if "Normale" in shot_style else (17.5 if "Ristretto" in shot_style else 40)

    st.header("3. Shot Results")
    current_grind = st.number_input("Current Grind", value=15.0, step=0.5)
    current_dose = st.number_input("Dose In (g)", value=18.0, step=0.5)
    
    # NEW: Decoupled Yield Input
    # We calculate the target for display, but don't force it into the input box
    calc_target = current_dose * ratio if shot_style != "Custom" else target_yield
    st.caption(f"🎯 Target Yield: {calc_target}g")
    current_yield = st.number_input("Yield Out (g)", value=0.0, step=0.1, help="Enter the actual weight in the cup")
    
    current_time = st.number_input("Time Total (s)", value=30.0, step=1.0)
    current_temp = st.number_input("Temp (°C)", value=93, min_value=86, max_value=96)
    
    col_pi1, col_pi2 = st.columns(2)
    with col_pi1:
        current_pi_power = st.number_input("PI Power (%)", value=65, min_value=55, max_value=99)
    with col_pi2:
        # NEW: PI Time Input
        current_pi_time = st.number_input("PI Time (s)", value=7, step=1)
    
    st.header("4. Sensory Feedback")
    taste = st.selectbox("Taste Balance", ["Balanced", "Sour", "Bitter", "Harsh"])
    texture = st.selectbox("Texture", ["Syrupy", "Watery", "Dry", "Channeling"])

# --- LOGIC ENGINE (V5.4) ---

# 1. Bean Age Logic (Nullable)
age_msg = ""
if know_date and roast_date:
    days_old = (date.today() - roast_date).days
    if days_old < 7:
        age_msg = f"⚠️ **Beans Fresh ({days_old}d).** Rest needed."
    elif days_old > 30:
        age_msg = f"⚠️ **Beans Aging ({days_old}d).** Expect faster flow."

# 2. Grind Logic
lower_limit = target_time_min
upper_limit = target_time_max

base_adj = 0.0
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

# 3. Dose Logic
dose_adj = 0.0
if texture == "Watery" and final_grind_adj == 0:
    dose_adj = +1.0

# 4. Temp Logic
min_temp, max_temp = 92, 96
if roast_level == "Dark": min_temp, max_temp = 86, 91
if roast_level == "Medium": min_temp, max_temp = 91, 94
if roast_level == "Light": min_temp, max_temp = 93, 96

is_decaf = "Decaf" in bean_name or "decaf" in bean_name
if is_decaf:
    max_temp = min(max_temp, 92)

temp_adj = 0
temp_msg = ""
flow_fast = current_time < (target_time_min - 8)

if flow_fast:
    temp_msg = "⚠️ **Flow too fast.** Ignore Temp."
elif taste == "Harsh":
    if roast_level == "Light":
        temp_msg = "⚠️ **Harshness (Light Roast):** Try Temp -1°C OR Check Prep."
    else:
        temp_msg = "🛑 **Harshness Detected:** Check WDT/Distribution."
elif taste == "Sour" and current_temp < max_temp:
    temp_adj = +1
elif taste == "Bitter" and current_temp > min_temp:
    temp_adj = -1

next_temp = current_temp + temp_adj

# 5. PI Logic
pi_adj = 0
pi_time_msg = ""
if texture == "Channeling":
    pi_adj = -15 if is_decaf else -10
elif texture == "Watery":
    pi_adj = +5
elif texture == "Dry":
    # NEW: Explicit PI Time instruction
    pi_time_msg = f"💧 **Dryness Detected:** Increase PI Time to {current_pi_time + 3}s (+3s)"

next_pi = max(55, min(99, current_pi_power + pi_adj))

# --- OUTPUT DISPLAY ---
st.divider()
st.subheader("🔮 Wizard Diagnosis (V5.4)")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**👉 Next Grind:** `{next_grind}`")
    if final_grind_adj != 0:
        st.caption(f"Adj: {final_grind_adj} (Sens: {sensitivity}x)")
    else:
        st.caption("Grind is Optimal")
    
    if dose_adj != 0:
        st.markdown(f"**⚖️ Next Dose:** `{current_dose + dose_adj}g`")
        st.caption("Increased +1.0g for Body")

with col2:
    if temp_msg:
        st.markdown(temp_msg)
    else:
        st.markdown(f"**🌡️ Next Temp:** `{next_temp}°C`")
        if temp_adj != 0: 
            st.caption(f"Adj: {temp_adj:+d}°C")
            st.warning("⚠️ Change may affect flow.")
        else: 
            st.caption("Temp is Optimal")

    if pi_adj != 0:
        st.markdown(f"**💪 Next PI Power:** `{next_pi}%`")
    else:
        st.markdown(f"**💪 Next PI Power:** `{current_pi_power}%`")

st.divider()

if age_msg: st.warning(age_msg)
if pi_time_msg: st.info(pi_time_msg)

# Yield Warning
yield_diff = abs(current_yield - calc_target)
tolerance = max(3.0, calc_target * 0.1)

if current_yield > 0 and yield_diff > tolerance:
    st.error(f"⚖️ **Yield Warning:** Target {calc_target}g | Actual {current_yield}g")

if is_decaf and flow_fast:
    st.info("☕ **Decaf Tip:** Structure is weak. Consider Dosing +0.5g up.")
