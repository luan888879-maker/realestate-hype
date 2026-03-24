import cloudscraper
from bs4 import BeautifulSoup

def fetch_property_data(url: str) -> dict:
    """Scrapes a Domain.com.au URL for the main OpenGraph image using a stealth scraper."""
    
    # Create a scraper that mimics a real Windows/Chrome desktop browser
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        # 1. Fetch the webpage (bumped timeout to 15s to account for firewall checks)
        response = scraper.get(url, timeout=15.0)
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
            "error": f"Firewall or Scraper Error: {str(e)}"
        }

if __name__ == "__main__":
    test_link = "https://www.domain.com.au/2-40-wentworth-street-glebe-nsw-2037-16942953"
    print(fetch_property_data(test_link))
