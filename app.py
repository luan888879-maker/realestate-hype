from data_fetch import fetch_property_data
import streamlit as st
import time
from vision_model import analyze_image_url

st.set_page_config(page_title="Hype vs Hardware", page_icon="🏢", layout="centered")

# --- SECURE SETTINGS & API VAULT ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    domain_api_key = st.secrets["DOMAIN_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("⚠️ API Keys missing from Streamlit Secrets. Please check your cloud settings.")
    st.stop()

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

import streamlit as st
from PIL import Image
# ... your other imports ...

# --- NEW HYBRID INPUT UI ---
st.write("### Target Property")
property_url = st.text_input("Domain.com.au Listing URL:")

st.markdown("---")
with st.expander("🛠️ Manual Override (If Domain Firewall Blocks URL)"):
    st.info("Use this if Domain.com.au blocks the cloud scraper.")
    uploaded_photo = st.file_uploader("Upload Property Photo", type=["jpg", "jpeg", "png"])
    manual_price = st.number_input("Asking Price ($)", min_value=0, value=1500000, step=50000)
    manual_address = st.text_input("Property Address", value="Custom Upload")

# The Action Button
if st.button("Run Intrinsic Valuation"):
    
    # 1. API Key Check
    if 'api_key' not in locals() or 'domain_api_key' not in locals():
        st.error("⚠️ API Keys missing. Please ensure GEMINI_API_KEY and DOMAIN_API_KEY are in your Streamlit Secrets.")
        st.stop()
        
    with st.spinner("Pulling API data, analyzing hardware, and calculating valuation..."):
        
        target_image = None
        asking_price = 0
        address = "Unknown Address"
        asking_price_str = "Unknown"
        bedrooms, bathrooms, carspaces = 0, 0, 0
        
        # ROUTE A: Use Manual Upload if provided
        if uploaded_photo is not None:
            target_image = Image.open(uploaded_photo)
            asking_price = manual_price
            address = manual_address
            asking_price_str = f"${asking_price:,.0f}"
            st.success("Using Manual Override Data.")
            
        # ROUTE B: Try the Official Domain API
        elif property_url:
            st.info("Connecting to official Domain API...")
            scrape_result = fetch_property_data(property_url, domain_api_key)
            
            if not scrape_result.get("success"):
                st.error(f"⚠️ API Error: {scrape_result.get('error')}")
                st.warning("Please check your Domain URL, or use the 'Manual Override' expander above.")
                st.stop()
            else:
                target_image_url = scrape_result.get("image_urls", [])[0] if scrape_result.get("image_urls") else None
                address = scrape_result.get("address", "Unknown Address")
                asking_price = scrape_result.get("asking_price", 0)
                asking_price_str = scrape_result.get("formatted_price", "Price not listed")
                
                # Grab the hardware stats!
                bedrooms = scrape_result.get("bedrooms", 0)
                bathrooms = scrape_result.get("bathrooms", 0)
                carspaces = scrape_result.get("carspaces", 0)
                
                target_image = target_image_url 
        else:
            st.error("Please enter a URL or use the Manual Override.")
            st.stop()

        # --- UI UPDATE: Display Property Header & Hardware ---
        st.subheader(f"📍 {address}")
        if bedrooms or bathrooms or carspaces:
            st.caption(f"🛏️ {bedrooms} Bed | 🛁 {bathrooms} Bath | 🚗 {carspaces} Car")
        
        if target_image:
            st.image(target_image, caption=f"Primary Image - {address}", use_column_width=True)
        else:
            st.warning("No image found for this property.")
        
        # 2. RUN THE AI VISION ENGINE
        if isinstance(target_image, str):
            vision_result = analyze_image_url(target_image, api_key)
        else:
            vision_result = {"condition_score": 7, "needs_cosmetic_renovation": False, "reasoning": "Manual upload detected. High quality finish."}
            
        score = vision_result.get("condition_score", 5)
        needs_reno = vision_result.get("needs_cosmetic_renovation", True)
        reasoning = vision_result.get("reasoning", "No AI notes available.")
        
        # 3. RUN THE MATH ENGINE
        try:
            safe_score = int(score)
        except:
            safe_score = 5

        valuation = calculate_valuation(
            asking_price=asking_price, 
            condition_score=safe_score, 
            land_value=estimated_land_val # Make sure this variable exists above your button!
        )
        
        # 4. DISPLAY THE REPORT
        st.success("Analysis Complete.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(label="Asking Price (Hype)", value=asking_price_str) 
            st.metric(label="AI-Adjusted House Value", value=f"${valuation.get('house_value', 0):,.0f}")
            st.metric(label="Land-to-Asset Ratio", value=f"{valuation.get('land_to_asset_ratio', 0)}%")
            
        with col2:
            st.metric(label="AI Condition Score", value=f"{safe_score} / 10")
            
            if valuation.get("error"):
                st.metric(label="Hype Premium", value="Data Error")
            else:
                prem_val = valuation.get("hype_premium", 0)
                if prem_val > 0:
                    st.metric(label="Hype Premium", value=f"${prem_val:,.0f}", delta="-Overpriced", delta_color="inverse")
                else:
                    st.metric(label="Discount to Intrinsic", value=f"${abs(prem_val):,.0f}", delta="Underpriced!", delta_color="normal")
        
        st.markdown("---")
        st.write("### 🤖 AI Inspector Notes")
        st.info(reasoning)
        
        if needs_reno:
            st.warning("🛠️ Flagged for Cosmetic Arbitrage: Property requires renovation. Factor into holding costs.")
