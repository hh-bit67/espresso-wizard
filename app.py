import streamlit as st
from datetime import date
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="Espresso Wizard V5.7", page_icon="☕")

st.title("☕ Espresso Diagnostic Engine V5.7")
st.markdown("Optimization logic for **Breville Dual Boiler + Niche Zero**.")

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
    st.caption("🔧 Advanced Calibration")
    use_manual_sens = st.checkbox("Override Sensitivity?")
    manual_sens = 1.0
    if use_manual_sens:
        manual_sens = st.slider("Sensitivity Factor", 0.5, 1.5, 1.0, 0.1)
    
    st.header("2. Shot Parameters")
    shot_style = st.selectbox("Shot Style", ["Ristretto (1:1.25)", "Normale (1:2)", "Lungo (1:3)", "Custom"])
    
    if shot_style == "Custom":
        target_yield = st.number_input("Target Yield (g)", value=36.0)
        target_time_min = st.number_input("Min Time (s)", value=25.0)
        target_time_max = st.number_input("Max Time (s)", value=30.0)
        target_center = (target_time_min + target_time_max) / 2
        ratio = 0 
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
    
    calc_target = current_dose * ratio if shot_style != "Custom" else target_yield
    st.caption(f"🎯 Target Yield: {calc_target}g")
    current_yield = st.number_input("Yield Out (g)", value=0.0, step=0.1, help="Enter actual weight")
    
    current_time = st.number_input("Time Total (s)", value=30.0, step=1.0)
    current_temp = st.number_input("Temp (°C)", value=93, min_value=86, max_value=96)
    
    col_pi1, col_pi2 = st.columns(2)
    with col_pi1:
        current_pi_power = st.number_input("PI Power (%)", value=65, min_value=55, max_value=99)
    with col_pi2:
        current_pi_time = st.number_input("PI Time (s)", value=7, step=1)
    
    st.header("4. Sensory Feedback")
    taste = st.selectbox("Taste Balance", ["Balanced", "Sour", "Bitter", "Harsh"])
    texture = st.selectbox("Texture", ["Syrupy", "Watery", "Dry", "Channeling"])

# --- LOGIC ENGINE (V5.7) ---

explanation_log = []

# 1. Bean Age Logic
age_msg = ""
if know_date and roast_date:
    days_old = (date.today() - roast_date).days
    if days_old < 7:
        age_msg = f"⚠️ **Beans Fresh ({days_old}d).** Rest needed."
        explanation_log.append(f"• **Age:** Beans are very fresh (<7d). CO2 off-gassing causes resistance bubbles.")
    elif days_old > 30:
        age_msg = f"⚠️ **Beans Aging ({days_old}d).** Expect faster flow."
        explanation_log.append(f"• **Age:** Beans are aging (>30d). Staling reduces resistance, causing faster flow.")

# 2. Grind Logic
lower_limit = target_time_min
upper_limit = target_time_max

base_adj = 0.0
reason = ""

if current_time >= lower_limit and current_time <= upper_limit:
    base_adj = 0.0
    reason = "Time is within target window."
elif current_time < (lower_limit - 8):
    base_adj = -2.0
    reason = "Shot ran >8s fast (Gusher)."
elif current_time < (lower_limit - 4):
    base_adj = -1.0
    reason = "Shot ran >4s fast."
elif current_time < lower_limit:
    base_adj = -0.5
    reason = "Shot ran slightly fast."
elif current_time > (upper_limit + 10):
    base_adj = +1.5
    reason = "Shot choked (>10s slow)."
elif current_time > (upper_limit + 5):
    base_adj = +1.0
    reason = "Shot ran >5s slow."
elif current_time > upper_limit:
    base_adj = +0.5
    reason = "Shot ran slightly slow."

sensitivity = manual_sens if use_manual_sens else (0.6 if roast_level == "Dark" else (0.8 if roast_level == "Medium" else 1.0))
final_grind_adj = round((base_adj * sensitivity) * 2) / 2
next_grind = current_grind + final_grind_adj

if base_adj != 0:
    explanation_log.append(f"• **Grind:** {reason} Applied base adj ({base_adj}) x Sensitivity ({sensitivity}) = {final_grind_adj}.")
else:
    explanation_log.append("• **Grind:** Flow rate is optimal. No change needed.")

# 3. Dose Logic
dose_adj = 0.0
if texture == "Watery" and final_grind_adj == 0:
    dose_adj = +0.5
    explanation_log.append("• **Dose:** Time is perfect but texture is Watery. We suggest a small mass increase (+0.5g) to add resistance.")

# 4. Temp & Ratio Logic
min_temp, max_temp = 92, 96
if roast_level == "Dark": min_temp, max_temp = 86, 91
if roast_level == "Medium": min_temp, max_temp = 91, 94
if roast_level == "Light": min_temp, max_temp = 93, 96

is_decaf = "Decaf" in bean_name or "decaf" in bean_name
if is_decaf:
    max_temp = min(max_temp, 92)
    explanation_log.append("• **Temp:** Decaf detected. Safety cap applied (Max 92°C).")

temp_adj = 0
temp_msg = ""
next_target_yield = calc_target # Default next target is same as current
flow_fast = current_time < (target_time_min - 8)

if flow_fast:
    temp_msg = "⚠️ **Flow too fast.** Ignore Temp."
    explanation_log.append("• **Temp:** Skipped. Flow is erratic/fast; changing temp now would be inconsistent.")
elif taste == "Harsh":
    if roast_level == "Light":
        temp_msg = "⚠️ **Harshness (Light Roast):** Try Temp -1°C OR Check Prep."
        explanation_log.append("• **Temp:** Harshness in Light Roast can be over-extraction (Temp too high) or channeling.")
    else:
        temp_msg = "🛑 **Harshness Detected:** Check WDT/Distribution."
        explanation_log.append("• **Temp:** Harshness in Dark/Med roast indicates uneven extraction (Channeling).")
elif taste == "Sour":
    if current_temp < max_temp:
        temp_adj = +1
        explanation_log.append(f"• **Temp:** Sourness indicates under-extraction. Increasing Temp (+1°C) improves solubility.")
    else:
        # SOUR FALLBACK: INCREASE YIELD
        next_target_yield = calc_target + 2.0
        explanation_log.append(f"• **Ratio:** You are Sour but at Max Temp ({max_temp}°C). We must extend the shot (+2g yield) to extract more sweetness without burning the beans.")

elif taste == "Bitter" and current_temp > min_temp:
    temp_adj = -1
    explanation_log.append(f"• **Temp:** Bitterness indicates over-extraction. Reducing Temp (-1°C) reduces tannin solubility.")

next_temp = current_temp + temp_adj

# 5. PI Logic
pi_adj = 0
pi_time_msg = ""
if texture == "Channeling":
    pi_adj = -15 if is_decaf else -10
    explanation_log.append(f"• **PI Power:** Channeling detected. Reducing pressure ({pi_adj}%) helps preserve puck integrity.")
elif texture == "Watery":
    pi_adj = +5
    explanation_log.append("• **PI Power:** Shot is Watery. Increasing PI pressure (+5%) compresses the puck for more resistance.")
elif texture == "Dry":
    pi_time_msg = f"💧 **Dryness Detected:** Increase PI Time to {current_pi_time + 3}s (+3s)"
    explanation_log.append("• **PI Time:** Dry/Astringent finish often means uneven saturation. Longer Pre-Infusion (+3s) helps water penetrate evenly.")

next_pi = max(55, min(99, current_pi_power + pi_adj))

# --- OUTPUT DISPLAY ---
st.divider()
st.subheader("🔮 Wizard Diagnosis (V5.7)")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**👉 Next Grind:** `{next_grind}`")
    if final_grind_adj != 0:
        st.caption(f"Adj: {final_grind_adj} (Sens: {sensitivity}x)")
    else:
        st.caption("Grind is Optimal")
    
    # DOSE OUTPUT
    if dose_adj != 0:
        st.markdown(f"**⚖️ Next Dose:** `{current_dose + dose_adj}g`")
        st.caption("Increased +0.5g for Body")
        st.warning("⚠️ Check Headroom (Razor Tool).")
    elif next_target_yield != calc_target:
        st.markdown(f"**🎯 Next Target Yield:** `{round(next_target_yield, 1)}g`")
        st.caption(f"Previous Target: {round(calc_target, 1)}g")
        st.info("💡 Extend shot to fix Sourness")

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
if pi_time_msg: st.info(pi_time_msg
