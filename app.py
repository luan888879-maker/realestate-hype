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
    # We no longer need Apify or ScraperAPI!
except (KeyError, FileNotFoundError):
    st.error("⚠️ API Key missing. Please ensure GEMINI_API_KEY is configured in your Streamlit secrets.")
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
        
    with st.spinner("Stealth browser running extraction..."):
        
        # 1. API EXTRACTION (Using our own Stealth Browser)
        scrape_result = fetch_property_data(property_url)
        
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
        reasoning = vision_result.get("reasoning", "No AI notes available.")
        
        # 3. RUN THE MATH ENGINE
        try:
            safe_score = int(score)
        except:
            safe_score = 5

        valuation = calculate_valuation(
            asking_price=asking_price, 
            condition_score=safe_score, 
            land_value=estimated_land_val,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            carspaces=carspaces
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
            elif asking_price > 0:
                prem_val = valuation.get("hype_premium", 0)
                if prem_val > 0:
                    st.metric(label="Hype Premium", value=f"${prem_val:,.0f}", delta="-Overpriced", delta_color="inverse")
                else:
                    st.metric(label="Discount to Intrinsic", value=f"${abs(prem_val):,.0f}", delta="Underpriced!", delta_color="normal")
            else:
                 st.metric(label="Hype Premium", value="N/A (Auction)")
        
        st.markdown("---")
        st.write("### 🤖 AI Inspector Notes")
        st.info(reasoning)
        if needs_reno:
            st.warning("🛠️ Flagged for Cosmetic Arbitrage: Property requires renovation.")
