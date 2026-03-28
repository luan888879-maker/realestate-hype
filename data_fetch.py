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
        
        # 3. The Surgical Gallery Hunter (No agent headshots, no duplicates)
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

        print(f"✅ [2/3] Data extracted! Found {len(image_urls)} unique photos, {bedrooms} beds, {bathrooms} baths.")
        
        # 4. Download images using Native VIP Headers
        pil_images = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://www.domain.com.au/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        
        for i, url in enumerate(image_urls[:5]):
            print(f"   -> Downloading high-res photo {i+1}...") 
            try:
                img_response = requests.get(url, headers=headers, timeout=15.0)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    pil_images.append(img)
            except Exception:
                continue

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
        return {"success": False, "error": f"ScraperAPI Connection Error: {str(e)}"}
