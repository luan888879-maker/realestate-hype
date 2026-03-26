import google.generativeai as genai
import requests
import json
from PIL import Image
from io import BytesIO

def analyze_property_images(image_urls, api_key: str) -> dict:
    """
    Downloads up to 5 property photos, feeds them to Gemini as a single context window, 
    and returns a structured JSON condition report.
    """
    
    # 1. Authenticate with Google
    genai.configure(api_key=api_key)
    
    # Ensure we are working with a list, even if a single string gets passed by accident
    if isinstance(image_urls, str):
        image_urls = [image_urls]
        
    pil_images = []
    
    # 2. Download the images into memory (Max 5 to keep it fast and cost-effective)
    for url in image_urls[:5]:
        try:
            response = requests.get(url, timeout=10.0)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                pil_images.append(img)
        except Exception as e:
            print(f"Failed to load an image for AI: {e}")
            continue
            
    # Safety fallback if the scraper found URLs but the images are broken
    if not pil_images:
        return {
            "condition_score": 5, 
            "needs_cosmetic_renovation": True, 
            "reasoning": "AI could not load the images. Defaulting to average condition."
        }

    # 3. Initialize the Multimodal AI
    # We use gemini-1.5-flash because it is blazingly fast and excellent at visual reasoning
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config={"response_mime_type": "application/json"} # Forces a strict JSON output!
    )

    # 4. The System Prompt
    prompt = """
    You are an expert Australian real estate inspector and valuer. 
    Analyze this set of property photos (which may include exterior, kitchen, bathroom, and living areas).
    Evaluate the physical hardware, age, wear-and-tear, and quality of finishes.
    
    Return ONLY a JSON object with this exact structure:
    {
        "condition_score": <integer from 1 to 10, where 1 is an unlivable tear-down and 10 is a brand-new luxury build>,
        "needs_cosmetic_renovation": <boolean true or false>,
        "reasoning": "<A strict, punchy 2-sentence explanation of why you gave this score based on what you saw in the rooms>"
    }
    """

    try:
        # We pass the text prompt AND the entire list of images in one massive payload
        payload = [prompt] + pil_images
        response = model.generate_content(payload)
        
        # 5. Parse the AI's JSON response
        result = json.loads(response.text)
        return result
        
    except Exception as e:
        return {
            "condition_score": 5, 
            "needs_cosmetic_renovation": True, 
            "reasoning": f"AI Processing Error: {str(e)}"
        }
