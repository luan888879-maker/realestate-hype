from curl_cffi import requests as stealth_requests
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

def fetch_property_data(property_url: str) -> dict:
    print(f"🚀 [1/3] Launching Stealth Chrome Browser with Session Memory...")
    
    # NEW: Create a Session so cookies and the Chrome disguise persist across all requests
    session = stealth_requests.Session(impersonate="chrome110")
    
    try:
        # 1. Grab raw HTML directly
        response = session.get(property_url, timeout=30.0)
        
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
        
        # 4. Download Images using the exact same Session and VIP Headers
        pil_images = []
        
        # NEW: Provide the exact headers the CDN expects to see from a real browser
        img_headers = {
            "Referer": "https://www.domain.com.au/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        
        for i, url in enumerate(image_urls[:5]):
            print(f"   -> Stealth downloading high-res photo {i+1}...") 
            try:
                # NEW: Use session.get() instead of stealth_requests.get()
                img_response = session.get(url, headers=img_headers, timeout=15.0)
                
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    pil_images.append(img)
                else:
                    print(f"   ❌ Blocked by CDN: Status {img_response.status_code}")
            except Exception as e:
                print(f"   ❌ Connection error on photo {i+1}: {e}")
                continue

        if not pil_images:
             return {"success": False, "error": "Stealth network found the URLs, but the CDN blocked the image download."}

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
        return {"success": False, "error": f"Stealth Connection Error: {str(e)}"}
