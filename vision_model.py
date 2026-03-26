from google import genai
from google.genai import types
import requests
import json
from PIL import Image
from io import BytesIO

def analyze_property_images(image_urls, api_key: str) -> dict:
    """
    Downloads up to 5 property photos, feeds them to Gemini 2.5 as a single context window, 
    and returns a structured JSON condition report using the new google-genai SDK.
    """
    
    # Ensure we are working with a list
    if isinstance(image_urls, str):
        image_urls = [image_urls]
        
    pil_images = []
    
    # 1. Download the images into memory
    for url in image_urls[:5]:
        try:
            response = requests.get(url, timeout=10.0)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                pil_images.append(img)
        except Exception as e:
            print(f"Failed to load an image for AI: {e}")
            continue
            
    if not pil_images:
        return {
            "condition_score": 5, 
            "needs_cosmetic_renovation": True, 
            "reasoning": "AI could not load the images. Defaulting to average condition."
        }

    # 2. Initialize the New SDK Client
    client = genai.Client(api_key=api_key)

    # 3. The System Prompt
    prompt = """
    You are an expert Australian real estate inspector and valuer. 
    Analyze this set of property photos (which may include exterior, kitchen, bathroom, and living areas).
    Evaluate the physical hardware, age, wear-and-tear, and quality of finishes.
    
    Return ONLY a JSON object with this exact structure:
    {
        "condition_score": <integer from 1 to 10, where 1 is an unlivable tear-down and 10 is a brand-new luxury build>,
        "needs_cosmetic_renovation": <boolean true or false>,
        "photos_analyzed": <integer, tell me exactly how many photos were provided to you in this prompt>,
        "reasoning": "<A strict, punchy 2-sentence explanation of why you gave this score based on what you saw in the rooms>"
    }
    """

    try:
        # We pass the text prompt AND the PIL images to the new client
        payload = [prompt] + pil_images
        
        # 4. Generate Content with Gemini 2.5 Flash and strict JSON formatting
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=payload,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # 5. Parse the AI's JSON response
        result = json.loads(response.text)
        return result
        
    except Exception as e:
        return {
            "condition_score": 5, 
            "needs_cosmetic_renovation": True, 
            "reasoning": f"AI Processing Error: {str(e)}"
        }
