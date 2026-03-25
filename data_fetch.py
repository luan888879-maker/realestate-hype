import requests
import re

def fetch_property_data(url: str, client_id: str, client_secret: str) -> dict:
    """Fetches property data using Domain's Official OAuth2 API Flow."""
    
    # 1. Extract the Listing ID from the URL
    try:
        match = re.search(r'-([0-9]+)/?$', url.strip())
        if not match:
            return {"success": False, "error": "Could not extract Listing ID from the URL."}
        listing_id = match.group(1)
    except Exception as e:
        return {"success": False, "error": f"URL Parsing Error: {str(e)}"}

    # --- THE FIX: STEP 2 - OAUTH2 AUTHENTICATION ---
    auth_url = "https://auth.domain.com.au/v1/connect/token"
    auth_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "api_listings_read" # We specifically ask for permission to read listings
    }
    
    try:
        # Ask the security server for a temporary token
        auth_response = requests.post(auth_url, data=auth_data)
        if auth_response.status_code != 200:
             return {"success": False, "error": f"OAuth2 Failed: Domain rejected your Client ID/Secret. Status: {auth_response.status_code}"}
             
        access_token = auth_response.json().get("access_token")
    except Exception as e:
        return {"success": False, "error": f"Domain Security Server Error: {str(e)}"}

    # --- STEP 3: FETCH THE DATA WITH THE BEARER TOKEN ---
    endpoint = f"https://api.domain.com.au/v1/listings/{listing_id}"
    
    # We pass the temporary token as a "Bearer" header
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(endpoint, headers=headers, timeout=10.0)
        
        if response.status_code == 404:
             return {"success": False, "error": "Property not found on Domain. It may be off-market or invalid."}
             
        response.raise_for_status() 
        data = response.json()
        
        # 4. Extract the clean data
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
