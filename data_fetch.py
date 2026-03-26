import requests
from bs4 import BeautifulSoup
import json
import re

def extract_from_dict(obj, target_key):
    """Recursively hunts through a complex JSON tree for a specific key."""
    if isinstance(obj, dict):
        if target_key in obj:
            return obj[target_key]
        for k, v in obj.items():
            result = extract_from_dict(v, target_key)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = extract_from_dict(item, target_key)
            if result is not None:
                return result
    return None

def fetch_property_data(property_url: str, scraper_api_key: str) -> dict:
    """Bypasses Cloudflare using ScraperAPI and deep-searches Domain's JSON."""
    
    proxy_url = "https://api.scraperapi.com/"
    params = {
        "api_key": scraper_api_key,
        "url": property_url,
        "premium": "true",
        "country_code": "au" 
    }
    
    try:
        response = requests.get(proxy_url, params=params, timeout=45.0)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Proxy blocked or failed. Status: {response.status_code}"}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Find the massive hidden JSON block
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not next_data_script:
            return {"success": False, "error": "Could not locate Domain's __NEXT_DATA__ payload."}
            
        data = json.loads(next_data_script.string)
        
        # 2. Use the Recursive Hunter to find our data, ignoring the folder structure!
        
        # Address
        address_parts = extract_from_dict(data, 'addressParts')
        address = address_parts.get('displayAddress', 'Unknown Address') if address_parts else 'Unknown Address'
        
        # Price
        price_details = extract_from_dict(data, 'priceDetails')
        formatted_price = price_details.get('displayPrice', 'Price not listed') if price_details else 'Price not listed'
        asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
        
        # Hardware
        features = extract_from_dict(data, 'features') or extract_from_dict(data, 'propertyFeatures')
        bedrooms = features.get('beds', 0) if features else 0
        bathrooms = features.get('baths', 0) if features else 0
        carspaces = features.get('parking', 0) if features else 0
        
        # Images (Domain uses either 'type' or 'category' to label images)
        media = extract_from_dict(data, 'media')
        image_urls = []
        if media and isinstance(media, list):
            image_urls = [m.get('url') for m in media if m.get('type') == 'image' or m.get('category') == 'Image'][:5]
            
        # HTML Fallback: If JSON completely fails to find images, check standard meta tags
        if not image_urls:
            for img in soup.find_all('meta', property='og:image'):
                image_urls.append(img['content'])

        return {
            "success": True,
            "image_urls": image_urls,
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
