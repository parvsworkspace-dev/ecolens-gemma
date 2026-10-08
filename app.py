import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# ----------------- MODULAR IMPORTS (WITH FALLBACKS) -----------------
try:
    from secondlife_map import render_secondlife_map
except ImportError:
    render_secondlife_map = None

try:
    from impact import render_giveaway_tab, render_impact_tab
except ImportError:
    render_giveaway_tab = None
    render_impact_tab = None

# ----------------- STREAMLIT PAGE CONFIG -----------------
st.set_page_config(
    page_title="EcoLens: SecondLife Edition",
    page_icon="🌱",
    layout="wide"
)

# ----------------- GLOBAL SESSION STATE -----------------
if "ai_scanned_item" not in st.session_state:
    st.session_state.ai_scanned_item = ""
if "ai_scanned_category" not in st.session_state:
    st.session_state.ai_scanned_category = "Furniture"

# ----------------- SIDEBAR CONFIGURATION -----------------
with st.sidebar:
    st.markdown("### 🌿 EcoLens")
    st.caption("Hackathon Track: Open-Source AI Project")
    st.markdown("**Team:** Codex")
    st.markdown("**Model:** `gemma-4-26b-a4b-it`")
    st.markdown("**License:** Apache 2.0 Open-Weight")
    st.divider()
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
    st.caption("[Get API key from Google AI Studio](https://aistudio.google.com/)")

st.title("🌱 EcoLens: SecondLife Edition")
st.caption("AI-Driven Waste Segregation & Community Circular Economy Pipeline")

# ----------------- TAB NAVIGATION -----------------
tab_scan, tab_map, tab_give, tab_impact = st.tabs([
    "📸 EcoLens AI Scanner",
    "🗺️ SecondLife Map",
    "🎁 Give Away / Rehome",
    "📊 Community Impact"
])

# ==============================================================================
# TAB 1: ECOLENS AI SCANNER (GEMMA 4 MULTIMODAL CLASSIFIER)
# ==============================================================================
with tab_scan:
    st.subheader("Visual Waste & Usability Classification")
    st.write("Scan or upload any unwanted item to receive disposal instructions, repair protocols, or rehoming pathways.")

    col_cam, col_upload = st.columns(2)
    with col_cam:
        img_camera = st.camera_input("Capture item with camera")
    with col_upload:
        img_upload = st.file_uploader("Or upload item image", type=["jpg", "jpeg", "png"])

    active_image_file = img_camera or img_upload

    if active_image_file:
        img = Image.open(active_image_file)
        st.image(img, caption="Captured Snapshot", width=340)

        if st.button("🔍 Analyze with Gemma 4", type="primary", use_container_width=True):
            if not api_key:
                st.error("Please enter your Gemini API Key in the sidebar to run inference.")
            else:
                with st.spinner("Classifying material composition and circular potential with Gemma 4..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        
                        system_instruction = (
                            "You are EcoLens, an expert circular economy and waste segregation AI assistant. "
                            "Analyze the provided image of an object and output structured, actionable markdown containing:\n"
                            "### Object Identified\n"
                            "- **Item**: Exact name of item\n"
                            "- **Primary Material**: Composition (e.g., Plastic PVC/PET, E-waste, Wood, Metal)\n\n"
                            "### Disposal Protocol\n"
                            "- **Category**: (Dry Waste / Wet Waste / Hazardous & E-Waste / Landfill / Reusable)\n"
                            "- **Recommended Bin Color**: (Blue for dry, Green for wet, Red for e-waste/hazardous, Black for landfill)\n"
                            "- **Disposal Action**: Specific steps to dispose safely or separate components\n\n"
                            "### Upcycling & Reuse Idea\n"
                            "- A practical way to repair, repurpose, or donate this item locally."
                        )

                        config = types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            thinking_config=types.ThinkingConfig(thinking_level="minimal")
                        )

                        prompt = (
                            "Analyze this item. Identify the object, materials, correct segregation bin/protocol, "
                            "and suggest whether it can be reused, repaired, or donated."
                        )

                        response = client.models.generate_content(
                            model="gemma-4-26b-a4b-it",
                            contents=[img, prompt],
                            config=config
                        )

                        st.success("✅ Analysis Complete!")
                        st.markdown(response.text)

                        # Auto-extract item keywords for seamless pre-filling in Linz's tab
                        resp_text_lower = response.text.lower()
                        if "electronic" in resp_text_lower or "e-waste" in resp_text_lower:
                            st.session_state.ai_scanned_category = "Electronics"
                        elif "plastic" in resp_text_lower:
                            st.session_state.ai_scanned_category = "Plastic"
                        elif "metal" in resp_text_lower:
                            st.session_state.ai_scanned_category = "Metal"
                        elif "paper" in resp_text_lower or "book" in resp_text_lower or "cardboard" in resp_text_lower:
                            st.session_state.ai_scanned_category = "Paper / Books"
                        elif "furniture" in resp_text_lower or "wood" in resp_text_lower:
                            st.session_state.ai_scanned_category = "Furniture"
                        else:
                            st.session_state.ai_scanned_category = "Other"

                        st.session_state.ai_scanned_item = "Scanned Item"
                        st.info("💡 Would you like to donate or list this item? Check out the **🎁 Give Away / Rehome** tab!")

                    except Exception as e:
                        st.error(f"Inference failed: {e}")

# ==============================================================================
# TAB 2: SECOND LIFE COMMUNITY MAP (SHARATH'S MODULE)
# ==============================================================================
with tab_map:
    if render_secondlife_map:
        render_secondlife_map()
    else:
        st.subheader("🗺️ SecondLife Community Map")
        st.warning("⚠️ `secondlife_map.py` could not be loaded. Ensure `secondlife_map.py` exists in your project directory.")

# ==============================================================================
# TAB 3: GIVE AWAY / REHOME FORM (LINZ'S MODULE)
# ==============================================================================
with tab_give:
    if render_giveaway_tab:
        render_giveaway_tab()
    else:
        st.subheader("🎁 List an Item on SecondLife Map")
        st.warning("⚠️ `impact.py` could not be loaded. Ensure `impact.py` exists in your project directory.")

# ==============================================================================
# TAB 4: COMMUNITY CIRCULAR IMPACT (LINZ'S MODULE)
# ==============================================================================
with tab_impact:
    if render_impact_tab:
        render_impact_tab()
    else:
        st.subheader("📊 Community Circular Impact Dashboard")
        st.warning("⚠️ `impact.py` could not be loaded. Ensure `impact.py` exists in your project directory.")