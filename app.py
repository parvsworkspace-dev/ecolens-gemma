import streamlit as st
from PIL import Image
import os
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
if "camera_key" not in st.session_state:
    st.session_state.camera_key = 0
if "ai_analysis_result" not in st.session_state:
    st.session_state.ai_analysis_result = None
if "ai_scanned_item" not in st.session_state:
    st.session_state.ai_scanned_item = ""
if "ai_scanned_category" not in st.session_state:
    st.session_state.ai_scanned_category = "Other"

# ----------------- AUTOMATIC API KEY DETECTION -----------------
auto_detected_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        auto_detected_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not auto_detected_key:
    auto_detected_key = os.environ.get("GEMINI_API_KEY", "")

# ----------------- SIDEBAR CONFIGURATION -----------------
with st.sidebar:
    st.markdown("### 🌿 EcoLens")
    st.caption("Hackathon Track: Open-Source AI Project")
    st.markdown("**Team:** Codex")
    st.markdown("**Model:** `gemma-4-26b-a4b-it`")
    st.markdown("**License:** Apache 2.0 Open-Weight")
    st.divider()

    # If secret is detected, prefill it; otherwise prompt the user
    if auto_detected_key:
        api_key_input = st.text_input(
            "Gemini API Key",
            value=auto_detected_key,
            type="password",
            help="Pre-configured via Streamlit Secrets."
        )
        st.caption("🟢 API key automatically detected from secrets.")
    else:
        api_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIzaSy..."
        )
        st.caption("[Get API key from Google AI Studio](https://aistudio.google.com/)")

    api_key = api_key_input or auto_detected_key

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
# TAB 1: ECOLENS AI SCANNER (WITH RECAPTURE BUTTON)
# ==============================================================================
with tab_scan:
    st.subheader("Visual Waste & Usability Classification")
    st.write("Scan or upload any unwanted item to receive disposal instructions, repair protocols, or rehoming pathways.")

    col_cam, col_upload = st.columns(2)
    with col_cam:
        img_camera = st.camera_input(
            "Capture item with camera", 
            key=f"cam_{st.session_state.camera_key}"
        )
        if img_camera:
            if st.button("🔄 Recapture Snapshot", use_container_width=True):
                st.session_state.camera_key += 1
                st.session_state.ai_analysis_result = None
                st.rerun()

    with col_upload:
        img_upload = st.file_uploader("Or upload item image", type=["jpg", "jpeg", "png"])

    active_image_file = img_camera or img_upload

    if active_image_file:
        img = Image.open(active_image_file)
        st.image(img, caption="Captured Snapshot", width=340)

        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            run_analysis = st.button("🔍 Analyze with Gemma 4", type="primary", use_container_width=True)

        if run_analysis:
            if not api_key:
                st.error("Please enter your Gemini API Key in the sidebar to run inference.")
            else:
                with st.spinner("Classifying material composition and circular potential with Gemma 4..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        
                        system_instruction = (
                            "You are EcoLens, an expert circular economy AI assistant. "
                            "Analyze the object in the image and output structured Markdown containing:\n"
                            "### Object Identified\n"
                            "- **Item**: Exact item name\n"
                            "- **Primary Material**: Composition\n"
                            "- **Recyclability Score**: Integer from 0 to 100\n\n"
                            "### Disposal Protocol\n"
                            "- **Category**: (Dry Waste / Wet Waste / Hazardous & E-Waste / Landfill / Reusable)\n"
                            "- **Recommended Bin Color**: (Blue / Green / Red / Black)\n"
                            "- **Disposal Action**: Concrete disposal or recycling instructions\n\n"
                            "### Upcycling & Reuse Idea\n"
                            "- A practical repurpose, repair, or donation pathway."
                        )

                        config = types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            thinking_config=types.ThinkingConfig(thinking_level="minimal")
                        )

                        prompt = "Classify this item for waste segregation, circular reusability, and material makeup."

                        response = client.models.generate_content(
                            model="gemma-4-26b-a4b-it",
                            contents=[img, prompt],
                            config=config
                        )

                        st.session_state.ai_analysis_result = response.text

                        # Auto-sync category for Tab 3 and Tab 4
                        resp_lower = response.text.lower()
                        if "electronic" in resp_lower or "e-waste" in resp_lower:
                            st.session_state.ai_scanned_category = "Electronics"
                        elif "plastic" in resp_lower:
                            st.session_state.ai_scanned_category = "Plastic"
                        elif "metal" in resp_lower:
                            st.session_state.ai_scanned_category = "Metal"
                        elif "paper" in resp_lower or "cardboard" in resp_lower:
                            st.session_state.ai_scanned_category = "Paper / Books"
                        elif "furniture" in resp_lower or "wood" in resp_lower:
                            st.session_state.ai_scanned_category = "Furniture"
                        else:
                            st.session_state.ai_scanned_category = "Other"

                        st.session_state.ai_scanned_item = "Scanned Item"

                    except Exception as e:
                        st.error(f"Inference failed: {e}")

    # Display analysis output if available
    if st.session_state.ai_analysis_result:
        st.success("✅ Analysis Complete!")
        st.markdown(st.session_state.ai_analysis_result)

        st.divider()
        mcol1, mcol2 = st.columns(2)
        with mcol1:
            st.info(f"**Identified Stream:** `{st.session_state.ai_scanned_category}`")
        with mcol2:
            st.markdown("💡 *Ready to keep this in circulation?* Head to the **🎁 Give Away / Rehome** tab to list it!")

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