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

    :root {
        --bg-0: #05080f;
        --bg-1: #0a101c;
        --surface: rgba(255, 255, 255, 0.035);
        --surface-strong: rgba(255, 255, 255, 0.06);
        --border: rgba(255, 255, 255, 0.08);
        --border-accent: rgba(52, 211, 153, 0.35);
        --text: #e6edf6;
        --muted: #8b9ab0;
        --emerald: #10b981;
        --emerald-light: #34d399;
        --mint: #6ee7b7;
        --cyan: #22d3ee;
        --radius: 16px;
    }

    /* ---------- Typography (icon fonts left untouched) ---------- */
    body, p, label, li, input, textarea, button, h1, h2, h3, h4, h5, h6,
    .stMarkdown, .stCaption, [data-testid="stWidgetLabel"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    h1, h2, h3, h4 {
        letter-spacing: -0.02em;
        font-weight: 700;
    }

    p, li { line-height: 1.7; }

    /* ---------- App Canvas: aurora + subtle grid ---------- */
    .stApp {
        background:
            radial-gradient(900px 500px at 8% -5%, rgba(16, 185, 129, 0.16), transparent 60%),
            radial-gradient(800px 500px at 100% 0%, rgba(34, 211, 238, 0.10), transparent 60%),
            radial-gradient(700px 500px at 50% 110%, rgba(16, 185, 129, 0.08), transparent 60%),
            linear-gradient(180deg, var(--bg-1) 0%, var(--bg-0) 100%);
        background-attachment: fixed;
        color: var(--text);
    }

    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
        background-size: 56px 56px;
        mask-image: radial-gradient(ellipse at center, black 30%, transparent 78%);
        -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 78%);
        pointer-events: none;
        z-index: 0;
    }

    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 4rem;
        max-width: 1280px;
    }

    /* Clean chrome */
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    /* ---------- Hero ---------- */
    .hero-container {
        background:
            linear-gradient(135deg, rgba(16, 185, 129, 0.10) 0%, rgba(6, 78, 59, 0.22) 50%, rgba(34, 211, 238, 0.06) 100%);
        border: 1px solid var(--border-accent);
        border-radius: 24px;
        padding: 40px 44px;
        margin-bottom: 28px;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        box-shadow:
            0 24px 60px -20px rgba(0, 0, 0, 0.7),
            0 0 0 1px rgba(255, 255, 255, 0.03) inset,
            0 1px 0 rgba(255, 255, 255, 0.12) inset;
        position: relative;
        overflow: hidden;
    }

    .hero-container::before {
        content: '';
        position: absolute;
        top: -60%;
        right: -10%;
        width: 460px;
        height: 460px;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.28) 0%, transparent 70%);
        border-radius: 50%;
        filter: blur(50px);
        pointer-events: none;
        animation: float 9s ease-in-out infinite;
    }

    .hero-container::after {
        content: '';
        position: absolute;
        bottom: -70%;
        left: 5%;
        width: 380px;
        height: 380px;
        background: radial-gradient(circle, rgba(34, 211, 238, 0.14) 0%, transparent 70%);
        border-radius: 50%;
        filter: blur(50px);
        pointer-events: none;
        animation: float 11s ease-in-out infinite reverse;
    }

    @keyframes float {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(-24px, 18px) scale(1.08); }
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        line-height: 1.1;
        background: linear-gradient(90deg, #a7f3d0 0%, #34d399 35%, #22d3ee 70%, #6ee7b7 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.04em;
        margin-bottom: 10px;
        position: relative;
        z-index: 1;
        animation: shimmer 8s linear infinite;
    }

    @keyframes shimmer {
        to { background-position: 200% center; }
    }

    .hero-subtitle {
        font-size: 1.08rem;
        color: #a5b4c8;
        font-weight: 500;
        margin-bottom: 20px;
        position: relative;
        z-index: 1;
        max-width: 720px;
    }

    .badge-pill-container {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 8px;
        position: relative;
        z-index: 1;
    }

    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: rgba(16, 185, 129, 0.10);
        color: var(--mint);
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid rgba(52, 211, 153, 0.28);
        backdrop-filter: blur(8px);
        transition: all 0.25s ease;
    }

    .badge-pill:hover {
        background: rgba(16, 185, 129, 0.2);
        transform: translateY(-2px);
        border-color: rgba(110, 231, 183, 0.6);
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

    /* ---------- Tabs ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: rgba(255, 255, 255, 0.03);
        padding: 6px;
        border-radius: 16px;
        border: 1px solid var(--border);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        box-shadow: 0 10px 30px -12px rgba(0, 0, 0, 0.6);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 10px 22px;
        color: var(--muted);
        font-weight: 600;
        transition: all 0.25s ease;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text);
        background: rgba(255, 255, 255, 0.05);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.24), rgba(34, 211, 238, 0.10)) !important;
        color: #6ee7b7 !important;
        border: 1px solid rgba(52, 211, 153, 0.4) !important;
        box-shadow: 0 6px 20px -8px rgba(16, 185, 129, 0.55);
    }

    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1.6rem;
    }

    /* ---------- Buttons ---------- */
    div.stButton > button {
        border-radius: 12px;
        font-weight: 600;
        letter-spacing: 0.01em;
        padding: 0.65rem 1.2rem;
        background: var(--surface-strong);
        color: var(--text);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(52, 211, 153, 0.3);
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 26px -6px rgba(16, 185, 129, 0.45);
        border-color: #34d399;
        color: #ecfdf5;
    }

    div.stButton > button:active { transform: translateY(0); }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 55%, #0d9488 100%);
        color: #04130d;
        font-weight: 700;
        border: 1px solid rgba(110, 231, 183, 0.6);
        box-shadow:
            0 10px 28px -10px rgba(16, 185, 129, 0.7),
            0 1px 0 rgba(255, 255, 255, 0.3) inset;
    }

    div.stButton > button[kind="primary"]:hover {
        filter: brightness(1.1);
        box-shadow:
            0 14px 34px -8px rgba(16, 185, 129, 0.8),
            0 1px 0 rgba(255, 255, 255, 0.35) inset;
        color: #021009;
    }

    /* ---------- Inputs ---------- */
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="textarea"],
    .stTextInput > div > div,
    .stTextArea textarea,
    .stNumberInput > div > div {
        background: rgba(255, 255, 255, 0.04) !important;
        border-radius: 12px !important;
        border-color: var(--border) !important;
        transition: all 0.2s ease;
    }

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="textarea"]:focus-within {
        border-color: var(--emerald-light) !important;
        box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.18) !important;
    }

    [data-testid="stWidgetLabel"] p {
        color: #b6c3d6;
        font-weight: 600;
        font-size: 0.88rem;
    }

    /* ---------- Camera + Uploader ---------- */
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1.5px dashed rgba(52, 211, 153, 0.35);
        border-radius: var(--radius);
        transition: all 0.25s ease;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        background: rgba(16, 185, 129, 0.08);
        border-color: var(--emerald-light);
        box-shadow: 0 0 30px -8px rgba(16, 185, 129, 0.35);
    }

    [data-testid="stCameraInput"] > div,
    [data-testid="stCameraInput"] video,
    [data-testid="stCameraInput"] img {
        border-radius: var(--radius);
    }

    [data-testid="stImage"] img {
        border-radius: var(--radius);
        border: 1px solid var(--border);
        box-shadow: 0 18px 40px -16px rgba(0, 0, 0, 0.7);
    }

    /* ---------- Alerts ---------- */
    [data-testid="stAlert"] {
        border-radius: 14px;
        border: 1px solid var(--border);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 10px 30px -16px rgba(0, 0, 0, 0.6);
    }

    /* ---------- Cards: metrics, expanders, forms, dataframes ---------- */
    [data-testid="stMetric"] {
        background: linear-gradient(160deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 18px 20px;
        box-shadow: 0 14px 34px -18px rgba(0, 0, 0, 0.7);
        transition: all 0.25s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: var(--border-accent);
        box-shadow: 0 18px 40px -14px rgba(16, 185, 129, 0.3);
    }

    [data-testid="stMetricValue"] {
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #a7f3d0, #34d399);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    [data-testid="stMetricLabel"] p { color: var(--muted); font-weight: 600; }

    [data-testid="stExpander"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
    }

    [data-testid="stForm"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 26px;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        box-shadow: 0 18px 44px -20px rgba(0, 0, 0, 0.7);
    }

    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
    }

    iframe {
        border-radius: 18px;
        border: 1px solid var(--border);
    }

    /* ---------- Misc ---------- */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(52, 211, 153, 0.4), transparent);
        margin: 1.6rem 0;
    }

    code {
        background: rgba(16, 185, 129, 0.12);
        color: var(--mint);
        border-radius: 6px;
        padding: 2px 7px;
    }

    [data-testid="stCaptionContainer"] { color: var(--muted); }

    a { color: var(--emerald-light); text-decoration: none; }
    a:hover { color: var(--mint); text-decoration: underline; }

    ::selection { background: rgba(16, 185, 129, 0.35); color: #fff; }

    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.25);
        border-radius: 10px;
        border: 2px solid transparent;
        background-clip: padding-box;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(52, 211, 153, 0.5); background-clip: padding-box; }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1220 0%, #070b14 100%);
        border-right: 1px solid var(--border);
    }

    .sidebar-brand-card {
        background:
            linear-gradient(160deg, rgba(16, 185, 129, 0.14) 0%, rgba(15, 23, 42, 0.9) 60%);
        border: 1px solid var(--border-accent);
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 18px;
        box-shadow:
            0 14px 34px -16px rgba(16, 185, 129, 0.35),
            0 1px 0 rgba(255, 255, 255, 0.08) inset;
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