import requests
from PIL import Image
from io import BytesIO
from apify_client import ApifyClient
import re

def extract_value(data_dict, possible_keys, default=0):
    """Hunts the Apify dictionary for variations of a key (e.g., 'beds', 'bedrooms')."""
    if not isinstance(data_dict, dict):
        return default
        
    for key, value in data_dict.items():
        if key.lower() in possible_keys and value is not None:
            return value
        if isinstance(value, dict):
            result = extract_value(value, possible_keys, default)
            if result != default:
                return result
    return default

def fetch_property_data(property_url: str, apify_api_key: str) -> dict:
    print(f"🚀 [1/3] Triggering Apify Actor (fatihtahta/domain-com-au-scraper)...")
    
    # 1. Initialize Apify
    client = ApifyClient(apify_api_key)
    
    # 2. Run the Fatih Tahta Actor
    run_input = {
        "startUrls": [{"url": property_url}]
    }
    
    try:
        run = client.actor("fatihtahta/domain-com-au-scraper").call(run_input=run_input)
        
        # 3. Grab the property result from the dataset
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        if not items:
            return {"success": False, "error": "Apify ran successfully, but returned no property data. Check the URL."}
            
        property_data = items[0]
        
        # 4. Extract the clean data (Our Data Hunter does the heavy lifting)
        address = extract_value(property_data, ['address', 'displayaddress', 'streetaddress'], "Unknown Address")
        price_str = str(extract_value(property_data, ['price', 'displayprice'], "Price not listed"))
        
        # Clean the price string to get raw numbers
        asking_price = int(re.sub(r'[^\d]', '', price_str)) if re.sub(r'[^\d]', '', price_str) else 0
        
        bedrooms = int(extract_value(property_data, ['beds', 'bedrooms', 'bedroom'], 0))
        bathrooms = int(extract_value(property_data, ['baths', 'bathrooms', 'bathroom'], 0))
        carspaces = int(extract_value(property_data, ['cars', 'carspaces', 'parking'], 0))
        
        # Hunt for the image list
        image_urls = extract_value(property_data, ['images', 'photos', 'media', 'imageurls'], [])
        
        # Clean up the image URLs if they are buried in dictionaries
        clean_urls = []
        if isinstance(image_urls, list):
            for img in image_urls:
                if isinstance(img, str) and img.startswith('http'):
                    clean_urls.append(img)
                elif isinstance(img, dict) and 'url' in img and img['url'].startswith('http'):
                    clean_urls.append(img['url'])

        # Remove duplicates while preserving order
        clean_urls = list(dict.fromkeys(clean_urls))

        print(f"✅ [2/3] Apify extraction complete! Found {len(clean_urls)} photos, {bedrooms} beds, {bathrooms} baths.")
        
        # 5. Download up to 5 images into memory
        pil_images = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        for i, url in enumerate(clean_urls[:5]):
            print(f"   -> Downloading high-res photo {i+1}...") 
            try:
                img_response = requests.get(url, headers=headers, timeout=15.0)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    pil_images.append(img)
                else:
                    print(f"   ❌ Failed to download photo {i+1} (Status {img_response.status_code})")
            except Exception as e:
                print(f"   ❌ Connection error on photo {i+1}: {e}")
                continue

        print(f"🎉 [3/3] Successfully downloaded {len(pil_images)} photos into memory. Handing off to AI.")

        return {
            "success": True,
            "downloaded_images": pil_images,
            "address": address,
            "asking_price": asking_price,
            "formatted_price": price_str,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "carspaces": carspaces,
            "error": None
        }

    except Exception as e:
        return {"success": False, "error": f"Apify Connection Error: {str(e)}"}
