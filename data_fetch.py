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
    # This specifically targets the exact house URL and steals the hidden JSON data
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
        
        # 3. YESTERDAY'S SURGICAL HUNTER (Adapted for the clean Apify pull)
        address_parts = extract_complex_data(data, 'addressParts')
        address = address_parts.get('displayAddress', 'Unknown Address') if isinstance(address_parts, dict) else 'Unknown Address'
        
        price_details = extract_complex_data(data, 'priceDetails')
        formatted_price = price_details.get('displayPrice', 'Price not listed') if isinstance(price_details, dict) else 'Price not listed'
        asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
        
        features = extract_complex_data(data, 'features') or extract_complex_data(data, 'propertyFeatures')
        bedrooms = features.get('beds', 0) if isinstance(features, dict) else 0
        bathrooms = features.get('baths', 0) if isinstance(features, dict) else 0
        carspaces = features.get('parking', 0) if isinstance(features, dict) else 0

        # The Surgical Image Hunter (Ignoring Agent Profiles)
        image_urls = []
        media_list = extract_complex_data(data, 'media')
        
        if media_list and isinstance(media_list, list):
            for item in media_list:
                if item.get('type') == 'IMAGE':
                    url = item.get('url')
                    if url and url.startswith('http'):
                        clean_url = url.replace('\\', '')
                        if clean_url not in image_urls:
                            image_urls.append(clean_url)

        # Fallback regex just in case Domain changes the 'media' folder
        if not image_urls:
            raw_text = json.dumps(data)
            found = re.findall(r'(https?://[^"\'\\]+property[^"\'\\]+\.(?:jpg|jpeg|webp|avif))', raw_text, re.IGNORECASE)
            image_urls = list(dict.fromkeys(found))

        print(f"✅ [2/3] HTML bypassed! Found {len(image_urls)} property photos, {bedrooms} beds, {bathrooms} baths.")
        
        # 4. Download images into RAM
        pil_images = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        for i, url in enumerate(image_urls[:5]):
            print(f"   -> Downloading high-res photo {i+1}...") 
            try:
                img_response = requests.get(url, headers=headers, timeout=20.0)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    pil_images.append(img)
            except Exception as e:
                print(f"   ❌ Failed to download photo {i+1}: {e}")
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
