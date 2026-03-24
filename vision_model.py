import requests
from google import genai
from google.genai import types
from PIL import Image
import json
import io

def analyze_image_url(image_url: str, api_key: str) -> dict:
    try:
        # 1. Fetch image with a fake Browser Header to bypass bot-blockers
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(image_url, headers=headers, timeout=10.0)
        response.raise_for_status() # Forces an error if Unsplash/Domain blocks us
        
        # Load the image into memory
        img = Image.open(io.BytesIO(response.content))
        
        # 2. Call Gemini API
        client = genai.Client(api_key=api_key)
        prompt = 'You are a strict real estate appraiser. Analyze this property photo. Return ONLY a JSON object with: "condition_score" (int 1-10), "needs_cosmetic_renovation" (boolean), and "reasoning" (1 short sentence).'
        
        result = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[img, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        return json.loads(result.text)
        
    except Exception as e:
        # THE BLINDFOLD IS OFF: We inject the exact error into the dashboard!
        return {
            'condition_score': 4,
            'needs_cosmetic_renovation': True,
            'reasoning': f'Mock data activated. ACTUAL ERROR: {str(e)}'
        }
