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

# ----------------- INJECT CLEAN PREMIUM DESIGN SYSTEM -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Animated Ambient Gradient Header */
    .hero-container {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(6, 78, 59, 0.18) 50%, rgba(5, 150, 105, 0.06) 100%);
        border: 1px solid rgba(52, 211, 153, 0.25);
        border-radius: 18px;
        padding: 28px 34px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
        position: relative;
        overflow: hidden;
    }
    
    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -30%;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, transparent 70%);
        border-radius: 50%;
        filter: blur(40px);
        pointer-events: none;
    }

    .hero-title {
        font-size: 2.25rem;
        font-weight: 800;
        background: linear-gradient(90deg, #34d399, #10b981, #6ee7b7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
        margin-bottom: 6px;
    }

    .hero-subtitle {
        font-size: 1.02rem;
        color: #94a3b8;
        font-weight: 500;
        margin-bottom: 14px;
    }

    .badge-pill-container {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 8px;
    }

    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.12);
        color: #6ee7b7;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid rgba(52, 211, 153, 0.25);
    }

    .pulse-dot {
        width: 7px;
        height: 7px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Tab Custom Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 8px;
        border-radius: 14px;
        border: 1px solid rgba(51, 65, 85, 0.6);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 8px 18px;
        color: #94a3b8;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(16, 185, 129, 0.18) !important;
        color: #34d399 !important;
        border: 1px solid rgba(52, 211, 153, 0.35) !important;
    }

    /* Button Enhancements */
    div.stButton > button {
        border-radius: 12px;
        font-weight: 600;
        letter-spacing: 0.01em;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(52, 211, 153, 0.3);
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px -2px rgba(16, 185, 129, 0.35);
        border-color: #34d399;
    }

    /* Sleek Sidebar Card */
    .sidebar-brand-card {
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(52, 211, 153, 0.2);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)

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
    st.markdown("""
    <div class="sidebar-brand-card">
        <h3 style="margin:0 0 4px 0; color:#34d399; display:flex; align-items:center; gap:8px;">
            🌿 EcoLens
        </h3>
        <p style="margin:0; font-size:0.8rem; color:#94a3b8;">Autonomous Circular Economy Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption("Hackathon Track: Open-Source AI Project")
    st.markdown("**Team:** Codex")
    st.markdown("**Model:** `gemma-4-26b-a4b-it`")
    st.markdown("**License:** Apache 2.0 Open-Weight")
    st.divider()

    if auto_detected_key:
        api_key_input = st.text_input(
            "Gemini API Key",
            value=auto_detected_key,
            type="password",
            help="Pre-configured via Streamlit Secrets."
        )
        st.markdown("""
        <div style="display:inline-flex; align-items:center; gap:6px; font-size:0.8rem; color:#34d399; margin-top:4px;">
            <span class="pulse-dot"></span> Secrets Engine Active
        </div>
        """, unsafe_allow_html=True)
    else:
        api_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIzaSy..."
        )
        st.caption("[Get API key from Google AI Studio](https://aistudio.google.com/)")

    api_key = api_key_input or auto_detected_key

# ----------------- HERO BANNER -----------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🌱 EcoLens: SecondLife Edition</div>
    <div class="hero-subtitle">Open-Source AI Segregation & Localized Circular Economy Infrastructure</div>
    <div class="badge-pill-container">
        <span class="badge-pill"><span class="pulse-dot"></span> Gemma 4 Multimodal Vision</span>
        <span class="badge-pill">⚡ Real-time Material Diagnostics</span>
        <span class="badge-pill">📍 Geo-spatial Rehoming Network</span>
        <span class="badge-pill">📉 Carbon Offset Ledger</span>
    </div>
</div>
""", unsafe_allow_html=True)

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