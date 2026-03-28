import requests
from PIL import Image
from io import BytesIO
from apify_client import ApifyClient
import re

def fetch_property_data(property_url: str, apify_api_key: str) -> dict:
    print(f"🚀 [1/3] Triggering Dedicated Property API (easyapi/domain-com-au-property-scraper)...")
    
    client = ApifyClient(apify_api_key)
    
    # We strictly limit it to 1 item so it doesn't wander off and scrape neighbors
    run_input = {
        "searchUrls": [property_url],
        "maxItems": 1
    }
    
    try:
        run = client.actor("easyapi/domain-com-au-property-scraper").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        if not items:
            return {"success": False, "error": "API returned blank. Domain might have removed the listing."}
            
        data = items[0]
        
        # --- Extract Exact Data ---
        address = data.get('address', 'Unknown Address')
        
        # Handle "Contact Agent" cleanly
        price_raw = str(data.get('price', '0'))
        asking_price = int(re.sub(r'[^\d]', '', price_raw)) if re.sub(r'[^\d]', '', price_raw) else 0
        
        bedrooms = int(data.get('beds', 0))
        bathrooms = int(data.get('baths', 0))
        carspaces = int(data.get('parking', 0))
        
        # Grab the exact high-res image array provided by the API
        image_urls = data.get('images', [])
        
        # Fallback if 'images' is empty but 'media' exists
        if not image_urls and 'media' in data:
            image_urls = [m.get('url') for m in data['media'] if m.get('type') == 'image']
            
        print(f"✅ [2/3] Data extracted! Found {len(image_urls)} photos, {bedrooms} beds, {bathrooms} baths.")
        
        # --- Download Images ---
        pil_images = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.domain.com.au/"
        }
        
        for i, url in enumerate(image_urls[:5]):
            print(f"   -> Downloading high-res photo {i+1}...") 
            try:
                img_response = requests.get(url, headers=headers, timeout=15.0)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    pil_images.append(img)
                else:
                    print(f"   ❌ Blocked by CDN: Status {img_response.status_code}")
            except Exception as e:
                print(f"   ❌ Connection error on photo {i+1}: {e}")

        if not pil_images:
             return {"success": False, "error": "Found image URLs, but Domain's CDN blocked the download."}

        print(f"🎉 [3/3] Successfully downloaded {len(pil_images)} photos.")

        return {
            "success": True,
            "downloaded_images": pil_images,
            "address": address,
            "asking_price": asking_price,
            "formatted_price": price_raw,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "carspaces": carspaces,
            "error": None
        }

    except Exception as e:
        return {"success": False, "error": f"API Connection Error: {str(e)}"}
