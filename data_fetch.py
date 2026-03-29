from curl_cffi import requests as stealth_requests
from bs4 import BeautifulSoup
import re

def fetch_property_data(property_url: str) -> dict:
    print(f"🚀 [1/2] Launching Stealth Chrome for Brute-Force Extraction...")
    
    try:
        # 1. Grab raw HTML directly
        response = stealth_requests.get(property_url, impersonate="chrome110", timeout=20.0)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Domain blocked the stealth request (Status {response.status_code})."}
            
        html_text = response.text
        
        # --- BRUTE-FORCE REGEX HUNTER ---
        # We ignore the JSON tree and search the raw code directly.
        
        # 1. Core Specs
        beds_match = re.search(r'"beds"\s*:\s*(\d+)', html_text, re.IGNORECASE)
        bedrooms = int(beds_match.group(1)) if beds_match else 0
        
        baths_match = re.search(r'"baths"\s*:\s*(\d+)', html_text, re.IGNORECASE)
        bathrooms = int(baths_match.group(1)) if baths_match else 0
        
        car_match = re.search(r'"(?:parking|cars)"\s*:\s*(\d+)', html_text, re.IGNORECASE)
        carspaces = int(car_match.group(1)) if car_match else 0
        
        # 2. Price
        price_match = re.search(r'"displayPrice"\s*:\s*"([^"]+)"', html_text, re.IGNORECASE)
        formatted_price = price_match.group(1) if price_match else 'Contact Agent'
        asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
        
        # 3. Address
        addr_match = re.search(r'"(?:displayAddress|streetAddress)"\s*:\s*"([^"]+)"', html_text, re.IGNORECASE)
        address = addr_match.group(1) if addr_match else 'Unknown Address'
        
        if address == 'Unknown Address':
            soup = BeautifulSoup(html_text, 'html.parser')
            h1_tag = soup.find('h1')
            if h1_tag:
                address = h1_tag.text.strip()
        
        # 4. Land Size
        land_m2 = 0
        land_match = re.search(r'"landArea"\s*:\s*\{\s*"value"\s*:\s*([\d\.]+)', html_text, re.IGNORECASE)
        if land_match:
            land_m2 = float(land_match.group(1))
        else:
            land_match_alt = re.search(r'"areaSize"\s*:\s*(\d+)', html_text, re.IGNORECASE)
            if land_match_alt:
                land_m2 = float(land_match_alt.group(1))
                
        # 5. Sold History
        sold_records = []
        sold_matches = re.finditer(r'"date"\s*:\s*"([^"]+)".*?"price"\s*:\s*(\d+).*?"category"\s*:\s*"sold"', html_text, re.IGNORECASE)
        for match in sold_matches:
            sold_records.append({"date": match.group(1), "price": int(match.group(2))})
            
        if not sold_records:
            sold_price_match = re.search(r'"soldPrice"\s*:\s*(\d+)', html_text, re.IGNORECASE)
            sold_date_match = re.search(r'"soldDate"\s*:\s*"([^"]+)"', html_text, re.IGNORECASE)
            if sold_price_match and sold_date_match:
                sold_records.append({"date": sold_date_match.group(1), "price": int(sold_price_match.group(1))})

        print(f"✅ [2/2] Data extracted! {bedrooms} Bed, {bathrooms} Bath, {land_m2}m2. Found {len(sold_records)} sold records.")

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
