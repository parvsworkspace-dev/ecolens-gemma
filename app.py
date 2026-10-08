import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# 1. Page Configuration
st.set_page_config(page_title="EcoLens - Gemma 4", page_icon="♻️", layout="centered")

# 2. Sidebar setup
with st.sidebar:
    st.title("🌿 EcoLens")
    st.markdown("**Hackathon Track:** Open-Source AI Project")
    st.markdown("**Team:** Codex")
    st.markdown("**Model:** `gemma-4-26b-a4b-it`")
    st.markdown("**License:** Apache 2.0 Open-Weight")
    st.divider()
    api_key = st.text_input("Gemini API Key", type="password")
    st.markdown("[Get API key from Google AI Studio](https://aistudio.google.com)")

# 3. Main Interface & Camera Capture
st.title("♻️ EcoLens: Smart Waste Classifier")
st.write("Scan waste or recyclables with your camera to detect proper disposal steps.")

camera_photo = st.camera_input("Point camera at a waste item")

if camera_photo:
    img = Image.open(camera_photo)
    st.image(img, caption="Captured Snapshot", width=400)

    if not api_key:
        st.warning("⚠️️ Enter your Gemini API Key in the left sidebar to analyze.")
    else:
        with st.spinner("Analyzing material properties with Gemma 4..."):
            try:
                # Initialize Google GenAI client
                client = genai.Client(api_key=api_key)

                system_instruction = (
                    "You are an expert waste and recycling auditor. "
                    "Analyze the object in the image and provide clear, structured disposal guidance."
                )

                prompt = """
                Analyze this item for waste sorting and recycling. Format the output cleanly:
                
                ### 📦 Object Identified
                - **Item:** [Name of the object]
                - **Primary Material:** [e.g., PET Plastic #1, Cardboard, Aluminum, Organic, Electronic]
                
                ### 🏷️ Disposal Protocol
                - **Category:** [Recyclable / Compost & Organic / Hazardous & E-Waste / Landfill]
                - **Recommended Bin Color:** [Blue / Green / Red / Black]
                - **Disposal Action:** [1 concise step, e.g., rinse thoroughly, remove cap, keep dry]
                
                ### 💡 Upcycling & Reuse Idea
                - [1 practical tip to reuse or repurpose this object]
                """

                # Gemma 4 call with minimal thinking for rapid live response
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    thinking_config=types.ThinkingConfig(thinking_level="minimal")
                )

                response = client.models.generate_content(
                    model="gemma-4-26b-a4b-it",
                    contents=[img, prompt],
                    config=config
                )

                st.success("✅ Analysis Complete!")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Inference error: {e}")