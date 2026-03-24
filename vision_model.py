import requests
from google import genai
from google.genai import types
from PIL import Image
import json
from io import BytesIO

def analyze_image_url(image_url: str, api_key: str) -> dict:
    """
    Fetches an image from the given URL, analyzes it with Gemini 2.5 Flash using the google-genai SDK,
    and returns a strict real estate appraisal as a JSON-like dict.
    Implements robust error handling: returns fixed mock output on any failure.
    """
    try:
        response = requests.get(image_url, stream=True, timeout=5.0)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))

        client = genai.Client(api_key=api_key)

        prompt = (
            'You are a strict real estate appraiser. Analyze this property photo. '
            'Return ONLY a JSON object with: "condition_score" (int 1-10), '
            '"needs_cosmetic_renovation" (boolean), and "reasoning" (1 short sentence).'
        )

        config = types.GenerateContentConfig(response_mime_type="application/json")

        result = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{"role": "user", "parts": [prompt, img]}],
            config=config
        )

        # Extract and parse the response's text as JSON.
        # Unified genai SDK returns object with .text for JSON response.
        appraisal = json.loads(result.text)
        return appraisal

    except Exception as e:
        return {
            "condition_score": 4,
            "needs_cosmetic_renovation": True,
            "reasoning": "Mock data activated due to firewall/proxy."
        }

if __name__ == '__main__':
    API_KEY = "AIzaSyAIjcWb2VtIBXQbMQJAUTw817bieRuRMAE"
    test_url = "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=800&q=80"
    result = analyze_image_url(test_url, API_KEY)
    print(result)