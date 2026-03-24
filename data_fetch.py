import requests
from bs4 import BeautifulSoup

def fetch_property_data(url: str) -> dict:
    """Scrapes a Domain.com.au URL for the main OpenGraph image."""
    
    # We disguise our bot as a standard Mac/Chrome web browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # 1. Fetch the webpage
        response = requests.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        
        # 2. Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. Hunt for the main property image (og:image meta tag)
        image_url = None
        og_image = soup.find('meta', property='og:image')
        
        if og_image and og_image.get('content'):
            image_url = og_image.get('content')
            
        return {
            "success": True if image_url else False,
            "image_url": image_url,
            "error": "Could not find a valid property image on that page." if not image_url else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "image_url": None,
            "error": f"Network or Scraper Error: {str(e)}"
        }

# --- Quick Local Workbench Test ---
if __name__ == "__main__":
    # Feel free to test this with a real Domain link!
    test_link = "https://www.domain.com.au/2-40-wentworth-street-glebe-nsw-2037-16942953"
    print(fetch_property_data(test_link))
