from curl_cffi import requests as stealth_requests
from bs4 import BeautifulSoup
import re

def fetch_property_data(property_url: str) -> dict:
    print(f"🚀 [1/2] Launching Stealth Chrome (Visual UI Targeting)...")
    
    try:
        # 1. Grab raw HTML directly
        response = stealth_requests.get(property_url, impersonate="chrome110", timeout=20.0)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Domain blocked the stealth request (Status {response.status_code})."}
            
        html_text = response.text
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # --- 1. PRICE & ADDRESS (These worked perfectly last time) ---
        address = soup.title.string.split('-')[0].split('|')[0].strip() if soup.title else "Unknown Address"
        
        price_elem = soup.find(attrs={"data-testid": "listing-details__summary-title"})
        formatted_price = price_elem.text.strip() if price_elem else "Contact Agent"
        asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0

        # --- 2. BEDS, BATHS, CARS (Targeting Domain's QA tags directly on the UI) ---
        def extract_ui_feature(testid):
            tag = soup.find(attrs={"data-testid": testid})
            if tag:
                # Strip everything except numbers
                num = re.sub(r'[^\d]', '', tag.text)
                return int(num) if num else 0
            return 0

        bedrooms = extract_ui_feature("property-features-feature-beds")
        bathrooms = extract_ui_feature("property-features-feature-baths")
        carspaces = extract_ui_feature("property-features-feature-parking")
        
        # --- FALLBACK: If UI tags fail, read the meta description ---
        if bedrooms == 0 and bathrooms == 0:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            desc_text = meta_desc['content'].lower() if meta_desc else ""
            
            beds_match = re.search(r'(\d+)\s*bed', desc_text)
            bedrooms = int(beds_match.group(1)) if beds_match else 0
            
            baths_match = re.search(r'(\d+)\s*bath', desc_text)
            bathrooms = int(baths_match.group(1)) if baths_match else 0
            
            cars_match = re.search(r'(\d+)\s*(?:car|parking)', desc_text)
            carspaces = int(cars_match.group(1)) if cars_match else 0

        # --- 3. LAND SIZE (From the UI Area Tag) ---
        land_m2 = 0
        area_tag = soup.find(attrs={"data-testid": "property-features-feature-area"})
        if area_tag:
            land_num = re.sub(r'[^\d\.]', '', area_tag.text)
            land_m2 = float(land_num) if land_num else 0

        # --- 4. SOLD HISTORY (Safe Regex on Quarantined Text) ---
        sold_records = []
        # Chop off the similar properties so we don't scrape neighbors
        safe_html = html_text.split('"similarProperties"')[0].split('"nearbyProperties"')[0]
        
        sold_matches = re.finditer(r'"date"\s*:\s*"([^"]+)".*?"price"\s*:\s*(\d+).*?"category"\s*:\s*"sold"', safe_html, re.IGNORECASE)
        for match in sold_matches:
            sold_records.append({"date": match.group(1), "price": int(match.group(2))})

        print(f"✅ [2/2] Data extracted! {bedrooms} Bed, {bathrooms} Bath, {land_m2}m2.")

        return {
            "success": True,
            "address": address,
            "asking_price": asking_price,
            "formatted_price": formatted_price,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "carspaces": carspaces,
            "land_m2": land_m2,
            "sold_records": sold_records,
            "error": None
        }

    except Exception as e:
        return {"success": False, "error": f"Extraction Error: {str(e)}"}
