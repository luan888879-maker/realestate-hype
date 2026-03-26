import requests
from bs4 import BeautifulSoup
import json
import re

def fetch_property_data(property_url: str, scraper_api_key: str) -> dict:
    """Bypasses Cloudflare using ScraperAPI and extracts Domain's hidden JSON data."""
    
    # Send the URL to ScraperAPI, which routes it through a residential proxy
    proxy_url = "https://api.scraperapi.com/"
    params = {
        "api_key": scraper_api_key,
        "url": property_url,
        "premium": "true", # Uses premium residential IPs to beat Cloudflare
        "country_code": "au" # Routes through Australia
    }
    
    try:
        response = requests.get(proxy_url, params=params, timeout=30.0)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Proxy blocked or failed. Status: {response.status_code}"}
            
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # DOMAIN SECRET: All data is stored in a massive hidden script tag called __NEXT_DATA__
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not next_data_script:
            return {"success": False, "error": "Could not locate Domain's data payload. They may have updated their site."}
            
        data = json.loads(next_data_script.string)
        
        # Navigate the JSON maze to find the property listing details
        try:
            # Note: Domain's JSON structure is deep, this hunts for the core listing object
            props = data.get('props', {}).get('pageProps', {}).get('componentProps', {})
            listing = props.get('listing', {})
            
            # Extract Address
            address = listing.get('addressParts', {}).get('displayAddress', 'Unknown Address')
            
            # Extract Price
            price_details = listing.get('priceDetails', {})
            formatted_price = price_details.get('displayPrice', 'Price not listed')
            # Strip text to get raw integer (e.g., "$1,500,000" -> 1500000)
            asking_price = int(re.sub(r'[^\d]', '', formatted_price)) if re.sub(r'[^\d]', '', formatted_price) else 0
            
            # Extract Hardware
            features = listing.get('features', {})
            bedrooms = features.get('beds', 0)
            bathrooms = features.get('baths', 0)
            carspaces = features.get('parking', 0)
            
            # Extract Images
            media = listing.get('media', [])
            image_urls = [m.get('url') for m in media if m.get('type') == 'image'][:5]
            
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
            
        except AttributeError:
             return {"success": False, "error": "Data structure changed. Could not parse listing details."}

    except Exception as e:
        return {"success": False, "error": f"Connection Error: {str(e)}"}
