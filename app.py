import streamlit as st
from data_fetch import fetch_property_data
from valuation_engine import calculate_valuation
from vision_model import analyze_image_url # Assuming this is your Gemini vision import

# --- PAGE SETUP ---
st.set_page_config(page_title="Hype vs Hardware", layout="wide")

st.title("Hype vs. Hardware 🏠")
st.write("AI-Powered Intrinsic Property Valuation")

# --- SECURE SETTINGS & API VAULT ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    domain_api_key = st.secrets["DOMAIN_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("⚠️ API Keys missing from Streamlit Secrets. Please check your cloud settings.")
    st.stop()

# --- INPUT UI ---
st.write("### Target Property")
property_url = st.text_input("Domain.com.au Listing URL:")
estimated_land_val = st.number_input("Estimated Land Value ($)", min_value=100000, value=1100000, step=50000)

st.markdown("---")

# --- THE ACTION BUTTON ---
if st.button("Run Intrinsic Valuation"):
    
    if not property_url:
        st.error("Please enter a valid Domain URL first.")
        st.stop()
        
    with st.spinner("Pulling API data, analyzing hardware, and calculating valuation..."):
        
        # 1. API EXTRACTION
        st.info("Connecting to official Domain API...")
        scrape_result = fetch_property_data(property_url, domain_api_key)
        
        if not scrape_result.get("success"):
            st.error(f"⚠️ API Error: {scrape_result.get('error')}")
            st.stop()
            
        # Extract the clean data
        target_image_url = scrape_result.get("image_urls", [])[0] if scrape_result.get("image_urls") else None
        address = scrape_result.get("address", "Unknown Address")
        asking_price = scrape_result.get("asking_price", 0)
        asking_price_str = scrape_result.get("formatted_price", "Price not listed")
        
        bedrooms = scrape_result.get("bedrooms", 0)
        bathrooms = scrape_result.get("bathrooms", 0)
        carspaces = scrape_result.get("carspaces", 0)

        # --- UI UPDATE: DISPLAY PROPERTY HEADER ---
        st.subheader(f"📍 {address}")
        if bedrooms or bathrooms or carspaces:
            st.caption(f"🛏️ {bedrooms} Bed | 🛁 {bathrooms} Bath | 🚗 {carspaces} Car")
        
        if target_image_url:
            st.image(target_image_url, caption=f"Primary Image - {address}", use_column_width=True)
        else:
            st.warning("No image found for this property.")
            st.stop() # The AI needs an image to do its job!

        # 2. RUN THE AI VISION ENGINE
        vision_result = analyze_image_url(target_image_url, api_key)
            
        score = vision_result.get("condition_score", 5)
        needs_reno = vision_result.get("needs_cosmetic_renovation", True)
        reasoning = vision_result.get("reasoning", "No AI notes available.")
        
        # 3. RUN THE MATH ENGINE
        try:
            safe_score = int(score)
        except:
            safe_score = 5

        # Note: We are currently passing the raw numbers, but the math engine 
        # still needs to be upgraded to use beds and baths!
        valuation = calculate_valuation(
            asking_price=asking_price, 
            condition_score=safe_score, 
            land_value=estimated_land_val
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
