import requests
from PIL import Image
from io import BytesIO
from apify_client import ApifyClient
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

def fetch_property_data(property_url: str, apify_api_key: str) -> dict:
    print(f"🚀 [1/3] Triggering Free Apify Puppeteer Browser (Cloudflare Bypass)...")
    
    # 1. Initialize Apify
    client = ApifyClient(apify_api_key)
    
    # 2. Run the Free Puppeteer Scraper with a custom Javascript injection
    js_code = """
    async function pageFunction(context) { 
        const jsonStr = await context.page.evaluate(() => { 
            const el = document.getElementById('__NEXT_DATA__'); 
            return el ? el.innerText : '{}'; 
        }); 
        return JSON.parse(jsonStr); 
    }
    """
    
    run_input = {
        "startUrls": [{"url": property_url}],
        "pageFunction": js_code,
        "proxyConfiguration": {"useApifyProxy": True}
    }
    
    try:
        run = client.actor("apify/puppeteer-scraper").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        if not items or not items[0]:
            return {"success": False, "error": "Apify browser blocked or Domain JSON not found."}
            
        data = items[0] 
        
        # --- 2. EXTRACT CORE PROPERTY DATA ---
        address_parts = extract_complex_data(data, 'addressParts')
        address = address_parts.get('displayAddress', 'Unknown Address') if isinstance(address_parts, dict) else 'Unknown Address'
        
        price_details = extract_complex_data(data, 'priceDetails')
        formatted_price = price_details.get('displayPrice', 'Price not listed') if isinstance(price_details, dict) else 'Price not listed'
        asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
        
        features = extract_complex_data(data, 'features') or extract_complex_data(data, 'propertyFeatures')
        bedrooms = features.get('beds', 0) if isinstance(features, dict) else 0
        bathrooms = features.get('baths', 0) if isinstance(features, dict) else 0
        carspaces = features.get('parking', 0) if isinstance(features, dict) else 0

        # --- 3. THE SURGICAL GALLERY HUNTER ---
        image_urls = []
        
        # We find every 'media' folder in the JSON data
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
        
        # Extract the high-res URL directly from the official gallery objects
        for folder in media_folders:
            for item in folder:
                if isinstance(item, dict):
                    # Domain strictly labels property photos as 'image'
                    item_type = item.get('type', '').lower()
                    if item_type in ['image', 'photograph', 'photo']:
                        url = item.get('url')
                        if url and url.startswith('http'):
                            # Double-check we aren't grabbing floorplans
                            lower_url = url.lower()
                            if 'floorplan' not in lower_url and 'profile' not in lower_url:
                                # Clean the URL and ensure no duplicates
                                clean_url = url.split('?')[0]
                                if clean_url not in image_urls:
                                    image_urls.append(clean_url)

        print(f"✅ [2/3] Data extracted! Found {len(image_urls)} true gallery photos, {bedrooms} beds, {bathrooms} baths.")
        
        # --- 4. DOWNLOAD IMAGES WITH VIP HEADERS ---
        pil_images = []
        
        # Domain's CDN blocks raw Python scripts. We must pretend to be a Mac user clicking from Domain.com.au
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://www.domain.com.au/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        
        for i, url in enumerate(image_urls[:5]):
            print(f"   -> Downloading high-res photo {i+1}...") 
            try:
                img_response = requests.get(url, headers=headers, timeout=20.0)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    pil_images.append(img)
                else:
                    print(f"   ❌ Blocked by CDN: Status {img_response.status_code}")
            except Exception as e:
                print(f"   ❌ Connection error on photo {i+1}: {e}")
                continue

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
        return {"success": False, "error": f"Apify Connection Error: {str(e)}"}
