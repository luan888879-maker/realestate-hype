import requests
from bs4 import BeautifulSoup
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

def fetch_property_data(property_url: str, scraper_api_key: str) -> dict:
    """Bypasses Cloudflare using ScraperAPI and extracts Domain's hidden data."""
    
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
        
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not next_data_script:
            return {"success": False, "error": "Could not locate Domain's __NEXT_DATA__ payload."}
            
        raw_text = next_data_script.string
        
        # --- THE BRUTE-FORCE IMAGE EXTRACTOR ---
        # Uses Regex to rip every image link directly from the raw code block
        all_links = re.findall(r'(https?://[^"\'\\]+\.(?:jpg|jpeg|png))', raw_text, re.IGNORECASE)
        
        image_urls = []
        for link in all_links:
            # Filter out tracking pixels and agent profile pictures
            if link not in image_urls and 'domain' in link.lower() and 'profile' not in link.lower() and 'avatars' not in link.lower():
                image_urls.append(link)
                
        # --- THE DATA EXTRACTOR ---
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

        return {
            "success": True,
            "image_urls": image_urls[:5], # Send the top 5 highest quality photos
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
