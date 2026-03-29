from curl_cffi import requests as stealth_requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import json
import re

def extract_complex_data(obj, target_key):
    if isinstance(obj, dict):
        if target_key in obj and isinstance(obj[target_key], (dict, list)):
            return obj[target_key]
        for k, v in obj.items():
            result = extract_complex_data(v, target_key)
            if result != None: return result
    elif isinstance(obj, list):
        for item in obj:
            result = extract_complex_data(item, target_key)
            if result != None: return result
    return None

def fetch_property_data(property_url: str) -> dict:
    print(f"🚀 [1/3] Launching Stealth Chrome Browser...")
    
    session = stealth_requests.Session(impersonate="chrome110")
    
    try:
        response = session.get(property_url, timeout=30.0)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Domain blocked the stealth request (Status {response.status_code})."}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not next_data_script:
            return {"success": False, "error": "HTML loaded, but Domain JSON data not found."}
            
        data = json.loads(next_data_script.string)
        
        address_parts = extract_complex_data(data, 'addressParts')
        address = address_parts.get('displayAddress', 'Unknown Address') if isinstance(address_parts, dict) else 'Unknown Address'
        
        price_details = extract_complex_data(data, 'priceDetails')
        formatted_price = price_details.get('displayPrice', 'Contact Agent') if isinstance(price_details, dict) else 'Contact Agent'
        asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
        
        features = extract_complex_data(data, 'features') or extract_complex_data(data, 'propertyFeatures')
        bedrooms = features.get('beds', 0) if isinstance(features, dict) else 0
        bathrooms = features.get('baths', 0) if isinstance(features, dict) else 0
        carspaces = features.get('parking', 0) if isinstance(features, dict) else 0
        
        # --- 3. THE FIX: EXACT URL HUNTER ---
        image_urls = []
        media_folders = []
        
        def find_media_folders(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() == 'media' and isinstance(v, list):
                        media_folders.append(v)
                    else: find_media_folders(v)
            elif isinstance(obj, list):
                for item in obj: find_media_folders(item)
                    
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
                                # NO MORE CHOPPING. KEEP THE URL INTACT.
                                clean_url = url.replace('\\u002F', '/').replace('\\', '')
                                if clean_url not in image_urls:
                                    image_urls.append(clean_url)

        print(f"✅ [2/3] Data extracted! Found {len(image_urls)} true photos.")
        
        # --- 4. DIRECT DOWNLOAD ---
        pil_images = []
        img_headers = {
            "Referer": "https://www.domain.com.au/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        
        for i, url in enumerate(image_urls[:5]):
            print(f"   -> Downloading high-res photo {i+1}...") 
            try:
                img_response = session.get(url, headers=img_headers, timeout=15.0)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    pil_images.append(img)
                else:
                    print(f"   ❌ CDN Blocked: Status {img_response.status_code}")
            except Exception as e:
                print(f"   ❌ Connection error on photo {i+1}: {e}")

        if not pil_images:
             return {"success": False, "error": "Found the URLs, but CDN download failed. Check terminal logs."}

        print(f"🎉 [3/3] Successfully downloaded {len(pil_images)} photos.")

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
