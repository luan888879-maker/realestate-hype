import streamlit as st
from data_fetch import fetch_property_data
from valuation_engine import calculate_valuation
from vision_model import analyze_property_images

# --- PAGE SETUP ---
st.set_page_config(page_title="Hype vs Hardware", layout="wide")

st.title("Hype vs. Hardware 🏠")
st.write("AI-Powered Intrinsic Property Valuation")

# --- SECURE SETTINGS & API VAULT ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    scraper_api_key = st.secrets["SCRAPER_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("⚠️ API Keys missing. Please ensure GEMINI_API_KEY and SCRAPER_API_KEY are configured in your Streamlit secrets.")
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
        
    with st.spinner("Hybrid network running extraction (Stealth + Proxy)..."):
        
        # 1. API EXTRACTION (Stealth HTML + ScraperAPI Images)
        scrape_result = fetch_property_data(property_url, scraper_api_key)
        
        if not scrape_result.get("success"):
            st.error(f"⚠️ Extraction Error: {scrape_result.get('error')}")
            st.stop()
            
        downloaded_images = scrape_result.get("downloaded_images", [])
        address = scrape_result.get("address", "Unknown Address")
        asking_price = scrape_result.get("asking_price", 0)
        asking_price_str = scrape_result.get("formatted_price", "Price not listed")
        
        bedrooms = scrape_result.get("bedrooms", 0)
        bathrooms = scrape_result.get("bathrooms", 0)
        carspaces = scrape_result.get("carspaces", 0)

        # --- UI UPDATE ---
        st.subheader(f"📍 {address}")
        if bedrooms or bathrooms or carspaces:
            st.caption(f"🛏️ {bedrooms} Bed | 🛁 {bathrooms} Bath | 🚗 {carspaces} Car")
            
        if asking_price == 0:
            st.warning(f"⚠️ Listed as '{asking_price_str}'. Intrinsic Value will calculate, but Hype Premium cannot be determined.")
        
        if downloaded_images:
            st.image(downloaded_images[0], caption=f"Primary Image - {address}", use_column_width=True)
            if len(downloaded_images) > 1:
                with st.expander(f"📸 View all {len(downloaded_images)} extracted photos"):
                    cols = st.columns(len(downloaded_images))
                    for idx, img in enumerate(downloaded_images):
                        cols[idx].image(img, use_column_width=True)
        else:
            st.warning("No high-res gallery images could be extracted.")
            st.stop() 

    with st.spinner("AI Inspector scanning interior condition..."):
        # 2. RUN THE AI VISION ENGINE
        vision_result = analyze_property_images(downloaded_images, api_key)
        
        score = vision_result.get("condition_score", 5)
        needs_reno = vision_result.get("needs_cosmetic_renovation", True)
        reasoning
