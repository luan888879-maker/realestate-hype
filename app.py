import streamlit as st
from data_fetch import fetch_property_data
from valuation_engine import calculate_valuation
from vision_model import analyze_property_images
from PIL import Image

# --- PAGE SETUP ---
st.set_page_config(page_title="Hype vs Hardware", layout="wide")

st.title("Hype vs. Hardware 🏠")
st.write("AI-Powered Intrinsic Property Valuation")

# --- SECURE SETTINGS ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("⚠️ API Key missing. Please ensure GEMINI_API_KEY is configured in your Streamlit secrets.")
    st.stop()

# --- INPUT UI ---
st.write("### 1. Target Property")
property_url = st.text_input("Domain.com.au Listing URL:")
estimated_land_val = st.number_input("Estimated Land Value ($)", min_value=100000, value=1100000, step=50000)

st.write("### 2. Property Photos")
st.info("💡 To bypass Domain's image firewall, right-click and save 3-5 key photos (Kitchen, Bath, Living, Front) from the listing, then upload them here.")
uploaded_files = st.file_uploader("Upload Property Images", type=["jpg", "jpeg", "png", "webp", "avif"], accept_multiple_files=True)

st.markdown("---")

# --- THE ACTION BUTTON ---
if st.button("Run Intrinsic Valuation"):
    
    if not property_url:
        st.error("Please enter a valid Domain URL.")
        st.stop()
        
    if not uploaded_files:
        st.error("Please upload at least 1 property photo for the AI to analyze.")
        st.stop()
        
    # --- PROCESS UPLOADED IMAGES ---
    pil_images = []
    for file in uploaded_files[:5]: # Cap at 5 for AI processing
        pil_images.append(Image.open(file))
        
    with st.spinner("Extracting hidden Domain market data..."):
        
        # 1. API EXTRACTION (Data Only)
        scrape_result = fetch_property_data(property_url)
        
        if not scrape_result.get("success"):
            st.error(f"⚠️ Extraction Error: {scrape_result.get('error')}")
            st.stop()
            
        address = scrape_result.get("address", "Unknown Address")
        asking_price = scrape_result.get("asking_price", 0)
        asking_price_str = scrape_result.get("formatted_price", "Price not listed")
        bedrooms = scrape_result.get("bedrooms", 0)
        bathrooms = scrape_result.get("bathrooms", 0)
        carspaces = scrape_result.get("carspaces", 0)
        land_m2 = scrape_result.get("land_m2", 0)
        sold_records = scrape_result.get("sold_records", [])

        # --- UI UPDATE: HEADER & DATA ---
        st.subheader(f"📍 {address}")
        
        # Show Beds/Baths/Land
        metrics_text = f"🛏️ {bedrooms} Bed | 🛁 {bathrooms} Bath | 🚗 {carspaces} Car"
        if land_m2: metrics_text += f" | 📏 {land_m2}m² Land"
        st.caption(metrics_text)
            
        if asking_price == 0:
            st.warning(f"⚠️ Listed as '{asking_price_str}'. Intrinsic Value will calculate, but Hype Premium cannot be determined.")
            
        # Show History if found
        if sold_records:
            with st.expander("📜 View Property Sales History"):
                for record in sold_records:
                    st.write(f"**{record.get('date')}**: Sold for ${record.get('price'):,.0f}")

    with st.spinner("AI Inspector scanning interior condition..."):
        # 2. RUN THE AI VISION ENGINE
        vision_result = analyze_property_images(pil_images, api_key)
        
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
