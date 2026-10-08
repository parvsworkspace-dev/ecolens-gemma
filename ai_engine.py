import json
from google import genai
from google.genai import types

def classify_item(image, api_key: str):
    client = genai.Client(api_key=api_key)
    prompt = """
    Analyze this item for waste segregation and circular economy reuse.
    Return ONLY a valid JSON object with:
    {
      "item_name": "String",
      "action": "RECYCLE" | "REPAIR" | "REUSE",
      "category": "Electronics" | "Plastic" | "Organic" | "Metal" | "Furniture" | "Paper" | "Other",
      "condition": "Usable" | "Repairable" | "Discard",
      "instructions": "Specific guidance on disposal, repair, or upcycling.",
      "bin_color": "Blue (Dry)" | "Green (Wet)" | "Red (Sanitary/Hazardous)" | "E-Waste"
    }
    """
    response = client.models.generate_content(
        model="gemma-4-26b-a4b-it",
        contents=[image, prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return json.loads(response.text)

if __name__ == "__main__":
    # Provide a dummy API key or load from environment variable
    import os
    api_key = os.environ.get("GEMINI_API_KEY", "YOUR_TEST_API_KEY")

    print("Testing AI Engine...")
    # You can pass a path to a sample image file on the computer for testing
    # image_path = "test_image.jpg"
    # result = classify_item(image_path, api_key)
    # print("Result:", result)

