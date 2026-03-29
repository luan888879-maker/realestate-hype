from curl_cffi import requests as stealth_requests
from bs4 import BeautifulSoup
import json
import re

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
    print(f"🚀 [1/2] Launching Stealth Chrome (The ID Lock-On Method)...")
    
    try:
        # --- 1. EXTRACT THE TARGET ID ---
        listing_id_match = re.search(r'-(\d+)/?$', property_url)
        listing_id = listing_id_match.group(1) if listing_id_match else None
        
        # 2. Grab raw HTML directly
        response = stealth_requests.get(property_url, impersonate="chrome110", timeout=20.0)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Domain blocked the stealth request (Status {response.status_code})."}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- 3. THE ABSOLUTE TRUTH: Title Tag ---
        title_text = soup.title.string.lower() if soup.title and soup.title.string else ""
        
        # Extract Address directly from the browser tab title
        address = soup.title.string.split('-')[0].split('|')[0].strip() if soup.title else "Unknown Address"
        
        # Google forces agents to put the real beds/baths in the title
        beds_match = re.search(r'(\d+)\s*bed', title_text)
        bedrooms = int(beds_match.group(1)) if beds_match else 0
        
        baths_match = re.search(r'(\d+)\s*bath', title_text)
        bathrooms = int(baths_match.group(1)) if baths_match else 0
        
        cars_match = re.search(r'(\d+)\s*(?:car|parking)', title_text)
        carspaces = int(cars_match.group(1)) if cars_match else 0
        
        # --- 4. JSON ID LOCK-ON FOR MARKET METRICS ---
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        asking_price = 0
        formatted_price = "Contact Agent"
        land_m2 = 0
        sold_records = []
        
        if next_data_script:
            data = json.loads(next_data_script.string)
            
            main_property_data = {}
            
            # Recursive function to find the exact dictionary belonging to our URL
            def find_exact_listing(obj):
                nonlocal main_property_data
                if isinstance(obj, dict):
                    # Check if this dictionary represents our exact house
                    if str(obj.get('id')) == listing_id or str(obj.get('listingId')) == listing_id:
                        # Grab it if it has the juicy market data
                        if 'priceDetails' in obj or 'propertyDetails' in obj:
                            main_property_data = obj
                            return True
                    for v in obj.values():
                        if find_exact_listing(v): return True
                elif isinstance(obj, list):
                    for item in obj:
                        if find_exact_listing(item): return True
                return False

            if listing_id:
                find_exact_listing(data)
                
            # If we locked on, we ONLY search inside main_property_data. 
            # This completely ignores your past search filters!
            search_target = main_property_data if main_property_data else data
            
            # Get Price
            price_details = hunt_for_key(search_target, 'priceDetails')
            if isinstance(price_details, dict):
                formatted_price = price_details.get('displayPrice', 'Contact Agent')
                asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
                
            # Get Land
            land_area = hunt_for_key(search_target, 'landArea') or hunt_for_key(search_target, 'areaSize')
            if isinstance(land_area, dict) and 'value' in land_area:
                land_m2 = float(land_area.get('value', 0))
            elif isinstance(land_area, (int, float)):
                land_m2 = float(land_area)
                
            # Get History
            history_timeline = hunt_for_key(search_target, 'timeline') or hunt_for_key(search_target, 'events')
            if isinstance(history_timeline, list):
                for event in history_timeline:
                    if isinstance(event, dict) and event.get('category', '').lower() == 'sold':
                        date = event.get('date', 'Unknown Date')
                        price = event.get('price', 0)
                        if price > 0:
                            sold_records.append({"date": date, "price": price})
                            
            if not sold_records:
                sold_details = hunt_for_key(search_target, 'soldDetails')
                if isinstance(sold_details, dict):
                    price = sold_details.get('soldPrice', 0)
                    date = sold_details.get('soldDate', 'Unknown Date')
                    if price > 0:
                        sold_records.append({"date": date, "price": price})

        # Fallback just in case the title tag missed the beds/baths
        if bedrooms == 0 and main_property_data:
            features = hunt_for_key(main_property_data, 'features') or hunt_for_key(main_property_data, 'propertyFeatures')
            if isinstance(features, dict):
                bedrooms = int(features.get('beds', 0))
                bathrooms = int(features.get('baths', 0))
                carspaces = int(features.get('parking', 0) or features.get('cars', 0))

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
