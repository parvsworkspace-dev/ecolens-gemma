import streamlit as st
import pandas as pd
import pydeck as pdk

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
DARK_BASEMAP = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

CATEGORY_COLORS = {
    "Electronics":   [34, 211, 238],   # cyan
    "Plastic":       [250, 204, 21],   # amber
    "Metal":         [167, 139, 250],  # violet
    "Paper / Books": [251, 146, 60],   # orange
    "Furniture":     [244, 114, 182],  # pink
    "Other":         [52, 211, 153],   # emerald
}
DEFAULT_COLOR = [52, 211, 153]

# Session-state keys where other modules (e.g. the Give Away tab) may store listings.
# Add your own key here if your listings are stored under a different name.
LISTING_KEYS = ("listings", "giveaway_items", "items", "rehome_items", "secondlife_items")

SAMPLE_DATA = [
    {"name": "Study Desk",        "category": "Furniture",     "lat": 12.9716, "lon": 77.5946, "description": "Solid wood desk, good condition"},
    {"name": "Old Laptop",        "category": "Electronics",   "lat": 12.9352, "lon": 77.6245, "description": "Works, needs a new battery"},
    {"name": "Textbook Bundle",   "category": "Paper / Books", "lat": 12.9784, "lon": 77.6408, "description": "Engineering textbooks, 12 books"},
    {"name": "Steel Utensils",    "category": "Metal",         "lat": 12.9250, "lon": 77.5938, "description": "Kitchen set, lightly used"},
    {"name": "Plastic Crates",    "category": "Plastic",       "lat": 13.0358, "lon": 77.5970, "description": "6 sturdy storage crates"},
    {"name": "Bookshelf",         "category": "Furniture",     "lat": 12.9141, "lon": 77.6101, "description": "5-tier shelf, easy to disassemble"},
    {"name": "Bluetooth Speaker", "category": "Electronics",   "lat": 13.0012, "lon": 77.5680, "description": "Charges fine, minor scratches"},
    {"name": "Bicycle Frame",     "category": "Metal",         "lat": 12.9592, "lon": 77.6974, "description": "Frame only, great for restoration"},
]


# ----------------------------------------------------------------------
# DATA LOADING (adapter: normalises whatever shape the listings are in)
# ----------------------------------------------------------------------
def _normalise(raw):
    """Convert a list of dicts / DataFrame into a clean DataFrame."""
    df = pd.DataFrame(raw)
    if df.empty:
        return df

    def pick(options):
        for col in options:
            if col in df.columns:
                return df[col]
        return None

    out = pd.DataFrame()
    name = pick(["name", "item", "title", "item_name"])
    out["name"] = name if name is not None else "Item"
    cat = pick(["category", "type", "stream"])
    out["category"] = cat if cat is not None else "Other"
    lat = pick(["lat", "latitude"])
    lon = pick(["lon", "lng", "long", "longitude"])
    if lat is None or lon is None:
        return pd.DataFrame()
    out["lat"] = pd.to_numeric(lat, errors="coerce")
    out["lon"] = pd.to_numeric(lon, errors="coerce")
    desc = pick(["description", "details", "notes", "desc"])
    out["description"] = desc if desc is not None else ""
    out = out.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    out["category"] = out["category"].fillna("Other").astype(str)
    out["name"] = out["name"].fillna("Item").astype(str)
    out["description"] = out["description"].fillna("").astype(str)
    return out


def _load_listings():
    for key in LISTING_KEYS:
        if key in st.session_state:
            data = st.session_state[key]
            try:
                df = _normalise(data)
            except Exception:
                continue
            if not df.empty:
                return df, True
    return _normalise(SAMPLE_DATA), False


def _color_for(category):
    return CATEGORY_COLORS.get(category, DEFAULT_COLOR)


# ----------------------------------------------------------------------
# MAIN RENDER FUNCTION
# ----------------------------------------------------------------------
def render_secondlife_map():
    st.markdown(
        """
        <style>
            .map-legend {display:flex; flex-wrap:wrap; gap:10px; margin:10px 0 14px 0;}
            .legend-chip {
                display:inline-flex; align-items:center; gap:8px;
                padding:5px 12px; border-radius:9999px; font-size:0.78rem; font-weight:600;
                background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1);
                color:#cbd5e1;
            }
            .legend-dot {width:10px; height:10px; border-radius:50%;}
            .map-frame {
                border:1px solid rgba(52,211,153,0.3); border-radius:20px; padding:6px;
                background:linear-gradient(160deg, rgba(16,185,129,0.12), rgba(255,255,255,0.02));
                box-shadow:0 20px 50px -20px rgba(16,185,129,0.35);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("🗺️ SecondLife Community Map")
    st.write("Discover items available for reuse and rehoming near you. Pick a location to spotlight it on the map.")

    df, from_app = _load_listings()
    if not from_app:
        st.caption("Showing sample locations. Listings added in the Give Away tab will appear here automatically.")

    if df.empty:
        st.info("No locations to display yet.")
        return

    # ---------------- Filters ----------------
    f1, f2, f3 = st.columns([2, 2, 1])
    categories = sorted(df["category"].unique())
    with f1:
        selected_cats = st.multiselect("Filter by category", categories, default=categories, key="slmap_cats")
    filtered = df[df["category"].isin(selected_cats)].reset_index(drop=True)

    with f2:
        options = ["None"] + filtered["name"].tolist()
        highlight = st.selectbox("Spotlight a location", options, key="slmap_highlight")
    with f3:
        show_labels = st.toggle("Labels", value=True, key="slmap_labels")

    if filtered.empty:
        st.info("No locations match the selected categories.")
        return

    # ---------------- Stat strip ----------------
    m1, m2, m3 = st.columns(3)
    m1.metric("Locations", len(filtered))
    m2.metric("Categories", filtered["category"].nunique())
    m3.metric("Top Stream", filtered["category"].value_counts().idxmax())

    # ---------------- Legend ----------------
    chips = "".join(
        f'<span class="legend-chip"><span class="legend-dot" style="background:rgb({",".join(map(str, _color_for(c)))});'
        f'box-shadow:0 0 10px rgb({",".join(map(str, _color_for(c)))});"></span>{c}</span>'
        for c in sorted(filtered["category"].unique())
    )
    st.markdown(f'<div class="map-legend">{chips}</div>', unsafe_allow_html=True)

    # ---------------- Map data ----------------
    filtered = filtered.copy()
    filtered["color"] = filtered["category"].apply(_color_for)
    filtered["halo_color"] = filtered["color"].apply(lambda c: c + [55])
    filtered["core_color"] = filtered["color"].apply(lambda c: c + [235])
    filtered["is_selected"] = filtered["name"] == highlight
    filtered["description"] = filtered["description"].replace("", "No description provided")

    selected = filtered[filtered["is_selected"]]

    # View state
    if not selected.empty:
        center_lat, center_lon, zoom = float(selected.iloc[0]["lat"]), float(selected.iloc[0]["lon"]), 13.5
    else:
        center_lat, center_lon, zoom = float(filtered["lat"].mean()), float(filtered["lon"].mean()), 11
        if len(filtered) == 1:
            zoom = 13

    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=zoom, pitch=45, bearing=0)

    layers = [
        # Outer glow
        pdk.Layer(
            "ScatterplotLayer", data=filtered,
            get_position="[lon, lat]", get_fill_color="halo_color",
            get_radius=900, radius_min_pixels=22, radius_max_pixels=60, pickable=False,
        ),
        # Mid glow
        pdk.Layer(
            "ScatterplotLayer", data=filtered,
            get_position="[lon, lat]", get_fill_color="halo_color",
            get_radius=450, radius_min_pixels=14, radius_max_pixels=36, pickable=False,
        ),
        # Core marker (interactive)
        pdk.Layer(
            "ScatterplotLayer", data=filtered,
            get_position="[lon, lat]", get_fill_color="core_color",
            get_line_color=[255, 255, 255, 230], line_width_min_pixels=2, stroked=True,
            get_radius=180, radius_min_pixels=7, radius_max_pixels=16, pickable=True, auto_highlight=True,
            highlight_color=[255, 255, 255, 255],
        ),
    ]

    if not selected.empty:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer", data=selected,
                get_position="[lon, lat]", get_fill_color=[250, 204, 21, 60],
                get_line_color=[250, 204, 21, 255], stroked=True, line_width_min_pixels=3,
                get_radius=1400, radius_min_pixels=34, radius_max_pixels=80, pickable=False,
            )
        )

    if show_labels:
        layers.append(
            pdk.Layer(
                "TextLayer", data=filtered,
                get_position="[lon, lat]", get_text="name",
                get_color=[236, 253, 245, 255], get_size=14, get_alignment_baseline="'top'",
                get_pixel_offset=[0, 18], font_family="'Plus Jakarta Sans', sans-serif",
                font_weight=700, pickable=False,
            )
        )

    tooltip = {
        "html": (
            "<div style='padding:4px 2px;'>"
            "<div style='font-weight:800; font-size:14px; color:#6ee7b7;'>{name}</div>"
            "<div style='font-size:11px; letter-spacing:.06em; text-transform:uppercase; color:#94a3b8; margin:2px 0 6px 0;'>{category}</div>"
            "<div style='font-size:12px; color:#e2e8f0; max-width:220px;'>{description}</div>"
            "</div>"
        ),
        "style": {
            "backgroundColor": "rgba(8,14,26,0.94)",
            "border": "1px solid rgba(52,211,153,0.5)",
            "borderRadius": "12px",
            "boxShadow": "0 12px 30px rgba(0,0,0,0.5)",
            "fontFamily": "Plus Jakarta Sans, sans-serif",
        },
    }

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=DARK_BASEMAP,
        tooltip=tooltip,
    )

    st.markdown('<div class="map-frame">', unsafe_allow_html=True)
    st.pydeck_chart(deck, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- Location table ----------------
    with st.expander("📍 View all locations", expanded=False):
        table = filtered[["name", "category", "description", "lat", "lon"]].rename(
            columns={"name": "Item", "category": "Category", "description": "Description", "lat": "Latitude", "lon": "Longitude"}
        )
        st.dataframe(table, use_container_width=True, hide_index=True)