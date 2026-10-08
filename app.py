import os
import re
import streamlit as st
import pandas as pd
from PIL import Image
from google import genai
from google.genai import types

# ---------- Optional external modules (used if present, else built-in tabs below) ----------
try:
    from secondlife_map import render_secondlife_map
except ImportError:
    render_secondlife_map = None
try:
    from impact import render_giveaway_tab, render_impact_tab
except ImportError:
    render_giveaway_tab = render_impact_tab = None

st.set_page_config(page_title="EcoLens: SecondLife Edition", page_icon="🌱", layout="wide")

# ---------- Design system ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root{--bg0:#05080f;--bg1:#0a101c;--glass:rgba(255,255,255,.045);--glass2:rgba(255,255,255,.075);
--line:rgba(255,255,255,.09);--accent-line:rgba(52,211,153,.38);--text:#e6edf6;--muted:#8b9ab0;
--em:#10b981;--em2:#34d399;--mint:#6ee7b7;--cyan:#22d3ee;--r:18px}
body,p,label,li,input,textarea,button,h1,h2,h3,h4,.stMarkdown,.stCaption,[data-testid="stWidgetLabel"]{font-family:'Plus Jakarta Sans',sans-serif}
h1,h2,h3,h4{letter-spacing:-.02em;font-weight:700}
p,li{line-height:1.7}
.stApp{background:radial-gradient(900px 500px at 8% -5%,rgba(16,185,129,.18),transparent 60%),
radial-gradient(800px 500px at 100% 0%,rgba(34,211,238,.11),transparent 60%),
radial-gradient(700px 500px at 50% 110%,rgba(16,185,129,.09),transparent 60%),
linear-gradient(180deg,var(--bg1),var(--bg0));background-attachment:fixed;color:var(--text)}
.stApp::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
background-size:56px 56px;-webkit-mask-image:radial-gradient(ellipse at center,#000 30%,transparent 78%);mask-image:radial-gradient(ellipse at center,#000 30%,transparent 78%)}
.block-container{padding-top:2rem;padding-bottom:4rem;max-width:1280px}
#MainMenu,footer{visibility:hidden}
header[data-testid="stHeader"]{background:transparent}

/* glass primitives */
.glass{background:var(--glass);border:1px solid var(--line);border-radius:var(--r);padding:22px 24px;
backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
box-shadow:0 18px 44px -22px rgba(0,0,0,.75),0 1px 0 rgba(255,255,255,.08) inset}
.glass.accent{border-color:var(--accent-line);background:linear-gradient(160deg,rgba(16,185,129,.12),rgba(255,255,255,.03))}
.kicker{font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--em2);margin-bottom:6px}

/* hero */
.hero{border:1px solid var(--accent-line);border-radius:26px;padding:42px 46px;margin-bottom:26px;position:relative;overflow:hidden;
background:linear-gradient(135deg,rgba(16,185,129,.11),rgba(6,78,59,.24) 50%,rgba(34,211,238,.06));
backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
box-shadow:0 28px 64px -22px rgba(0,0,0,.75),0 1px 0 rgba(255,255,255,.14) inset}
.hero::before,.hero::after{content:'';position:absolute;border-radius:50%;filter:blur(55px);pointer-events:none}
.hero::before{top:-60%;right:-8%;width:460px;height:460px;background:radial-gradient(circle,rgba(16,185,129,.3),transparent 70%);animation:float 9s ease-in-out infinite}
.hero::after{bottom:-70%;left:5%;width:380px;height:380px;background:radial-gradient(circle,rgba(34,211,238,.16),transparent 70%);animation:float 11s ease-in-out infinite reverse}
@keyframes float{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(-24px,18px) scale(1.08)}}
.hero-title{font-size:2.9rem;font-weight:800;line-height:1.1;letter-spacing:-.04em;margin-bottom:10px;position:relative;z-index:1;
background:linear-gradient(90deg,#a7f3d0,#34d399 35%,#22d3ee 70%,#6ee7b7);background-size:200% auto;
-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 8s linear infinite}
@keyframes shimmer{to{background-position:200% center}}
.hero-sub{font-size:1.08rem;color:#a5b4c8;font-weight:500;max-width:720px;margin-bottom:18px;position:relative;z-index:1}
.pills{display:flex;gap:10px;flex-wrap:wrap;position:relative;z-index:1}
.pill{display:inline-flex;align-items:center;gap:7px;background:rgba(16,185,129,.1);color:var(--mint);padding:6px 14px;border-radius:99px;
font-size:.78rem;font-weight:600;border:1px solid rgba(52,211,153,.28);transition:all .25s}
.pill:hover{background:rgba(16,185,129,.2);transform:translateY(-2px);border-color:rgba(110,231,183,.6)}
.dot{width:7px;height:7px;background:#10b981;border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(16,185,129,.7)}70%{box-shadow:0 0 0 8px rgba(16,185,129,0)}100%{box-shadow:0 0 0 0 rgba(16,185,129,0)}}

/* tabs */
.stTabs [data-baseweb="tab-list"]{gap:6px;background:var(--glass);padding:6px;border-radius:16px;border:1px solid var(--line);
backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);box-shadow:0 10px 30px -12px rgba(0,0,0,.6)}
.stTabs [data-baseweb="tab"]{border-radius:12px;padding:10px 22px;color:var(--muted);font-weight:600;transition:all .25s;background:transparent}
.stTabs [data-baseweb="tab"]:hover{color:var(--text);background:rgba(255,255,255,.05)}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,rgba(16,185,129,.26),rgba(34,211,238,.1))!important;color:var(--mint)!important;
border:1px solid rgba(52,211,153,.4)!important;box-shadow:0 6px 20px -8px rgba(16,185,129,.55)}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none}
.stTabs [data-baseweb="tab-panel"]{padding-top:1.6rem}

/* buttons */
div.stButton>button,div.stFormSubmitButton>button{border-radius:12px;font-weight:600;padding:.65rem 1.2rem;background:var(--glass2);color:var(--text);
border:1px solid rgba(52,211,153,.3);transition:all .25s cubic-bezier(.4,0,.2,1)}
div.stButton>button:hover,div.stFormSubmitButton>button:hover{transform:translateY(-2px);box-shadow:0 10px 26px -6px rgba(16,185,129,.45);border-color:var(--em2);color:#ecfdf5}
div.stButton>button[kind="primary"],div.stFormSubmitButton>button[kind="primary"]{background:linear-gradient(135deg,#10b981,#059669 55%,#0d9488);
color:#04130d;font-weight:700;border:1px solid rgba(110,231,183,.6);box-shadow:0 10px 28px -10px rgba(16,185,129,.7),0 1px 0 rgba(255,255,255,.3) inset}
div.stButton>button[kind="primary"]:hover,div.stFormSubmitButton>button[kind="primary"]:hover{filter:brightness(1.1);color:#021009}

/* inputs */
div[data-baseweb="input"],div[data-baseweb="select"]>div,div[data-baseweb="textarea"],.stTextArea textarea,.stNumberInput>div>div{
background:rgba(255,255,255,.04)!important;border-radius:12px!important;border-color:var(--line)!important}
div[data-baseweb="input"]:focus-within,div[data-baseweb="select"]>div:focus-within,div[data-baseweb="textarea"]:focus-within{
border-color:var(--em2)!important;box-shadow:0 0 0 3px rgba(52,211,153,.18)!important}
[data-testid="stWidgetLabel"] p{color:#b6c3d6;font-weight:600;font-size:.88rem}

/* media */
[data-testid="stFileUploaderDropzone"]{background:var(--glass);border:1.5px dashed rgba(52,211,153,.35);border-radius:var(--r);transition:all .25s}
[data-testid="stFileUploaderDropzone"]:hover{background:rgba(16,185,129,.08);border-color:var(--em2);box-shadow:0 0 30px -8px rgba(16,185,129,.35)}
[data-testid="stCameraInput"] video,[data-testid="stCameraInput"] img,[data-testid="stCameraInput"]>div{border-radius:var(--r)}
[data-testid="stImage"] img{border-radius:var(--r);border:1px solid var(--line);box-shadow:0 18px 40px -16px rgba(0,0,0,.7)}
[data-testid="stAlert"]{border-radius:14px;border:1px solid var(--line);backdrop-filter:blur(10px)}

/* cards */
[data-testid="stMetric"]{background:linear-gradient(160deg,rgba(255,255,255,.07),rgba(255,255,255,.02));border:1px solid var(--line);border-radius:var(--r);
padding:18px 20px;box-shadow:0 14px 34px -18px rgba(0,0,0,.7);transition:all .25s}
[data-testid="stMetric"]:hover{transform:translateY(-3px);border-color:var(--accent-line);box-shadow:0 18px 40px -14px rgba(16,185,129,.3)}
[data-testid="stMetricValue"]{font-weight:800;letter-spacing:-.02em;background:linear-gradient(90deg,#a7f3d0,#34d399);
-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
[data-testid="stMetricLabel"] p{color:var(--muted);font-weight:600}
[data-testid="stExpander"]{background:var(--glass);border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
[data-testid="stForm"]{background:var(--glass);border:1px solid var(--line);border-radius:22px;padding:26px;
backdrop-filter:blur(14px);box-shadow:0 18px 44px -20px rgba(0,0,0,.7)}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
.stProgress>div>div>div>div{background:linear-gradient(90deg,#10b981,#22d3ee)}
iframe{border-radius:18px;border:1px solid var(--line)}
hr{border:none;height:1px;background:linear-gradient(90deg,transparent,rgba(52,211,153,.4),transparent);margin:1.6rem 0}
code{background:rgba(16,185,129,.12);color:var(--mint);border-radius:6px;padding:2px 7px}
a{color:var(--em2);text-decoration:none}a:hover{color:var(--mint);text-decoration:underline}
::selection{background:rgba(16,185,129,.35);color:#fff}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(148,163,184,.25);border-radius:10px;border:2px solid transparent;background-clip:padding-box}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1220,#070b14);border-right:1px solid var(--line)}
.brand{background:linear-gradient(160deg,rgba(16,185,129,.15),rgba(15,23,42,.9) 60%);border:1px solid var(--accent-line);border-radius:16px;padding:18px;margin-bottom:16px}
.bin{display:inline-block;padding:4px 12px;border-radius:99px;font-size:.78rem;font-weight:700;border:1px solid var(--accent-line);color:var(--mint);background:rgba(16,185,129,.12)}
.listing{margin-bottom:12px}.listing b{font-size:1rem}.listing span{color:var(--muted);font-size:.85rem}
@media(max-width:700px){.hero{padding:26px 22px}.hero-title{font-size:2rem}}
</style>
""", unsafe_allow_html=True)

# ---------- Data & state ----------
CATEGORIES = ["Electronics", "Plastic", "Metal", "Paper / Books", "Furniture", "Clothing", "Other"]
CO2_KG = {"Electronics": 20, "Plastic": 3, "Metal": 6, "Paper / Books": 2, "Furniture": 25, "Clothing": 8, "Other": 4}
AREAS = {"Indiranagar": (12.9719, 77.6412), "Koramangala": (12.9352, 77.6245), "Jayanagar": (12.9308, 77.5838),
         "HSR Layout": (12.9116, 77.6389), "Whitefield": (12.9698, 77.7500), "Malleshwaram": (13.0035, 77.5647)}
SEED = [
    ("Study desk", "Furniture", "Good", "Indiranagar", "Solid wood, minor scratches."),
    ("Old laptop", "Electronics", "Repairable", "Koramangala", "Works, battery needs replacing."),
    ("Textbook set", "Paper / Books", "Good", "Jayanagar", "Class 10 CBSE, 6 books."),
    ("Steel utensils", "Metal", "Good", "HSR Layout", "Assorted pots and pans."),
    ("Storage bins", "Plastic", "Fair", "Whitefield", "Four stackable crates."),
    ("Winter jackets", "Clothing", "Good", "Malleshwaram", "Three adult sizes, cleaned."),
]
defaults = {"camera_key": 0, "ai_analysis_result": None, "ai_scanned_item": "", "ai_scanned_category": "Other",
            "ai_score": None, "ai_bin": None,
            "listings": [dict(item=i, category=c, condition=d, area=a, notes=n, lat=AREAS[a][0], lon=AREAS[a][1], claimed=False)
                         for i, c, d, a, n in SEED]}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

key = ""
try:
    key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    pass
key = key or os.environ.get("GEMINI_API_KEY", "")

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="brand"><h3 style="margin:0 0 4px;color:#34d399">🌿 EcoLens</h3>'
                '<p style="margin:0;font-size:.8rem;color:#94a3b8">Autonomous Circular Economy Assistant</p></div>',
                unsafe_allow_html=True)
    st.caption("Hackathon Track: Open-Source AI Project")
    st.markdown("**Team:** Codex")
    st.markdown("**Model:** `gemma-4-26b-a4b-it`")
    st.markdown("**License:** Apache 2.0 Open-Weight")
    st.divider()
    api_key = st.text_input("Gemini API Key", value=key, type="password", placeholder="AIzaSy...",
                            help="Pre-configured via Streamlit Secrets." if key else None) or key
    if key:
        st.markdown('<div style="display:inline-flex;align-items:center;gap:6px;font-size:.8rem;color:#34d399">'
                    '<span class="dot"></span> Secrets Engine Active</div>', unsafe_allow_html=True)
    else:
        st.caption("[Get an API key from Google AI Studio](https://aistudio.google.com/)")

# ---------- Hero ----------
st.markdown("""
<div class="hero">
  <div class="hero-title">🌱 EcoLens: SecondLife Edition</div>
  <div class="hero-sub">Open-Source AI Segregation &amp; Localized Circular Economy Infrastructure</div>
  <div class="pills">
    <span class="pill"><span class="dot"></span> Gemma 4 Multimodal Vision</span>
    <span class="pill">⚡ Real-time Material Diagnostics</span>
    <span class="pill">📍 Geo-spatial Rehoming Network</span>
    <span class="pill">📉 Carbon Offset Ledger</span>
  </div>
</div>
""", unsafe_allow_html=True)

tab_scan, tab_map, tab_give, tab_impact = st.tabs(
    ["📸 EcoLens AI Scanner", "🗺️ SecondLife Map", "🎁 Give Away / Rehome", "📊 Community Impact"])

# ---------- Built-in tab renderers ----------
def builtin_map():
    st.markdown('<div class="kicker">Live network</div>', unsafe_allow_html=True)
    st.subheader("SecondLife Community Map")
    ls = [l for l in st.session_state.listings if not l["claimed"]]
    c1, c2 = st.columns([2.2, 1])
    with c2:
        cat = st.multiselect("Filter by category", CATEGORIES, default=[])
        shown = [l for l in ls if not cat or l["category"] in cat]
        st.caption(f"{len(shown)} items available nearby")
        for i, l in enumerate(shown):
            st.markdown(f'<div class="glass listing"><b>{l["item"]}</b><br><span>{l["category"]} · {l["condition"]} · {l["area"]}</span>'
                        f'<br><span>{l["notes"]}</span></div>', unsafe_allow_html=True)
            if st.button("Claim this item", key=f"claim_{i}_{l['item']}", use_container_width=True):
                l["claimed"] = True
                st.rerun()
    with c1:
        if shown:
            st.map(pd.DataFrame(shown)[["lat", "lon"]], size=120, color="#10b981", zoom=11)
        else:
            st.info("No items match. Be the first to list one in the Give Away tab.")

def builtin_give():
    st.markdown('<div class="kicker">Share</div>', unsafe_allow_html=True)
    st.subheader("List an Item on SecondLife Map")
    default_cat = st.session_state.ai_scanned_category
    with st.form("give_form", clear_on_submit=True):
        a, b = st.columns(2)
        item = a.text_input("Item name", value=st.session_state.ai_scanned_item if st.session_state.ai_scanned_item != "Scanned Item" else "")
        cat = b.selectbox("Category", CATEGORIES, index=CATEGORIES.index(default_cat) if default_cat in CATEGORIES else len(CATEGORIES) - 1)
        c, d = st.columns(2)
        cond = c.select_slider("Condition", ["Fair", "Good", "Repairable", "Like new"], value="Good")
        area = d.selectbox("Pickup area", list(AREAS))
        notes = st.text_area("Description", placeholder="Size, condition, pickup instructions...")
        if st.form_submit_button("🎁 Publish listing", type="primary", use_container_width=True):
            if not item.strip():
                st.error("Please name the item.")
            else:
                st.session_state.listings.insert(0, dict(item=item.strip(), category=cat, condition=cond, area=area,
                                                         notes=notes.strip() or "No description.", lat=AREAS[area][0], lon=AREAS[area][1], claimed=False))
                st.success("Listed! It now appears on the SecondLife Map.")

def builtin_impact():
    st.markdown('<div class="kicker">Community</div>', unsafe_allow_html=True)
    st.subheader("Community Circular Impact Dashboard")
    df = pd.DataFrame(st.session_state.listings)
    rehomed = df[df.claimed]
    co2 = sum(CO2_KG.get(c, 4) for c in rehomed.category)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Items listed", len(df))
    m2.metric("Items rehomed", len(rehomed))
    m3.metric("CO₂ avoided", f"{co2} kg")
    m4.metric("Landfill diverted", f"{len(rehomed) * 4.5:.1f} kg")
    st.divider()
    l, r = st.columns(2)
    with l:
        st.markdown("**Listings by category**")
        st.bar_chart(df.category.value_counts(), color="#10b981")
    with r:
        st.markdown("**Potential CO₂ savings by category (kg)**")
        pot = df.groupby("category").size().mul(pd.Series(CO2_KG)).dropna()
        st.bar_chart(pot, color="#22d3ee")

# ---------- TAB 1: Scanner ----------
with tab_scan:
    st.markdown('<div class="kicker">Gemma 4 Vision</div>', unsafe_allow_html=True)
    st.subheader("Visual Waste & Usability Classification")
    st.write("Scan or upload any unwanted item to receive disposal instructions, repair protocols, or rehoming pathways.")

    col_cam, col_up = st.columns(2)
    with col_cam:
        img_camera = st.camera_input("Capture item with camera", key=f"cam_{st.session_state.camera_key}")
        if img_camera and st.button("🔄 Recapture Snapshot", use_container_width=True):
            st.session_state.camera_key += 1
            st.session_state.ai_analysis_result = None
            st.rerun()
    with col_up:
        img_upload = st.file_uploader("Or upload item image", type=["jpg", "jpeg", "png"])

    active = img_camera or img_upload
    if active:
        img = Image.open(active)
        pv, ac = st.columns([1, 1.4])
        with pv:
            st.image(img, caption="Captured Snapshot", use_container_width=True)
        with ac:
            st.markdown('<div class="glass accent"><div class="kicker">Ready</div><b>Run material diagnostics</b>'
                        '<p style="color:#a5b4c8;margin:6px 0 0">Gemma 4 will identify the item, grade its recyclability and suggest a second life.</p></div>',
                        unsafe_allow_html=True)
            st.write("")
            run = st.button("🔍 Analyze with Gemma 4", type="primary", use_container_width=True)

        if run:
            if not api_key:
                st.error("Please enter your Gemini API Key in the sidebar to run inference.")
            else:
                with st.spinner("Classifying material composition and circular potential..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        system = ("You are EcoLens, an expert circular economy AI assistant. "
                                  "Analyze the object in the image and output structured Markdown containing:\n"
                                  "### Object Identified\n- **Item**: Exact item name\n- **Primary Material**: Composition\n"
                                  "- **Recyclability Score**: Integer from 0 to 100\n\n"
                                  "### Disposal Protocol\n"
                                  "- **Category**: (Dry Waste / Wet Waste / Hazardous & E-Waste / Landfill / Reusable)\n"
                                  "- **Recommended Bin Color**: (Blue / Green / Red / Black)\n"
                                  "- **Disposal Action**: Concrete disposal or recycling instructions\n\n"
                                  "### Upcycling & Reuse Idea\n- A practical repurpose, repair, or donation pathway.")
                        cfg = types.GenerateContentConfig(system_instruction=system,
                                                          thinking_config=types.ThinkingConfig(thinking_level="minimal"))
                        resp = client.models.generate_content(
                            model="gemma-4-26b-a4b-it",
                            contents=[img, "Classify this item for waste segregation, circular reusability, and material makeup."],
                            config=cfg)
                        txt = resp.text
                        st.session_state.ai_analysis_result = txt
                        low = txt.lower()
                        cat = "Other"
                        for words, name in [(("electronic", "e-waste"), "Electronics"), (("plastic",), "Plastic"), (("metal", "steel", "aluminium", "aluminum"), "Metal"),
                                            (("paper", "cardboard", "book"), "Paper / Books"), (("furniture", "wood"), "Furniture"),
                                            (("cloth", "fabric", "textile"), "Clothing")]:
                            if any(w in low for w in words):
                                cat = name
                                break
                        st.session_state.ai_scanned_category = cat
                        m = re.search(r"Item\*\*:?\s*(.+)", txt)
                        st.session_state.ai_scanned_item = m.group(1).strip(" *") if m else "Scanned Item"
                        s = re.search(r"Recyclability Score\*\*:?\s*(\d+)", txt)
                        st.session_state.ai_score = min(int(s.group(1)), 100) if s else None
                        b = re.search(r"Bin Color\*\*:?\s*\(?\s*(Blue|Green|Red|Black)", txt, re.I)
                        st.session_state.ai_bin = b.group(1).title() if b else None
                    except Exception as e:
                        st.error(f"Inference failed: {e}")

    if st.session_state.ai_analysis_result:
        st.success("✅ Analysis Complete!")
        m1, m2, m3 = st.columns(3)
        m1.metric("Item", st.session_state.ai_scanned_item or "—")
        m2.metric("Stream", st.session_state.ai_scanned_category)
        m3.metric("Recyclability", f"{st.session_state.ai_score}/100" if st.session_state.ai_score is not None else "—")
        if st.session_state.ai_score is not None:
            st.progress(st.session_state.ai_score / 100)
        if st.session_state.ai_bin:
            st.markdown(f'Recommended bin: <span class="bin">{st.session_state.ai_bin}</span>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(st.session_state.ai_analysis_result)
        st.info("💡 Ready to keep this in circulation? Head to the **🎁 Give Away / Rehome** tab to list it. The form is pre-filled.")

# ---------- Other tabs ----------
with tab_map:
    (render_secondlife_map or builtin_map)()
with tab_give:
    (render_giveaway_tab or builtin_give)()
with tab_impact:
    (render_impact_tab or builtin_impact)()