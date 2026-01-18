import streamlit as st
from datetime import date
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="Espresso Wizard V5.1", page_icon="☕")

st.title("☕ Espresso Diagnostic Engine V5.1")
st.markdown("Optimization logic for **Breville Dual Boiler + Niche Zero**.")

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("1. Bean Data")
    bean_name = st.text_input("Bean Name", "Onyx Geometry")
    roast_level = st.selectbox("Roast Level", ["Light", "Medium", "Dark"])
    roast_date = st.date_input("Roast Date", date.today())
    
    st.header("2. Shot Parameters")
    shot_style = st.selectbox("Shot Style", ["Ristretto (1:1.25)", "Normale (1:2)", "Lungo (1:3)", "Custom"])
    
    if shot_style == "Custom":
        target_yield = st.number_input("Target Yield (g)", value=36.0)
        target_time_min = st.number_input("Min Time (s)", value=25.0)
        target_time_max = st.number_input("Max Time (s)", value=30.0)
        target_center = (target_time_min + target_time_max) / 2
    else:
        # Auto-calculate targets based on V5.1 Logic
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
    
    # Auto-fill yield based on style to save typing
    default_yield = current_dose * (ratio if shot_style != "Custom" else 2.0)
    current_yield = st.number_input("Yield Out (g)", value=default_yield, step=0.1)
    
    current_time = st.number_input("Time Total (s)", value=30.0, step=1.0)
    current_temp = st.number_input("Temp (°C)", value=93, min_value=86, max_value=96)
    current_pi_power = st.number_input("PI Power (%)", value=65, min_value=55, max_value=99)
    
    st.header("4. Sensory Feedback")
    taste = st.selectbox("Taste Balance", ["Balanced", "Sour", "Bitter", "Harsh"])
    texture = st.selectbox("Texture", ["Syrupy", "Watery", "Dry", "Channeling"])

# --- LOGIC ENGINE (V5.1) ---

# 1. Bean Age Logic
days_old = (date.today() - roast_date).days
age_msg = ""
if days_old < 7:
    age_msg = f"⚠️ **Beans Fresh ({days_old}d).** Rest needed."
elif days_old > 45:
    age_msg = f"⚠️ **Beans Stale ({days_old}d).** Expect fast flow."

# 2. Grind Logic (Sensitivity Factor)
delta_time = current_time - target_center # Unused but good for debug
# Determine Limits based on style
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

# Apply Sensitivity Multiplier
sensitivity = 1.0
if roast_level == "Dark": sensitivity = 0.6
if roast_level == "Medium": sensitivity = 0.8

# Round to nearest 0.5
final_grind_adj = round((base_adj * sensitivity) * 2) / 2
next_grind = current_grind + final_grind_adj

# 3. Dose Logic (Vectoring)
dose_adj = 0.0
if texture == "Watery" and final_grind_adj == 0:
    dose_adj = +0.5
if texture == "Channeling" and "Decaf" in bean_name:
    # Decaf channeling handled in PI, but maybe check dose? 
    # V5.1 paper strictly mentions PI for channeling, so we skip dose here unless needed.
    pass

# 4. Temp Logic (Hardware Clamped)
# Limits: Dark (86-91), Medium (91-94), Light (93-96)
min_temp, max_temp = 92, 96
if roast_level == "Dark": min_temp, max_temp = 86, 91
if roast_level == "Medium": min_temp, max_temp = 91, 94
if roast_level == "Light": min_temp, max_temp = 93, 96

temp_adj = 0
temp_msg = ""
flow_fast = current_time < (target_time_min - 8)

if flow_fast:
    temp_msg = "⚠️ **Flow too fast.** Ignore Temp."
elif taste == "Harsh":
    temp_msg = "🛑 **Harshness Detected.** Check WDT/Distribution."
elif taste == "Sour" and current_temp < max_temp:
    temp_adj = +1
elif taste == "Bitter" and current_temp > min_temp:
    temp_adj = -1

next_temp = current_temp + temp_adj

# 5. PI Logic
pi_adj = 0
is_decaf = "Decaf" in bean_name or "decaf" in bean_name
if texture == "Channeling":
    pi_adj = -15 if is_decaf else -10
elif texture == "Watery":
    pi_adj = +5

next_pi = max(55, min(99, current_pi_power + pi_adj))

# --- OUTPUT DISPLAY ---
st.divider()
st.subheader("🔮 Wizard Diagnosis")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**👉 Next Grind:** `{next_grind}`")
    if final_grind_adj != 0:
        st.caption(f"Adjustment: {final_grind_adj} (Sensitivity: {sensitivity}x)")
    else:
        st.caption("Grind is Optimal")
    
    if dose_adj != 0:
        st.markdown(f"**⚖️ Next Dose:** `{current_dose + dose_adj}g`")
        st.caption("Increase to fix Watery texture")

with col2:
    if temp_msg:
        st.markdown(temp_msg)
    else:
        st.markdown(f"**🌡️ Next Temp:** `{next_temp}°C`")
        if temp_adj != 0: st.caption(f"Adj: {temp_adj:+d}°C")
        else: st.caption("Temp is Optimal")

    if pi_adj != 0:
        st.markdown(f"**💪 Next PI Power:** `{next_pi}%`")
    else:
        st.markdown(f"**💪 Next PI Power:** `{current_pi_power}%` (No Change)")

st.divider()

# Warnings
if age_msg: st.warning(age_msg)
if texture == "Dry": st.info("💧 **Dryness Detected:** Increase Pre-Infusion Time +3s")
if abs(current_yield - (current_dose * ratio if shot_style != "Custom" else target_yield)) > 3:
    st.error(f"⚖️ **Yield Warning:** You missed target by {round(abs(current_yield - (current_dose * ratio if shot_style != 'Custom' else target_yield)),1)}g")
if is_decaf and flow_fast:
    st.info("☕ **Decaf Tip:** Structure is weak. Consider Dosing +0.5g up.")

