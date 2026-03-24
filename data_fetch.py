import cloudscraper
from bs4 import BeautifulSoup
import re

def fetch_property_data(url: str) -> dict:
    """Scrapes Domain for up to 5 images, address, and asking price with robust error handling."""
    
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    
    try:
        # 1. Fetch the webpage
        response = scraper.get(url, timeout=15.0)
        response.raise_for_status() # This forces an error if we get a 403 Forbidden or 404 Not Found
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Grab an Array of Images (The Gallery)
        image_urls = []
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_urls.append(og_image.get('content'))
            
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and 'http' in src and ('domain' in src or 'bucket' in src) and 'size=' not in src:
                if src not in image_urls:
                    image_urls.append(src)
                    
        target_images = image_urls[:5]

        # 3. Grab the Address safely
        address = "Address not found"
        try:
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                address = og_title.get('content').split('-')[0].strip()
        except Exception:
            pass # Keep default "Address not found" if parsing fails

        # 4. Hunt for the Price using Regex safely
        asking_price = 0
        price_text = "Price not listed"
        try:
            price_match = re.search(r'\$[0-9]{1,3}(?:,[0-9]{3})*', soup.text)
            if price_match:
                price_text = price_match.group()
                clean_num = re.sub(r'[^\d]', '', price_text)
                if clean_num:
                    asking_price = int(clean_num)
        except Exception:
            pass # Keep default 0 and "Price not listed" if regex fails

        # 5. Return structured data
        if len(target_images) == 0:
            return {
                "success": False,
                "error": "Page loaded successfully, but no property images could be found."
            }

        return {
            "success": True,
            "image_urls": target_images,
            "address": address,
            "asking_price": asking_price,
            "formatted_price": price_text,
            "error": None
        }
        
    except Exception as e:
        # This catches timeouts, local proxy blocks, and Domain WAF blocks
        return {
            "success": False,
            "image_urls": [],
            "address": "Unknown",
            "asking_price": 0,
            "formatted_price": "Unknown",
            "error": f"Network or Scraper Error: {str(e)}"
        }

# --- Quick Local Workbench Test ---
if __name__ == "__main__":
    test_link = "https://www.domain.com.au/2-40-wentworth-street-glebe-nsw-2037-16942953"
    print(f"Testing URL: {test_link}\n")
    
    result = fetch_property_data(test_link)
    
    # THE FIX: We explicitly check for success and print the actual error if it fails!
    if result.get("success"):
        print("✅ SCRAPE SUCCESSFUL\n")
        print(f"Address: {result.get('address')}")
        print(f"Price: {result.get('formatted_price')} (Integer value: {result.get('asking_price')})")
        print(f"Images Found: {len(result.get('image_urls', []))}")
        for idx, img in enumerate(result.get('image_urls', [])):
            print(f"  Photo {idx + 1}: {img}")
    else:
        print("❌ SCRAPE FAILED\n")
        print(f"Error Details: {result.get('error')}")
