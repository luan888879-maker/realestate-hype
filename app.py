import streamlit as st
from data_fetch import fetch_property_data
from valuation_engine import calculate_valuation
from vision_model import analyze_image_url # Your Gemini Vision import

# --- PAGE SETUP ---
st.set_page_config(page_title="Hype vs Hardware", layout="wide")

st.title("Hype vs. Hardware 🏠")
st.write("AI-Powered Intrinsic Property Valuation")

# --- SECURE SETTINGS & API VAULT ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    domain_client_id = st.secrets["DOMAIN_CLIENT_ID"]
    domain_client_secret = st.secrets["DOMAIN_CLIENT_SECRET"]
except (KeyError, FileNotFoundError):
    st.error("⚠️ API Keys missing from Streamlit Secrets. Please check your cloud settings.")
    st.stop()

# --- INPUT UI ---
st.write("### Target Property")
property_url = st.text_input("Domain.com.au Listing URL:")
# The $1.1M default land value bridge we discussed
estimated_land_val = st.number_input("Estimated Land Value ($)", min_value=100000, value=1100000, step=50000)

st.markdown("---")

# --- THE ACTION BUTTON ---
if st.button("Run Intrinsic Valuation"):
    
    if not property_url:
        st.error("Please enter a valid Domain URL first.")
        st.stop()
        
    with st.spinner("Authenticating API, analyzing hardware, and calculating valuation..."):
        
        # 1. API EXTRACTION (Using OAuth2 flow)
        st.info("Connecting to official Domain API...")
        scrape_result = fetch_property_data(property_url, domain_client_id, domain_client_secret)
        
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
        st.info("AI Inspector scanning property condition...")
        vision_result = analyze_image_url(target_image_url, api_key)
            
        score = vision_result.get("condition_score", 5)
        needs_reno = vision_result.get("needs_cosmetic_renovation", True)
        reasoning = vision_result.get("reasoning", "No AI notes available.")
        
        # 3. RUN THE MATH ENGINE
        try:
            safe_score = int(score)
        except:
            safe_score = 5

        # We now pass the bedrooms, bathrooms, and carspaces so the engine
        # calculates a dynamic replacement cost instead of a flat $600k!
        valuation = calculate_valuation(
            asking_price=asking_price, 
            condition_score=safe_score, 
            land_value=estimated_land_val,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            carspaces=carspaces
        )
