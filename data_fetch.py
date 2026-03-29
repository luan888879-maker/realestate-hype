from curl_cffi import requests as stealth_requests
from bs4 import BeautifulSoup
import json
import re

def extract_complex_data(obj, target_key):
    """Recursively hunts for a key, but ONLY returns it if it is a Dictionary or List."""
    if isinstance(obj, dict):
        if target_key.lower() in [k.lower() for k in obj.keys()] and isinstance(obj.get(target_key), (dict, list)):
            return obj.get(target_key)
        for k, v in obj.items():
            result = extract_complex_data(v, target_key)
            if result is not None: return result
    elif isinstance(obj, list):
        for item in obj:
            result = extract_complex_data(item, target_key)
            if result is not None: return result
    return None

def fetch_property_data(property_url: str) -> dict:
    print(f"🚀 [1/2] Launching Stealth Chrome for Data Extraction...")
    
    try:
        # 1. Grab raw HTML directly
        response = stealth_requests.get(property_url, impersonate="chrome110", timeout=20.0)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Domain blocked the stealth request (Status {response.status_code})."}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not next_data_script:
            return {"success": False, "error": "HTML loaded, but Domain JSON data not found."}
            
        data = json.loads(next_data_script.string)
        
        # 2. Extract Core Data
        address_parts = extract_complex_data(data, 'addressParts')
        address = address_parts.get('displayAddress', 'Unknown Address') if isinstance(address_parts, dict) else 'Unknown Address'
        
        price_details = extract_complex_data(data, 'priceDetails')
        formatted_price = price_details.get('displayPrice', 'Contact Agent') if isinstance(price_details, dict) else 'Contact Agent'
        asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
        
        features = extract_complex_data(data, 'features') or extract_complex_data(data, 'propertyFeatures')
        bedrooms = features.get('beds', 0) if isinstance(features, dict) else 0
        bathrooms = features.get('baths', 0) if isinstance(features, dict) else 0
        carspaces = features.get('parking', 0) if isinstance(features, dict) else 0
        
        # --- NEW: ADVANCED METRICS & HISTORY HUNTER ---
        
        # Hunt for Land Size
        land_area = extract_complex_data(data, 'landArea') or extract_complex_data(data, 'areaSize')
        land_m2 = land_area.get('value', 0) if isinstance(land_area, dict) else 0
        
        # Hunt for Previous Sold History
        sold_records = []
        history_node = extract_complex_data(data, 'propertyHistory') or extract_complex_data(data, 'salesHistory')
        
        # If we find a history array, look for 'sold' events
        if isinstance(history_node, dict):
            timeline = history_node.get('timeline', []) or history_node.get('events', [])
            for event in timeline:
                if isinstance(event, dict) and event.get('category', '').lower() == 'sold':
                    date = event.get('date', 'Unknown Date')
                    price = event.get('price', 0)
                    if price > 0:
                        sold_records.append({"date": date, "price": price})
                        
        # Fallback if history is structured differently
        if not sold_records:
            sold_details = extract_complex_data(data, 'soldDetails')
            if isinstance(sold_details, dict):
                sold_price = sold_details.get('soldPrice', 0)
                sold_date = sold_details.get('soldDate', 'Unknown Date')
                if sold_price > 0:
                     sold_records.append({"date": sold_date, "price": sold_price})

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
