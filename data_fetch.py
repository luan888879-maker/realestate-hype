from curl_cffi import requests as stealth_requests
from bs4 import BeautifulSoup
import json
import re

def purge_neighbors(obj):
    """Recursively destroys any data related to neighbors or recommendations."""
    bad_keys = ['similarproperties', 'recommendedproperties', 'nearbyproperties']
    if isinstance(obj, dict):
        keys_to_delete = [k for k in obj.keys() if str(k).lower() in bad_keys]
        for k in keys_to_delete:
            del obj[k]
        for v in obj.values():
            purge_neighbors(v)
    elif isinstance(obj, list):
        for item in obj:
            purge_neighbors(item)

def hunt_for_dict_with_keys(obj, required_keys):
    """Finds the first dictionary containing ALL the requested keys."""
    if isinstance(obj, dict):
        if all(k in obj for k in required_keys):
            return obj
        for v in obj.values():
            res = hunt_for_dict_with_keys(v, required_keys)
            if res: return res
    elif isinstance(obj, list):
        for item in obj:
            res = hunt_for_dict_with_keys(item, required_keys)
            if res: return res
    return {}

def hunt_for_key(obj, target_key):
    """Finds the first value for a specific key anywhere in the data."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() == target_key.lower() and v is not None:
                return v
        for v in obj.values():
            res = hunt_for_key(v, target_key)
            if res is not None: return res
    elif isinstance(obj, list):
        for item in obj:
            res = hunt_for_key(item, target_key)
            if res is not None: return res
    return None

def fetch_property_data(property_url: str) -> dict:
    print(f"🚀 [1/2] Launching Stealth Chrome (The JSON Quarantine Method)...")
    
    try:
        # 1. Grab raw HTML directly
        response = stealth_requests.get(property_url, impersonate="chrome110", timeout=20.0)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Domain blocked the stealth request (Status {response.status_code})."}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not next_data_script:
            return {"success": False, "error": "HTML loaded, but Domain JSON data not found."}
            
        # Load the raw JSON into memory
        data = json.loads(next_data_script.string)
        
        # 🛑 THE FIX: Destroy the neighbors before searching
        purge_neighbors(data)
        
        # 1. CORE SPECS (Find the single dictionary that contains both beds AND baths)
        features = hunt_for_dict_with_keys(data, ['beds', 'baths'])
        bedrooms = int(features.get('beds', 0))
        bathrooms = int(features.get('baths', 0))
        carspaces = int(features.get('parking', 0) or features.get('cars', 0))
        
        # 2. ADDRESS
        address_dict = hunt_for_dict_with_keys(data, ['displayAddress'])
        address = address_dict.get('displayAddress', 'Unknown Address')
        
        # 3. PRICE
        price_dict = hunt_for_dict_with_keys(data, ['displayPrice'])
        formatted_price = price_dict.get('displayPrice', 'Contact Agent')
        asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
        
        # 4. LAND SIZE
        land_m2 = 0
        land_area = hunt_for_key(data, 'landArea') or hunt_for_key(data, 'areaSize')
        if isinstance(land_area, dict) and 'value' in land_area:
            land_m2 = float(land_area.get('value', 0))
        elif isinstance(land_area, (int, float)):
            land_m2 = float(land_area)
            
        # 5. PROPERTY HISTORY
        sold_records = []
        history_timeline = hunt_for_key(data, 'timeline') or hunt_for_key(data, 'events')
        
        if isinstance(history_timeline, list):
            for event in history_timeline:
                if isinstance(event, dict) and event.get('category', '').lower() == 'sold':
                    date = event.get('date', 'Unknown Date')
                    price = event.get('price', 0)
                    if price > 0:
                        sold_records.append({"date": date, "price": price})
                        
        # Fallback for sold history
        if not sold_records:
            sold_details = hunt_for_key(data, 'soldDetails')
            if isinstance(sold_details, dict):
                price = sold_details.get('soldPrice', 0)
                date = sold_details.get('soldDate', 'Unknown Date')
                if price > 0:
                    sold_records.append({"date": date, "price": price})

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
