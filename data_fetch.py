import requests
from bs4 import BeautifulSoup
import json
import re
from PIL import Image
from io import BytesIO

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
    """Bypasses Cloudflare, extracts data, and securely downloads images into memory."""
    proxy_url = "https://api.scraperapi.com/"
    params = {"api_key": scraper_api_key, "url": property_url, "premium": "true", "country_code": "au"}
    
    try:
        # 1. Fetch the main HTML
        print("🚀 [1/3] Proxy initiated: Attempting to bypass Cloudflare for main HTML...")
        response = requests.get(proxy_url, params=params, timeout=45.0)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Proxy blocked. Status: {response.status_code}"}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not next_data_script:
            return {"success": False, "error": "Could not locate Domain's payload."}
            
        raw_text = next_data_script.string
        
        # 2. Extract standard JSON data
        data = json.loads(raw_text)
        
        address_parts = extract_complex_data(data, 'addressParts')
        address = address_parts.get('displayAddress', 'Unknown Address') if isinstance(address_parts, dict) else 'Unknown Address'
        
        price_details = extract_complex_data(data, 'priceDetails')
        formatted_price = price_details.get('displayPrice', 'Price not listed') if isinstance(price_details, dict) else 'Price not listed'
        asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
        
        features = extract_complex_data(data, 'features') or extract_complex_data(data, 'propertyFeatures')
        bedrooms = features.get('beds', 0) if isinstance(features, dict) else 0
        bathrooms = features.get('baths', 0) if isinstance(features, dict) else 0
        carspaces = features.get('parking', 0) if isinstance(features, dict) else 0

       # 3. Extract Image URLs (The Deep-Dive Dictionary Method)
        raw_urls = set() # Use a set to automatically prevent duplicates
        
        def hunt_for_urls(obj):
            """Recursively hunts through every folder of the JSON for image links."""
            if isinstance(obj, dict):
                for v in obj.values():
                    hunt_for_urls(v)
            elif isinstance(obj, list):
                for item in obj:
                    hunt_for_urls(item)
            elif isinstance(obj, str):
                lower_str = obj.lower()
                # If it is a web link and an image...
                if lower_str.startswith('http') and any(ext in lower_str for ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif']):
                    # And it isn't agent junk...
                    if 'profile' not in lower_str and 'avatar' not in lower_str and 'logo' not in lower_str:
                        raw_urls.add(obj)
        
        # Launch the hunter into the clean Python data
        hunt_for_urls(data) 
        image_urls = list(raw_urls)

        print(f"✅ [2/3] HTML bypassed! Found {len(image_urls)} image links. Starting secure downloads...")

        # 4. Securely download the images into memory
        pil_images = []
        for i, url in enumerate(image_urls[:5]):
            print(f"   -> Downloading photo {i+1}...") # Heartbeat log
            img_params = {"api_key": scraper_api_key, "url": url, "country_code": "au"}
            try:
                img_response = requests.get(proxy_url, params=img_params, timeout=30.0)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    pil_images.append(img)
                else:
                    print(f"   ❌ Proxy failed on photo {i+1} with status: {img_response.status_code}")
            except Exception as e:
                print(f"   ❌ Connection error on photo {i+1}: {e}")
                continue

        print(f"🎉 [3/3] Successfully downloaded {len(pil_images)} photos into memory. Handing off to AI.")

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
