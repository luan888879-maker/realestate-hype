from google import genai
from google.genai import types
import json

# It now expects physical image objects, not URLs, and doesn't need the scraper key!
def analyze_property_images(pil_images, api_key: str) -> dict:
    
    if not pil_images:
        return {
            "condition_score": 5, 
            "needs_cosmetic_renovation": True, 
            "photos_analyzed": 0,
            "reasoning": "No images were provided to the AI. Defaulting to average condition."
        }

    client = genai.Client(api_key=api_key)

    prompt = """
    You are an expert Australian real estate inspector and valuer. 
    Analyze this set of property photos.
    
    Return ONLY a JSON object with this exact structure:
    {
        "condition_score": <integer from 1 to 10>,
        "needs_cosmetic_renovation": <boolean true or false>,
        "photos_analyzed": <integer, tell me exactly how many photos were provided to you>,
        "reasoning": "<A strict, punchy 2-sentence explanation of why you gave this score>"
    }
    """

    try:
        payload = [prompt] + pil_images
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=payload,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        
        if "photos_analyzed" not in result:
            result["photos_analyzed"] = len(pil_images)
            
        return result
        
    except Exception as e:
        return {
            "condition_score": 5, 
            "needs_cosmetic_renovation": True, 
            "photos_analyzed": len(pil_images),
            "reasoning": f"AI Processing Error: {str(e)}"
        }
