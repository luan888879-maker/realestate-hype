from curl_cffi import requests as stealth_requests
from bs4 import BeautifulSoup
import re

def fetch_property_data(property_url: str) -> dict:
    print(f"🚀 [1/2] Launching Stealth Chrome (Targeting SEO Meta Tags)...")
    
    try:
        # 1. Grab raw HTML directly
        response = stealth_requests.get(property_url, impersonate="chrome110", timeout=20.0)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Domain blocked the stealth request (Status {response.status_code})."}
            
        html_text = response.text
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # --- 1. THE ABSOLUTE TRUTH: SEO Meta Tags ---
        # Google requires these to describe the main house, preventing neighbor-scraping.
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        desc_text = meta_desc['content'].lower() if meta_desc else ""
        
        beds_match = re.search(r'(\d+)\s+bed', desc_text)
        bedrooms = int(beds_match.group(1)) if beds_match else 0
        
        baths_match = re.search(r'(\d+)\s+bath', desc_text)
        bathrooms = int(baths_match.group(1)) if baths_match else 0
        
        cars_match = re.search(r'(\d+)\s+(?:car|parking)', desc_text)
        carspaces = int(cars_match.group(1)) if cars_match else 0
        
        # --- 2. THE EXACT ADDRESS ---
        address = "Unknown Address"
        if soup.title and soup.title.string:
            # Example: "211 Fullers Road, Chatswood NSW 2067 - 4 beds 1 bath | Domain"
            address = soup.title.string.split('-')[0].split('|')[0].strip()
            
        # --- 3. THE PRICE ---
        # Domain puts the main price in a specific UI element at the top
        price_elem = soup.find(attrs={"data-testid": "listing-details__summary-title"})
        formatted_price = price_elem.text.strip() if price_elem else "Contact Agent"
        asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
        
        # --- 4. LAND SIZE & HISTORY (Quarantining the Neighbors) ---
        # We split the raw text at the word "similarProperties" to completely destroy 
        # the bottom half of the JSON where the neighbors are stored.
        safe_html = html_text.split('"similarProperties"')[0]
        
        # Fallback for price if it wasn't in the UI element
        if asking_price == 0:
            price_match = re.search(r'"displayPrice"\s*:\s*"([^"]+)"', safe_html, re.IGNORECASE)
            if price_match:
                formatted_price = price_match.group(1)
                asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0

        # Hunt for Land Size in the safe zone
        land_m2 = 0
        land_match = re.search(r'"landArea"\s*:\s*\{\s*"value"\s*:\s*([\d\.]+)', safe_html, re.IGNORECASE)
        if land_match:
            land_m2 = float(land_match.group(1))
        else:
            land_match_alt = re.search(r'"areaSize"\s*:\s*(\d+)', safe_html, re.IGNORECASE)
            if land_match_alt:
                land_m2 = float(land_match_alt.group(1))
                
        # Hunt for Sold History in the safe zone
        sold_records = []
        sold_matches = re.finditer(r'"date"\s*:\s*"([^"]+)".*?"price"\s*:\s*(\d+).*?"category"\s*:\s*"sold"', safe_html, re.IGNORECASE)
        for match in sold_matches:
            sold_records.append({"date": match.group(1), "price": int(match.group(2))})
            
        if not sold_records:
            sold_price_match = re.search(r'"soldPrice"\s*:\s*(\d+)', safe_html, re.IGNORECASE)
            sold_date_match = re.search(r'"soldDate"\s*:\s*"([^"]+)"', safe_html, re.IGNORECASE)
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
