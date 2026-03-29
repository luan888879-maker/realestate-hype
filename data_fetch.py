from curl_cffi import requests as stealth_requests
import requests as standard_requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import json
import re

def extract_complex_data(obj, target_key):
    """Recursively hunts for a key, but ONLY returns it if it is a Dictionary or List."""
    if isinstance(obj, dict):
        if target_key in obj and isinstance(obj[target_key], (dict, list)):
            return obj[target_key]
        for k, v in obj.items():
            result = extract_complex_data(v, target_key)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = extract_complex_data(item, target_key)
            if result is not None:
                return result
    return None

def fetch_property_data(property_url: str, scraper_api_key: str) -> dict:
    print(f"🚀 [1/3] Launching Stealth Chrome Browser for HTML extraction...")
    
    try:
        # 1. Grab raw HTML directly (Free & Fast)
        response = stealth_requests.get(property_url, impersonate="chrome110", timeout=30.0)
        
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
        
        # 3. The Surgical Gallery Hunter
        image_urls = []
        media_folders = []
        
        def find_media_folders(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() == 'media' and isinstance(v, list):
                        media_folders.append(v)
                    else:
                        find_media_folders(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_media_folders(item)
                    
        find_media_folders(data)
        
        for folder in media_folders:
            for item in folder:
                if isinstance(item, dict):
                    item_type = item.get('type', '').lower()
                    if item_type in ['image', 'photograph', 'photo']:
                        url = item.get('url')
                        if url and url.startswith('http'):
                            lower_url = url.lower()
                            if 'floorplan' not in lower_url and 'profile' not in lower_url:
                                clean_url = url.split('?')[0].split('-w')[0]
                                if clean_url not in image_urls:
                                    image_urls.append(clean_url)

        print(f"✅ [2/3] Data extracted! Found {len(image_urls)} unique photos.")
        
        # 4. Proxy Download Images (Bypassing Datacenter IP Blocks)
        pil_images = []
        
        # THE FIX: We MUST give the proxy the VIP ticket, and tell it NOT to throw it away
        img_headers = {
            "Referer": "https://www.domain.com.au/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        for i, url in enumerate(image_urls[:5]):
            print(f"   -> Routing photo {i+1} through Residential Proxy...") 
            try:
                # Instruct ScraperAPI to use Residential IPs AND keep our headers
                proxy_params = {
                    "api_key": scraper_api_key, 
                    "url": url, 
                    "premium": "true",
                    "keep_headers": "true" 
                }
                
                # Notice we pass the img_headers here!
                img_response = standard_requests.get(
                    "http://api.scraperapi.com", 
                    params=proxy_params, 
                    headers=img_headers,
                    timeout=30.0
                )
                
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    pil_images.append(img)
                else:
                    print(f"   ❌ Proxy blocked: Status {img_response.status_code}")
            except Exception as e:
                print(f"   ❌ Connection error on photo {i+1}: {e}")
                continue

        if not pil_images:
             return {"success": False, "error": "Residential proxy failed to download the images."}

        print(f"🎉 [3/3] Successfully downloaded {len(pil_images)} photos into memory.")

        return {
            "success": True,
            "downloaded_images": pil_images,
            "address": address,
            "asking_price": asking_price,
            "formatted_price": formatted_price,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "carspaces": carspaces,
            "error": None
        }

    except Exception as e:
        return {"success": False, "error": f"Connection Error: {str(e)}"}
