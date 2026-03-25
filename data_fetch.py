import requests
import re

def fetch_property_data(url: str, domain_api_key: str) -> dict:
    """Fetches structured property data using the official Domain API."""
    
    # 1. Extract the Listing ID from the end of the URL
    try:
        match = re.search(r'-([0-9]+)/?$', url.strip())
        if not match:
            return {"success": False, "error": "Could not extract Listing ID from the URL. Please ensure it is a valid Domain listing link."}
        listing_id = match.group(1)
    except Exception as e:
        return {"success": False, "error": f"URL Parsing Error: {str(e)}"}

    # 2. Call the Official Domain API
    endpoint = f"https://api.domain.com.au/v1/listings/{listing_id}"
    headers = {"X-Api-Key": domain_api_key}
    
    try:
        response = requests.get(endpoint, headers=headers, timeout=10.0)
        
        # If Domain rejects the key or the ID is bad, catch it cleanly
        if response.status_code == 401 or response.status_code == 403:
             return {"success": False, "error": "Domain API Key rejected (Unauthorized). Check your Streamlit Secrets."}
        elif response.status_code == 404:
             return {"success": False, "error": "Property not found on Domain's API. It may be off-market."}
             
        response.raise_for_status() 
        data = response.json()
        
        # 3. Extract the clean data
        media = data.get("media", [])
        image_urls = [m.get("url") for m in media if m.get("category") == "Image"][:5]
        
        address_obj = data.get("addressParts", {})
        address = address_obj.get("displayAddress", "Address not found")
        
        price_details = data.get("priceDetails", {})
        formatted_price = price_details.get("displayPrice", "Price not listed")
        asking_price = price_details.get("price", 0) 
        
        return {
            "success": True,
            "image_urls": image_urls,
            "address": address,
            "asking_price": asking_price,
            "formatted_price": formatted_price,
            "bedrooms": data.get("bedrooms", 0),
            "bathrooms": data.get("bathrooms", 0),
            "carspaces": data.get("carspaces", 0),
            "error": None
        }
        
    except Exception as e:
        return {"success": False, "error": f"API Connection Error: {str(e)}"}
