"""
EcoLens: SecondLife Edition — refactored.

Layers (top to bottom):
  1. config      constants, domain data (unchanged business rules)
  2. domain      pure functions: classification, parsing, CO2 maths, spec export
  3. services    Gemini inference
  4. theme       design tokens (dark / light) + CSS
  5. components  small HTML/state renderers (skeleton, empty, error, score ring)
  6. views       one function per tab
  7. main        layout + routing
"""
from __future__ import annotations

import os
import re
import html
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from google import genai
from google.genai import types

# Optional external modules (used if present, else built-in views below)
try:
    from secondlife_map import render_secondlife_map
except ImportError:
    render_secondlife_map = None
try:
    from impact import render_giveaway_tab, render_impact_tab
except ImportError:
    render_giveaway_tab = render_impact_tab = None

st.set_page_config(page_title="EcoLens: SecondLife Edition", page_icon="🌱", layout="wide")

# ═════════════════════════════ 1. CONFIG ═════════════════════════════
MODEL = "gemma-4-26b-a4b-it"
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
CATEGORY_KEYWORDS = [
    (("electronic", "e-waste"), "Electronics"), (("plastic",), "Plastic"),
    (("metal", "steel", "aluminium", "aluminum"), "Metal"), (("paper", "cardboard", "book"), "Paper / Books"),
    (("furniture", "wood"), "Furniture"), (("cloth", "fabric", "textile"), "Clothing"),
]
CAT_ICON = {"Electronics": "💻", "Plastic": "🧴", "Metal": "🥄", "Paper / Books": "📚",
            "Furniture": "🪑", "Clothing": "🧥", "Other": "📦"}
BIN_HEX = {"Blue": "#6ea8fe", "Green": "#7fc79a", "Red": "#ef8a8a", "Black": "#9aa4b2"}
SYSTEM_PROMPT = (
    "You are EcoLens, an expert circular economy AI assistant. "
    "Analyze the object in the image and output structured Markdown containing:\n"
    "### Object Identified\n- **Item**: Exact item name\n- **Primary Material**: Composition\n"
    "- **Recyclability Score**: Integer from 0 to 100\n\n"
    "### Disposal Protocol\n"
    "- **Category**: (Dry Waste / Wet Waste / Hazardous & E-Waste / Landfill / Reusable)\n"
    "- **Recommended Bin Color**: (Blue / Green / Red / Black)\n"
    "- **Disposal Action**: Concrete disposal or recycling instructions\n\n"
    "### Upcycling & Reuse Idea\n- A practical repurpose, repair, or donation pathway."
)
USER_PROMPT = "Classify this item for waste segregation, circular reusability, and material makeup."

# Tooltips explain each metric in plain language
HELP = {
    "score": "How easily this item's materials re-enter a recycling stream, 0 to 100. Higher means easier to recycle.",
    "stream": "The material family used to estimate carbon impact. It is inferred from the analysis text.",
    "co2": "Estimated kg of CO₂ avoided when an item of this category is reused instead of replaced.",
    "landfill": "Estimated 4.5 kg of landfill avoided per rehomed item.",
    "rehomed": "Listings that a neighbour has claimed.",
}

# ═════════════════════════════ 2. DOMAIN (logic unchanged) ═════════════════════════════
def classify_stream(text: str) -> str:
    low = text.lower()
    for words, name in CATEGORY_KEYWORDS:
        if any(w in low for w in words):
            return name
    return "Other"


def parse_analysis(text: str) -> dict:
    m = re.search(r"Item\*\*:?\s*(.+)", text)
    s = re.search(r"Recyclability Score\*\*:?\s*(\d+)", text)
    b = re.search(r"Bin Color\*\*:?\s*\(?\s*(Blue|Green|Red|Black)", text, re.I)
    return {
        "category": classify_stream(text),
        "item": m.group(1).strip(" *") if m else "Scanned Item",
        "score": min(int(s.group(1)), 100) if s else None,
        "bin": b.group(1).title() if b else None,
    }


def impact_totals(df: pd.DataFrame) -> dict:
    rehomed = df[df.claimed]
    return {"listed": len(df), "rehomed": len(rehomed),
            "co2": sum(CO2_KG.get(c, 4) for c in rehomed.category), "landfill": len(rehomed) * 4.5}


def potential_co2(df: pd.DataFrame) -> pd.Series:
    return df.groupby("category").size().mul(pd.Series(CO2_KG)).dropna()


def build_specification() -> str:
    s = st.session_state
    co2 = CO2_KG.get(s.ai_scanned_category, 4)
    return (f"# EcoLens Specification: {s.ai_scanned_item}\n\n"
            f"_Generated {datetime.now():%d %b %Y, %H:%M}_\n\n"
            f"| Field | Value |\n|---|---|\n| Item | {s.ai_scanned_item} |\n| Stream | {s.ai_scanned_category} |\n"
            f"| Recyclability | {f'{s.ai_score}/100' if s.ai_score is not None else 'n/a'} |\n"
            f"| Bin | {s.ai_bin or 'n/a'} |\n| Est. CO₂ avoided if reused | {co2} kg |\n\n"
            f"---\n\n{s.ai_analysis_result}\n")


# ═════════════════════════════ 3. SERVICES ═════════════════════════════
def run_inference(api_key: str, img: Image.Image) -> str:
    client = genai.Client(api_key=api_key)
    cfg = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT,
                                      thinking_config=types.ThinkingConfig(thinking_level="minimal"))
    return client.models.generate_content(model=MODEL, contents=[img, USER_PROMPT], config=cfg).text


def get_api_key() -> str:
    key = ""
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        pass
    return key or os.environ.get("GEMINI_API_KEY", "")


# ═════════════════════════════ STATE ═════════════════════════════
def init_state() -> None:
    defaults = {
        "camera_key": 0, "ai_analysis_result": None, "ai_scanned_item": "", "ai_scanned_category": "Other",
        "ai_score": None, "ai_bin": None, "ai_error": None, "theme": "dark",
        "listings": [dict(item=i, category=c, condition=d, area=a, notes=n,
                          lat=AREAS[a][0], lon=AREAS[a][1], claimed=False) for i, c, d, a, n in SEED],
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def apply_analysis(text: str) -> None:
    p = parse_analysis(text)
    s = st.session_state
    s.ai_analysis_result, s.ai_scanned_category = text, p["category"]
    s.ai_scanned_item, s.ai_score, s.ai_bin, s.ai_error = p["item"], p["score"], p["bin"], None


def set_theme(mode: str) -> None:
    st.session_state.theme = mode


def claim_listing(listing: dict) -> None:
    listing["claimed"] = True


# ═════════════════════════════ 4. THEME ═════════════════════════════
TOKENS = {
    "dark": dict(bg="#0c0f0e", surface="#141918", raised="#1a201f", line="#252d2b", text="#eef1ef",
                 muted="#8e9a96", accent="#a8c3ae", accent_ink="#0c1410", accent_soft="rgba(168,195,174,.12)",
                 danger="#f09a9a", chart2="#6f8f7a",
                 shadow="0 1px 0 rgba(255,255,255,.04) inset,0 12px 30px -16px rgba(0,0,0,.7)",
                 glow="rgba(168,195,174,.10)", dot="rgba(255,255,255,.05)"),
    "light": dict(bg="#f6f7f5", surface="#ffffff", raised="#f0f2ef", line="#dfe3df", text="#151a18",
                  muted="#5d6a65", accent="#3f5f4b", accent_ink="#ffffff", accent_soft="rgba(63,95,75,.09)",
                  danger="#b4403f", chart2="#8aa595",
                 shadow="0 1px 2px rgba(20,30,25,.05),0 14px 30px -18px rgba(30,50,40,.25)",
                 glow="rgba(63,95,75,.09)", dot="rgba(30,60,45,.07)"),
}


def inject_css(mode: str) -> None:
    t = TOKENS[mode]
    vars_css = ";".join(f"--{k.replace('_', '-')}:{v}" for k, v in t.items())
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&display=swap');
:root{{{vars_css};--r:14px;color-scheme:{mode}}}
html,body,.stApp,p,label,li,input,textarea,button,h1,h2,h3,h4,[data-testid="stWidgetLabel"]{{font-family:'Instrument Sans',system-ui,sans-serif}}
.stApp{{isolation:isolate;background:radial-gradient(1000px 520px at 10% -8%,var(--glow),transparent 65%),var(--bg);color:var(--text);font-variant-numeric:tabular-nums}}
.stApp::before{{content:'';position:fixed;inset:0;z-index:-1;pointer-events:none;background-image:radial-gradient(var(--dot) 1px,transparent 1.3px);
background-size:22px 22px;-webkit-mask-image:linear-gradient(180deg,#000,transparent 65%);mask-image:linear-gradient(180deg,#000,transparent 65%)}}
.block-container{{max-width:1180px;padding:2.4rem 2rem 4rem}}
#MainMenu,footer{{visibility:hidden}} header[data-testid="stHeader"]{{background:transparent}}
.stApp [data-testid="stSidebar"]{{background:var(--surface);border-right:1px solid var(--line)}}
:focus-visible{{outline:2px solid var(--accent)!important;outline-offset:2px}}

/* ── text colour: explicit so Streamlit's own theme can never leak through ── */
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp p,.stApp li,.stApp label,.stApp summary,
.stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stMetricValue"],.stApp kbd{{color:var(--text)}}
.stApp h1,.stApp h2,.stApp h3,.stApp h4{{letter-spacing:-.02em;font-weight:650}}
.stApp p,.stApp li{{line-height:1.65}}
.stApp [data-testid="stWidgetLabel"] p,.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stCaptionContainer"] *,
.stApp [data-testid="stMetricLabel"] p,.stApp .muted,.stApp .mast p,.stApp .sub,.stApp .state p{{color:var(--muted)}}
.stApp .state.err h4{{color:var(--danger)}}
.stApp a{{color:var(--accent)}}
.stApp code{{background:var(--accent-soft);color:var(--accent);border-radius:6px;padding:2px 6px}}
.stApp kbd{{background:var(--raised);border:1px solid var(--line);border-bottom-width:2px;border-radius:6px;padding:1px 6px;font-size:.78rem}}
::selection{{background:var(--accent);color:var(--accent-ink)}}
::-webkit-scrollbar{{width:10px;height:10px}}::-webkit-scrollbar-thumb{{background:var(--line);border-radius:10px;border:2px solid transparent;background-clip:padding-box}}

/* ── masthead & brand ── */
.logo{{width:44px;height:44px;border-radius:13px;display:grid;place-items:center;flex:none;background:var(--accent);color:var(--accent-ink);
box-shadow:var(--shadow),0 0 0 4px var(--accent-soft)}}
.logo.sm{{width:34px;height:34px;border-radius:10px}}
.mast{{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;padding-bottom:24px;margin-bottom:24px;border-bottom:1px solid var(--line)}}
.brandrow{{display:flex;align-items:center;gap:16px}}
.stApp .mast h1{{font-size:2.4rem;margin:0;line-height:1.1}}
.stApp .mast p{{margin:12px 0 0;max-width:560px}}
.status{{display:inline-flex;align-items:center;gap:8px;padding:7px 14px;border:1px solid var(--line);border-radius:99px;background:var(--surface);
box-shadow:var(--shadow);color:var(--muted);font-size:.84rem;font-weight:550;white-space:nowrap}}
.live{{width:7px;height:7px;border-radius:50%;background:var(--accent);display:inline-block;animation:ping 2.4s infinite}}
@keyframes ping{{0%{{box-shadow:0 0 0 0 var(--accent-soft)}}70%{{box-shadow:0 0 0 8px transparent}}100%{{box-shadow:0 0 0 0 transparent}}}}
.sbrand{{display:flex;align-items:center;gap:12px;padding:4px 0 6px}} .sbrand b{{display:block;font-size:1.05rem}}

/* ── surfaces ── */
.card{{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:20px 22px;box-shadow:var(--shadow)}}
.card.tint{{background:var(--accent-soft);border-color:var(--accent)}}
.listing{{margin-bottom:10px;padding:14px 16px;transition:border-color .2s,transform .2s}}
.listing:hover{{border-color:var(--accent);transform:translateY(-1px)}}
.lh{{display:flex;align-items:center;gap:12px}} .lh b{{display:block;font-size:.98rem;line-height:1.25}}
.badge{{width:36px;height:36px;border-radius:10px;display:grid;place-items:center;background:var(--raised);border:1px solid var(--line);flex:none}}
.tag{{margin-left:auto;font-size:.74rem;font-weight:650;padding:3px 10px;border-radius:99px;background:var(--accent-soft);border:1px solid var(--line);color:var(--accent)}}
.stApp .tag{{color:var(--accent)}} .note{{display:block;margin-top:8px}} .sub{{font-size:.85rem;display:block}}
.stApp [data-testid="stMetric"]{{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:16px 18px;box-shadow:var(--shadow);transition:border-color .2s}}
.stApp [data-testid="stMetric"]:hover{{border-color:var(--accent)}}
.stApp [data-testid="stMetricValue"]{{font-weight:650;letter-spacing:-.02em}}
.stApp [data-testid="stExpander"],.stApp [data-testid="stForm"],.stApp [data-testid="stVerticalBlockBorderWrapper"]{{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--shadow)}}
.stApp [data-testid="stExpander"] summary:hover{{background:var(--raised)}}
.stApp [data-testid="stAlert"]{{background:var(--accent-soft)!important;border:1px solid var(--line);border-radius:12px}}
.stApp [data-testid="stAlert"] *{{color:var(--text)!important}}
.stApp [data-testid="stImage"] img{{border-radius:var(--r);border:1px solid var(--line);box-shadow:var(--shadow)}}
.stProgress>div>div>div>div{{background:var(--accent)}}
.stApp hr{{border:none;height:1px;background:var(--line);margin:1.4rem 0}}

/* ── tabs: segmented pill ── */
.stApp .stTabs [data-baseweb="tab-list"]{{display:flex;width:fit-content;max-width:100%;gap:2px;padding:4px;background:var(--raised);border:1px solid var(--line);border-radius:13px}}
.stApp .stTabs [data-baseweb="tab"]{{height:auto;padding:8px 18px;border-radius:9px;background:transparent;transition:background .2s,box-shadow .2s}}
.stApp .stTabs [data-baseweb="tab"] p{{color:var(--muted);font-weight:550;font-size:.92rem;transition:color .2s}}
.stApp .stTabs [data-baseweb="tab"]:hover p{{color:var(--text)}}
.stApp .stTabs [aria-selected="true"]{{background:var(--surface)!important;box-shadow:var(--shadow)}}
.stApp .stTabs [aria-selected="true"] p{{color:var(--text)}}
.stApp .stTabs [data-baseweb="tab-highlight"],.stApp .stTabs [data-baseweb="tab-border"]{{display:none!important}}
.stApp .stTabs [data-baseweb="tab-panel"]{{padding-top:1.8rem}}

/* ── buttons ── */
.stApp [data-testid^="stBaseButton-secondary"],.stApp div.stButton>button,.stApp div.stDownloadButton>button{{border-radius:10px;font-weight:600;padding:.6rem 1.1rem;
background:var(--surface);border:1px solid var(--line);box-shadow:var(--shadow);transition:transform .15s,border-color .2s,background .2s}}
.stApp [data-testid^="stBaseButton-secondary"]:hover{{border-color:var(--accent);background:var(--raised)}}
.stApp [data-testid^="stBaseButton-primary"]{{border-radius:10px;font-weight:650;padding:.6rem 1.1rem;background:var(--accent);border:1px solid var(--accent);
box-shadow:var(--shadow),0 8px 22px -10px var(--accent);transition:transform .15s,filter .2s}}
.stApp [data-testid^="stBaseButton-primary"]:hover{{filter:brightness(1.08)}}
.stApp [data-testid^="stBaseButton"]:active{{transform:scale(.985)}}
.stApp [data-testid^="stBaseButton-secondary"] p,.stApp [data-testid^="stBaseButton-secondary"] span{{color:var(--text)}}
.stApp [data-testid^="stBaseButton-primary"] p,.stApp [data-testid^="stBaseButton-primary"] span{{color:var(--accent-ink)}}

/* ── inputs ── */
.stApp [data-baseweb="input"],.stApp [data-baseweb="base-input"],.stApp [data-baseweb="textarea"],.stApp [data-baseweb="select"]>div{{
background:var(--surface)!important;border-color:var(--line)!important;border-radius:10px!important}}
.stApp input,.stApp textarea{{background:transparent!important;color:var(--text)!important;-webkit-text-fill-color:var(--text)!important;caret-color:var(--accent)}}
.stApp input::placeholder,.stApp textarea::placeholder{{color:var(--muted)!important;-webkit-text-fill-color:var(--muted)!important}}
.stApp [data-baseweb="select"] *{{color:var(--text)}}
.stApp [data-baseweb="select"] svg,.stApp [data-baseweb="input"] svg{{fill:var(--muted);color:var(--muted)}}
.stApp [data-baseweb="input"]:focus-within,.stApp [data-baseweb="select"]>div:focus-within,.stApp [data-baseweb="textarea"]:focus-within{{
border-color:var(--accent)!important;box-shadow:0 0 0 3px var(--accent-soft)!important}}
.stApp [data-baseweb="tag"]{{background:var(--accent-soft)!important;border-radius:8px}} .stApp [data-baseweb="tag"] span{{color:var(--text)!important}}
[data-baseweb="popover"]>div{{background:var(--surface)!important;border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow)}}
[data-baseweb="popover"] ul{{background:var(--surface)!important}}
[data-baseweb="popover"] li{{color:var(--text)!important;background:transparent!important}}
[data-baseweb="popover"] li:hover,[data-baseweb="popover"] li[aria-selected="true"]{{background:var(--accent-soft)!important}}
.stApp [data-testid="stSlider"] [role="slider"]{{background:var(--accent)!important;box-shadow:0 0 0 4px var(--accent-soft)}}
.stApp [data-testid="stSliderThumbValue"],.stApp [data-testid="stSlider"] [data-testid="stThumbValue"]{{color:var(--accent)!important}}
.stApp [data-testid="stSliderTickBarMin"],.stApp [data-testid="stSliderTickBarMax"]{{color:var(--muted)}}

/* ── uploader & camera ── */
.stApp [data-testid="stFileUploaderDropzone"],.stApp [data-testid="stCameraInput"]>div{{background:var(--surface);border:1px dashed var(--line);border-radius:var(--r);transition:border-color .2s,background .2s}}
.stApp [data-testid="stFileUploaderDropzone"]:hover{{border-color:var(--accent);background:var(--accent-soft)}}
.stApp [data-testid="stFileUploaderDropzone"] *,.stApp [data-testid="stFileUploaderFile"] *{{color:var(--muted)}}
.stApp [data-testid="stFileUploaderDropzone"] button *{{color:var(--text)}}

/* ── chips, ring, states ── */
.chip{{display:inline-flex;align-items:center;gap:8px;padding:5px 12px;border-radius:99px;border:1px solid var(--line);background:var(--raised);font-weight:600;font-size:.85rem}}
.chip i{{width:10px;height:10px;border-radius:50%;display:inline-block}}
.ring{{display:flex;align-items:center;gap:22px}}
.ring svg{{transform:rotate(-90deg);filter:drop-shadow(0 0 8px var(--accent-soft))}}
.ring circle.fg{{stroke-dasharray:var(--c) 999;animation:fill .9s cubic-bezier(.2,.8,.2,1) both}}
@keyframes fill{{from{{stroke-dasharray:0 999}}}}
.ring .num{{font-size:2.5rem;font-weight:650;letter-spacing:-.03em;line-height:1}}
.state{{text-align:center;padding:38px 24px}} .state .ico{{font-size:1.8rem}} .state h4{{margin:10px 0 4px}} .state p{{margin:0 auto;max-width:440px}}
.state.err{{border-color:var(--danger)}}
.steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:12px}}
.step{{display:flex;align-items:center;gap:12px;padding:14px 16px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);box-shadow:var(--shadow)}}
.step .n{{width:26px;height:26px;border-radius:50%;display:grid;place-items:center;flex:none;font-size:.8rem;font-weight:700;background:var(--accent-soft);color:var(--accent);border:1px solid var(--line)}}
.stApp .step .n{{color:var(--accent)}} .step b{{display:block;font-size:.92rem}}
.sk{{border-radius:8px;background:linear-gradient(90deg,var(--raised) 25%,var(--line) 50%,var(--raised) 75%);background-size:200% 100%;animation:sk 1.4s linear infinite}}
@keyframes sk{{to{{background-position:-200% 0}}}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}}}
@media(max-width:700px){{.mast{{flex-direction:column;align-items:flex-start}}.stApp .mast h1{{font-size:1.8rem}}.steps{{grid-template-columns:1fr}}}}
</style>""", unsafe_allow_html=True)


def inject_shortcuts() -> None:
    """1–4 switch tabs, A runs analysis. Ignored while typing in a field."""
    components.html("""<script>
const d=window.parent.document;
if(!d.__ecoKeys){d.__ecoKeys=true;d.addEventListener('keydown',e=>{
 const t=e.target.tagName;if(['INPUT','TEXTAREA','SELECT'].includes(t)||e.metaKey||e.ctrlKey||e.altKey)return;
 if('1234'.includes(e.key)&&e.key){const tabs=d.querySelectorAll('[data-baseweb="tab"]');if(tabs[+e.key-1])tabs[+e.key-1].click();}
 if(e.key.toLowerCase()==='a'){[...d.querySelectorAll('button')].find(b=>b.innerText.includes('Analyze'))?.click();}
});}
</script>""", height=0)


# ═════════════════════════════ 5. COMPONENTS ═════════════════════════════
def esc(x) -> str:
    return html.escape(str(x))


def state_card(kind: str, icon: str, title: str, body: str) -> None:
    cls = "state err" if kind == "error" else "state"
    role = 'role="alert"' if kind == "error" else 'role="status"'
    st.markdown(f'<div class="card {cls}" {role}><div class="ico" aria-hidden="true">{icon}</div>'
                f'<h4>{esc(title)}</h4><p>{esc(body)}</p></div>', unsafe_allow_html=True)


def skeleton() -> str:
    return ('<div class="card" role="status" aria-label="Analyzing item" aria-busy="true">'
            '<div class="sk" style="height:18px;width:38%;margin-bottom:16px"></div>'
            '<div class="sk" style="height:12px;width:92%;margin-bottom:10px"></div>'
            '<div class="sk" style="height:12px;width:80%;margin-bottom:10px"></div>'
            '<div class="sk" style="height:12px;width:66%;margin-bottom:22px"></div>'
            '<div class="sk" style="height:84px;width:100%"></div></div>')


def verdict(score: int) -> str:
    return "Highly recyclable" if score >= 70 else "Partly recyclable" if score >= 40 else "Hard to recycle"


def score_ring(score: int, bin_name: str | None) -> None:
    r, c = 44, 2 * 3.14159 * 44
    dash = c * score / 100
    chip = (f'<span class="chip"><i style="background:{BIN_HEX[bin_name]}"></i>{bin_name} bin</span>' if bin_name else "")
    st.markdown(
        f'<div class="card ring" role="img" aria-label="Recyclability {score} out of 100, {verdict(score)}">'
        f'<svg width="108" height="108" viewBox="0 0 108 108" aria-hidden="true">'
        f'<circle cx="54" cy="54" r="{r}" fill="none" stroke="var(--line)" stroke-width="8"/>'
        f'<circle class="fg" cx="54" cy="54" r="{r}" fill="none" stroke="var(--accent)" stroke-width="8" '
        f'stroke-linecap="round" style="--c:{dash:.1f}"/></svg>'
        f'<div><div class="num">{score}<span class="muted" style="font-size:1rem;font-weight:500">/100</span></div>'
        f'<div class="muted" style="margin:4px 0 10px">{verdict(score)}</div>{chip}</div></div>',
        unsafe_allow_html=True)


def themed_bar(df: pd.DataFrame, x: str, y: str, color: str, y_title: str) -> None:
    t = TOKENS[st.session_state.theme]
    chart = (alt.Chart(df).mark_bar(cornerRadiusEnd=5, color=color, size=22)
             .encode(y=alt.Y(f"{x}:N", sort="-x", title=None), x=alt.X(f"{y}:Q", title=y_title),
                     tooltip=[alt.Tooltip(f"{x}:N", title="Category"), alt.Tooltip(f"{y}:Q", title=y_title)])
             .properties(height=max(160, 38 * len(df)))
             .configure(background="transparent").configure_view(strokeWidth=0)
             .configure_axis(labelColor=t["muted"], titleColor=t["muted"], gridColor=t["line"], domain=False,
                             labelFont="Instrument Sans", titleFont="Instrument Sans"))
    st.altair_chart(chart, use_container_width=True, theme=None)


# ═════════════════════════════ 6. VIEWS ═════════════════════════════
def sidebar() -> str:
    key = get_api_key()
    with st.sidebar:
        st.markdown(f'<div class="sbrand"><span class="logo sm" aria-hidden="true">{LEAF}</span><div><b>EcoLens</b>'
                    '<span class="sub">Autonomous circular economy assistant</span></div></div>', unsafe_allow_html=True)
        cl, cd = st.columns(2)
        for col, mode, label in ((cl, "light", "☀️ Light"), (cd, "dark", "🌙 Dark")):
            col.button(label, key=f"theme_{mode}", on_click=set_theme, args=(mode,), use_container_width=True,
                       type="primary" if st.session_state.theme == mode else "secondary")
        st.divider()
        st.caption("Hackathon track: Open-Source AI Project")
        st.markdown(f"**Team** Codex  \n**Model** `{MODEL}`  \n**License** Apache 2.0 open-weight")
        st.divider()
        api_key = st.text_input("Gemini API key", value=key, type="password", placeholder="AIzaSy...",
                                help="Pre-configured via Streamlit Secrets." if key else None) or key
        if key:
            st.markdown('<span class="muted" style="font-size:.85rem"><span class="live"></span>Key loaded from secrets</span>',
                        unsafe_allow_html=True)
        else:
            st.caption("[Get a key from Google AI Studio](https://aistudio.google.com/)")
        st.divider()
        st.markdown('<span class="sub">Shortcuts <kbd>1</kbd>–<kbd>4</kbd> tabs · <kbd>A</kbd> analyze</span>', unsafe_allow_html=True)
    return api_key


LEAF = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 20A7 7 0 0 1 4 13c0-6 6-9 16-9 0 10-3 16-9 16z"/>'
        '<path d="M4 20c2-5 5-8 10-10"/></svg>')


def masthead() -> None:
    st.markdown(
        f'<header class="mast"><div><div class="brandrow"><span class="logo" aria-hidden="true">{LEAF}</span>'
        '<h1>EcoLens: SecondLife Edition</h1></div>'
        '<p>Point a camera at anything you no longer need. Get disposal steps, a recyclability grade, '
        'and a neighbour who can take it.</p></div>'
        '<div class="status"><span class="live"></span>Gemma 4 vision · Bengaluru network</div></header>',
        unsafe_allow_html=True)


def steps_strip() -> None:
    items = [("Capture", "Take or upload a photo"), ("Analyze", "Get a grade and disposal steps"), ("Rehome", "List it for a neighbour")]
    cells = "".join(f'<div class="step"><span class="n">{i}</span><div><b>{a}</b><span class="sub">{b}</span></div></div>'
                    for i, (a, b) in enumerate(items, 1))
    st.markdown(f'<div class="steps">{cells}</div>', unsafe_allow_html=True)


def view_scanner(api_key: str) -> None:
    st.subheader("Scan an item")
    st.caption("Capture or upload a photo to get disposal instructions, repair options, or a rehoming path.")

    col_cam, col_up = st.columns(2)
    with col_cam:
        with st.expander("Use camera", expanded=False):
            img_camera = st.camera_input("Capture item", key=f"cam_{st.session_state.camera_key}",
                                         label_visibility="collapsed")
            if img_camera and st.button("Retake photo", use_container_width=True):
                st.session_state.camera_key += 1
                st.session_state.ai_analysis_result = None
                st.rerun()
    with col_up:
        img_upload = st.file_uploader("Upload item image", type=["jpg", "jpeg", "png"])

    active = img_camera or img_upload
    result_slot = st.empty()

    if not active and not st.session_state.ai_analysis_result:
        with result_slot.container():
            state_card("empty", "📷", "No item scanned yet",
                       "Upload a photo or open the camera. Results appear here in a few seconds.")
            steps_strip()
        return

    if active:
        img = Image.open(active)
        pv, ac = st.columns([1, 1.4])
        with pv:
            st.image(img, caption="Item preview", use_container_width=True)
        with ac:
            st.markdown('<div class="card tint"><b>Ready to analyze</b>'
                        '<p class="muted" style="margin:6px 0 0">Gemma 4 identifies the item, grades its recyclability, '
                        'and suggests a second life.</p></div>', unsafe_allow_html=True)
            st.write("")
            run = st.button("Analyze item", type="primary", use_container_width=True)

        if run:
            if not api_key:
                st.session_state.ai_error = "Add your Gemini API key in the sidebar, then analyze again."
                st.session_state.ai_analysis_result = None
            else:
                result_slot.markdown(skeleton(), unsafe_allow_html=True)  # loading state
                try:
                    apply_analysis(run_inference(api_key, img))
                except Exception as e:
                    st.session_state.ai_error = f"Inference failed: {e}"
                    st.session_state.ai_analysis_result = None
                result_slot.empty()

    s = st.session_state
    if s.ai_error:
        with result_slot.container():
            state_card("error", "⚠️", "Analysis didn't complete", s.ai_error)
        return

    if s.ai_analysis_result:
        with result_slot.container():
            st.success("Analysis complete")
            ring, a, b = st.columns([1.5, 1, 1])
            with ring:
                if s.ai_score is not None:
                    score_ring(s.ai_score, s.ai_bin)
                elif s.ai_bin:
                    st.markdown(f'<span class="chip"><i style="background:{BIN_HEX[s.ai_bin]}"></i>{s.ai_bin} bin</span>',
                                unsafe_allow_html=True)
            a.metric("Item", s.ai_scanned_item or "—")
            b.metric("Material stream", s.ai_scanned_category, help=HELP["stream"])
            st.metric("Est. CO₂ avoided if reused", f"{CO2_KG.get(s.ai_scanned_category, 4)} kg", help=HELP["co2"])
            with st.container(border=True):
                st.markdown(s.ai_analysis_result)
            d1, d2 = st.columns([1, 1])
            d1.download_button("Download specification", build_specification(),
                               file_name=f"ecolens-{re.sub(r'[^a-z0-9]+', '-', s.ai_scanned_item.lower()).strip('-') or 'item'}.md",
                               mime="text/markdown", type="primary", use_container_width=True)
            d2.caption("Keep it in circulation: open **Give away / rehome**. The form is pre-filled.")


def builtin_map() -> None:
    st.subheader("Community map")
    ls = [l for l in st.session_state.listings if not l["claimed"]]
    c1, c2 = st.columns([2.2, 1])
    with c2:
        cat = st.multiselect("Filter by category", CATEGORIES, default=[])
        shown = [l for l in ls if not cat or l["category"] in cat]
        st.caption(f"{len(shown)} items available nearby")
        for i, l in enumerate(shown):
            st.markdown(
                f'<div class="card listing"><div class="lh"><span class="badge" aria-hidden="true">{CAT_ICON.get(l["category"], "📦")}</span>'
                f'<div><b>{esc(l["item"])}</b><span class="sub">{esc(l["category"])} · {esc(l["area"])}</span></div>'
                f'<span class="tag">{esc(l["condition"])}</span></div><span class="sub note">{esc(l["notes"])}</span></div>',
                unsafe_allow_html=True)
            if st.button("Claim this item", key=f"claim_{i}_{l['item']}", use_container_width=True):
                claim_listing(l)
                st.rerun()
    with c1:
        if shown:
            st.map(pd.DataFrame(shown)[["lat", "lon"]], size=120, color=TOKENS[st.session_state.theme]["accent"], zoom=11)
        else:
            state_card("empty", "🗺️", "Nothing matches these filters",
                       "Clear a filter, or list an item in Give away / rehome to start the network.")


def builtin_give() -> None:
    st.subheader("List an item")
    st.caption("Three quick steps. Optional details stay tucked away until you need them.")
    default_cat = st.session_state.ai_scanned_category
    with st.form("give_form", clear_on_submit=True):
        st.markdown("**1 · What is it?**")
        a, b = st.columns(2)
        item = a.text_input("Item name", value=st.session_state.ai_scanned_item
                            if st.session_state.ai_scanned_item != "Scanned Item" else "")
        cat = b.selectbox("Category", CATEGORIES,
                          index=CATEGORIES.index(default_cat) if default_cat in CATEGORIES else len(CATEGORIES) - 1)
        st.markdown("**2 · Where can it be collected?**")
        c, d = st.columns(2)
        cond = c.select_slider("Condition", ["Fair", "Good", "Repairable", "Like new"], value="Good")
        area = d.selectbox("Pickup area", list(AREAS))
        with st.expander("3 · Add details (optional)"):
            notes = st.text_area("Description", placeholder="Size, condition, pickup instructions...")
        if st.form_submit_button("Publish listing", type="primary", use_container_width=True):
            if not item.strip():
                st.error("Name the item so neighbours know what's on offer.")
            else:
                st.session_state.listings.insert(0, dict(
                    item=item.strip(), category=cat, condition=cond, area=area, notes=notes.strip() or "No description.",
                    lat=AREAS[area][0], lon=AREAS[area][1], claimed=False))
                st.success("Published. Your item is now on the community map.")


def builtin_impact() -> None:
    st.subheader("Community impact")
    df = pd.DataFrame(st.session_state.listings)
    t = impact_totals(df)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Items listed", t["listed"])
    m2.metric("Items rehomed", t["rehomed"], help=HELP["rehomed"])
    m3.metric("CO₂ avoided", f"{t['co2']} kg", help=HELP["co2"])
    m4.metric("Landfill diverted", f"{t['landfill']:.1f} kg", help=HELP["landfill"])
    if t["rehomed"] == 0:
        st.info("Nothing rehomed yet. Claim an item on the map and these numbers update.")
    st.divider()
    acc = TOKENS[st.session_state.theme]
    l, r = st.columns(2)
    with l:
        st.markdown("**Listings by category**")
        counts = df.category.value_counts().rename_axis("category").reset_index(name="items")
        themed_bar(counts, "category", "items", acc["accent"], "Items")
    with r:
        st.markdown("**Potential CO₂ savings by category**")
        pot = potential_co2(df).rename_axis("category").reset_index(name="kg")
        themed_bar(pot, "category", "kg", acc["chart2"], "kg CO₂")


# ═════════════════════════════ 7. MAIN ═════════════════════════════
def main() -> None:
    init_state()
    inject_css(st.session_state.theme)
    api_key = sidebar()
    masthead()
    tab_scan, tab_map, tab_give, tab_impact = st.tabs(
        ["Scanner", "Community map", "Give away / rehome", "Impact"])
    with tab_scan:
        view_scanner(api_key)
    with tab_map:
        (render_secondlife_map or builtin_map)()
    with tab_give:
        (render_giveaway_tab or builtin_give)()
    with tab_impact:
        (render_impact_tab or builtin_impact)()
    inject_shortcuts()


main()