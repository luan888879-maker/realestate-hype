import requests
from PIL import Image
from io import BytesIO
from apify_client import ApifyClient
import re

def extract_value(data_dict, possible_keys, default=None):
    """Hunts the Apify dictionary for variations of a key."""
    if not isinstance(data_dict, dict):
        return default
        
    for key, value in data_dict.items():
        if key.lower() in [k.lower() for k in possible_keys] and value is not None:
            return value
        if isinstance(value, dict):
            result = extract_value(value, possible_keys, default)
            if result != default:
                return result
    return default

def fetch_property_data(property_url: str, apify_api_key: str) -> dict:
    print(f"🚀 [1/3] Triggering PowerAI Domain Scraper (Pay-Per-Result)...")
    
    client = ApifyClient(apify_api_key)
    
    # Run the specific PowerAI Domain Actor
    run_input = {
        "searchUrls": [property_url],
        "maxItems": 1
    }
    
    try:
        # Changed to your new chosen Actor
        run = client.actor("powerai/domain-com-au-property-scraper-ppr").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        if not items:
            return {"success": False, "error": "Apify ran successfully, but returned no data. Check the URL."}
            
        data = items[0]
        
        # --- 1. CORE PROPERTY DATA ---
        address = str(extract_value(data, ['address', 'displayaddress', 'streetaddress'], "Unknown Address"))
        
        price_str = str(extract_value(data, ['price', 'displayprice'], "0"))
        asking_price = int(re.sub(r'[^\d]', '', price_str)) if re.sub(r'[^\d]', '', price_str) else 0
        
        sold_price_str = str(extract_value(data, ['soldprice', 'solddetails'], "0"))
        sold_price = int(re.sub(r'[^\d]', '', sold_price_str)) if re.sub(r'[^\d]', '', sold_price_str) else 0
        
        bedrooms = int(extract_value(data, ['beds', 'bedrooms', 'bedroom'], 0))
        bathrooms = int(extract_value(data, ['baths', 'bathrooms', 'bathroom'], 0))
        carspaces = int(extract_value(data, ['cars', 'carspaces', 'parking'], 0))
        
        # --- 2. ADVANCED BUILDING & LAND METRICS ---
        land_m2 = extract_value(data, ['landarea', 'landsize', 'areasize'], 0)
        building_m2 = extract_value(data, ['buildingarea', 'floorsize', 'buildingsize'], 0)
        
        # Domain stores extra amenities in a list/array
        features_list = extract_value(data, ['features', 'propertyfeatures', 'tags'], [])
        if not isinstance(features_list, list):
            features_list = []
            
        # Convert list to lowercase string for easy keyword hunting
        features_text = str(features_list).lower()
        
        has_pool = 'pool' in features_text
        is_vacant_land = 'vacant' in features_text or 'land' in address.lower()
        
        # --- 3. IMAGE EXTRACTION ---
        image_urls = extract_value(data, ['images', 'photos', 'media', 'imageurls'], [])
        clean_urls = []
        if isinstance(image_urls, list):
            for img in image_urls:
                if isinstance(img, str) and img.startswith('http'):
                    clean_urls.append(img)
                elif isinstance(img, dict) and 'url' in img and img['url'].startswith('http'):
                    clean_urls.append(img['url'])

        print(f"✅ [2/3] Data extracted! {bedrooms} Bed, {bathrooms} Bath | Land: {land_m2}m2 | Pool: {has_pool}")
        
        # --- 4. SECURE IMAGE DOWNLOAD ---
        pil_images = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        for i, url in enumerate(clean_urls[:5]):
            print(f"   -> Downloading high-res photo {i+1}...") 
            try:
                img_response = requests.get(url, headers=headers, timeout=15.0)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    pil_images.append(img)
            except Exception as e:
                print(f"   ❌ Failed to download photo {i+1}: {e}")

        print(f"🎉 [3/3] Successfully downloaded {len(pil_images)} photos.")

        return {
            "success": True,
            "downloaded_images": pil_images,
            "address": address,
            "asking_price": asking_price,
            "sold_price": sold_price,
            "formatted_price": price_str,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "carspaces": carspaces,
            "land_m2": land_m2,
            "building_m2": building_m2,
            "has_pool": has_pool,
            "is_vacant_land": is_vacant_land,
            "error": None
        }

    except Exception as e:
        return {"success": False, "error": f"Apify Connection Error: {str(e)}"}
