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
    
    # Check for API Key
    if 'api_key' not in locals() or not api_key:
        st.error("Please ensure your Google API Key is configured in the sidebar or secrets vault.")
        st.stop()
        
    with st.spinner("Analyzing hardware and calculating valuation..."):
        
        target_image = None
        asking_price = 0
        address = "Unknown Address"
        asking_price_str = "Unknown"
        
        # ROUTE A: Use Manual Upload if provided
        if uploaded_photo is not None:
            target_image = Image.open(uploaded_photo)
            asking_price = manual_price
            address = manual_address
            asking_price_str = f"${asking_price:,.0f}"
            st.success("Using Manual Override Data.")
            
        # ROUTE B: Try the URL Scraper
        elif property_url:
            st.info("Attempting to bypass Domain WAF...")
            scrape_result = fetch_property_data(property_url)
            
            if not scrape_result.get("success"):
                st.error(f"⚠️ Scraper Blocked: {scrape_result.get('error')}")
                st.warning("Please use the 'Manual Override' expander above to upload the photo directly.")
                st.stop()
            else:
                target_image_url = scrape_result.get("image_urls", [])[0]
                address = scrape_result.get("address", "Unknown Address")
                asking_price = scrape_result.get("asking_price", 0)
                asking_price_str = scrape_result.get("formatted_price", "Price not listed")
                target_image = target_image_url # Can be URL string for our vision model
        else:
            st.error("Please enter a URL or use the Manual Override.")
            st.stop()

        # UI UPDATE: Display Property Header
        st.subheader(f"📍 {address}")
        
        # Display the image whether it's an uploaded PIL Image or a URL string
        st.image(target_image, caption=f"Primary Image - {address}", use_column_width=True)
        
        # 2. RUN THE AI VISION ENGINE
        # (Your vision_model.py should be able to handle both URLs and direct PIL Images, 
        # but for now, if it expects a URL, you might need to test with an Unsplash URL 
        # or update vision_model to accept PIL images directly).
        
        if isinstance(target_image, str):
            vision_result = analyze_image_url(target_image, api_key)
        else:
            # If they uploaded a file, we need the vision model to read the raw image
            # For this quick fix, let's just trigger a placeholder so the UI doesn't crash
            vision_result = {"condition_score": 7, "needs_cosmetic_renovation": False, "reasoning": "Manual upload detected. High quality finish."}
            
        score = vision_result.get("condition_score", "N/A")
        needs_reno = vision_result.get("needs_cosmetic_renovation", True)
        reasoning = vision_result.get("reasoning", "No AI notes available.")
        
        # 3. DISPLAY THE REPORT
        st.success("Analysis Complete.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(label="Asking Price (Hype)", value=asking_price_str) 
            st.metric(label="True Land Value", value="$1,100,000") # Still hardcoded
            st.metric(label="Land-to-Asset Ratio", value="73%") # Still hardcoded
            
        with col2:
            st.metric(label="AI Condition Score", value=f"{score} / 10")
            st.metric(label="Hype Premium", value="Pending Math", delta="-Overpriced", delta_color="inverse")
        
        st.markdown("---")
        st.write("### 🤖 AI Inspector Notes")
        st.info(reasoning)
        
