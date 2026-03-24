import streamlit as st
import time
from vision_model import analyze_image_url

st.set_page_config(page_title="Hype vs Hardware", page_icon="🏢", layout="centered")

# --- SECURE SETTINGS & API VAULT ---
# First, try to grab the key securely from Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    # If the secret isn't found, fallback to asking the user
    with st.sidebar:
        st.header("⚙️ Engine Settings")
        api_key = st.text_input("Google Gemini API Key:", type="password")
        st.markdown("*Required to run the AI Vision model.*")

# --- MAIN DASHBOARD ---
st.title("🏢 Hype vs. Hardware")
st.subheader("The Institutional-Grade BS Detector for Property Investors")
st.markdown("---")

property_url = st.text_input("Paste a Domain.com.au Property URL:")

# The Micro-Premium Toggles
with st.expander("Optional: Add Micro-Premiums"):
    north_facing = st.checkbox("North/North-East Facing Rear (+5% Land Value)")
    flat_block = st.checkbox("Perfectly Flat Block (+0% to +5%)")
    bad_position = st.checkbox("T-Intersection or Bad Street Position (-10%)")

# The Action Button
if st.button("Run Intrinsic Valuation"):
    if not property_url:
        st.error("Please enter a valid URL first.")
    elif not api_key:
        st.error("Please enter your Google API Key in the sidebar.")
    else:
        with st.spinner("Bypassing marketing hype... analyzing hardware..."):
            
            # 1. MOCK SCRAPER: In the future, data_fetch.py gets this image URL from the Domain link.
            # For now, we hand it a direct image URL to test the pipeline.
            test_image_url = "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=800&q=80"
            
            # 2. RUN THE AI VISION ENGINE
            # Because you are on a proxy, this will take ~5 seconds and return your mock data!
            vision_result = analyze_image_url(test_image_url, api_key)
            
            score = vision_result.get("condition_score", "N/A")
            needs_reno = vision_result.get("needs_cosmetic_renovation", True)
            reasoning = vision_result.get("reasoning", "No AI notes available.")
            
            # 3. DISPLAY THE REPORT
            st.success("Analysis Complete.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(label="Asking Price (Hype)", value="$1,500,000")
                st.metric(label="True Land Value", value="$1,100,000")
                st.metric(label="Land-to-Asset Ratio", value="73%")
                
            with col2:
                # Dynamically injecting the AI's score!
                st.metric(label="AI Condition Score", value=f"{score} / 10")
                st.metric(label="Hype Premium", value="$150,000", delta="-Overpriced", delta_color="inverse")
            
            st.markdown("---")
            st.write("### 🤖 AI Inspector Notes")
            st.info(reasoning)
            
            if needs_reno:
                st.warning("🛠️ Flagged for Cosmetic Arbitrage: Property requires renovation. Factor into holding costs.")
