import requests
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
import re
import json

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
    print(f"🚀 [1/3] Triggering ScraperAPI (Cloudflare Bypass)...")
    
    proxy_url = "http://api.scraperapi.com"
    params = {"api_key": scraper_api_key, "url": property_url, "country_code": "au"}
    
    try:
        # 1. Grab raw HTML via ScraperAPI
        response = requests.get(proxy_url, params=params, timeout=45.0)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not next_data_script:
            return {"success": False, "error": "Domain blocked the proxy. Run it again."}
            
        data = json.loads(next_data_script.string)
        
        # 2. Extract Core Data using the Deep Hunter
        address_parts = extract_complex_data(data, 'addressParts')
        address = address_parts.get('displayAddress', 'Unknown Address') if isinstance(address_parts, dict) else 'Unknown Address'
        
        price_details = extract_complex_data(data, 'priceDetails')
        formatted_price = price_details.get('displayPrice', 'Contact Agent') if isinstance(price_details, dict) else 'Contact Agent'
        
        # Safe extraction of price (Defaults to 0 if it says 'Auction' or 'Contact Agent')
        asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
        
        features = extract_complex_data(data, 'features') or extract_complex_data(data, 'propertyFeatures')
        bedrooms = features.get('beds', 0) if isinstance(features, dict) else 0
        bathrooms = features.get('baths', 0) if isinstance(features, dict) else 0
        carspaces = features.get('parking', 0) if isinstance(features, dict) else 0
        
        # 3. THE BRUTE-FORCE IMAGE HUNTER
        # We convert the entire JSON into a massive string and hunt for Domain's specific Image CDNs
        raw_string = json.dumps(data)
        
        # Domain strictly uses rimh2 or bucket-api to host property photos. We grab them all.
        raw_urls = re.findall(r'(https?://(?:rimh2\.domain\.com\.au|bucket-api\.domain\.com\.au)[^\s"\'\\]+)', raw_string)
        
        image_urls = []
        for url in raw_urls:
            # Clean up the JSON escaping and remove size limits to get the raw high-res photo
            clean_url = url.replace('\\u002F', '/').replace('\\', '').split('?')[0].split('-w')[0]
            
            # Filter out agent logos
            if 'profile' not in clean_url.lower() and 'avatar' not in clean_url.lower():
                if clean_url not in image_urls:
                    image_urls.append(clean_url)

        print(f"✅ [2/3] Data extracted! Found {len(image_urls)} unique Domain CDN photos.")
        
        # 4. THE NUCLEAR DOWNLOADER (Proxying the Images)
        pil_images = []
        
        # We don't download from our server. We force ScraperAPI to fetch the images too!
        for i, url in enumerate(image_urls[:5]):
            print(f"   -> Proxying high-res photo {i+1}...") 
            try:
                img_params = {"api_key": scraper_api_key, "url": url, "country_code": "au"}
                # Notice we send it through proxy_url, NOT the raw url
                img_response = requests.get(proxy_url, params=img_params, timeout=25.0)
                
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    pil_images.append(img)
                else:
                    print(f"   ❌ Proxy failed on photo {i+1} (Status {img_response.status_code})")
            except Exception as e:
                print(f"   ❌ Connection error on photo {i+1}: {e}")
                continue

        print(f"🎉 [3/3] Successfully proxied {len(pil_images)} photos into memory.")

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
        return {"success": False, "error": f"ScraperAPI Connection Error: {str(e)}"}
