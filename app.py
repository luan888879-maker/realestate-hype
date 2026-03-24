from data_fetch import fetch_property_data
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
    # This checks if api_key exists (handling both the sidebar and the secrets vault)
    elif 'api_key' not in locals() or not api_key:
        st.error("Please ensure your Google API Key is configured in the sidebar or secrets vault.")
    else:
        with st.spinner("Scraping Domain.com.au and analyzing hardware..."):
            
            # 1. RUN THE SCRAPER
            scrape_result = fetch_property_data(property_url)
            
            if not scrape_result.get("success"):
                st.error(f"⚠️ {scrape_result.get('error')}")
            else:
                target_image_url = scrape_result["image_url"]
                
                # Show the user the photo we successfully grabbed!
                st.image(target_image_url, caption="Target Property Acquired", use_column_width=True)
                
                # 2. RUN THE AI VISION ENGINE
                vision_result = analyze_image_url(target_image_url, api_key)
                
                score = vision_result.get("condition_score", "N/A")
                needs_reno = vision_result.get("needs_cosmetic_renovation", True)
                reasoning = vision_result.get("reasoning", "No AI notes available.")
                
                # 3. DISPLAY THE REPORT
                st.success("Analysis Complete.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # These math figures are still hardcoded placeholders until we wire up valuation_engine.py next!
                    st.metric(label="Asking Price (Hype)", value="$1,500,000") 
                    st.metric(label="True Land Value", value="$1,100,000")
                    st.metric(label="Land-to-Asset Ratio", value="73%")
                    
                with col2:
                    st.metric(label="AI Condition Score", value=f"{score} / 10")
                    st.metric(label="Hype Premium", value="$150,000", delta="-Overpriced", delta_color="inverse")
                
                st.markdown("---")
                st.write("### 🤖 AI Inspector Notes")
                st.info(reasoning)
                
                if needs_reno:
                    st.warning("🛠️ Flagged for Cosmetic Arbitrage: Property requires renovation. Factor into holding costs.")
