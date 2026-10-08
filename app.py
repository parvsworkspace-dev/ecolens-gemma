"""Blinking (pulsing) map pointers for folium / streamlit-folium.

Usage inside secondlife_map.py:

    import folium
    from streamlit_folium import st_folium
    from blink_marker import add_blinking_marker

    m = folium.Map(location=[12.9716, 77.5946], zoom_start=12, tiles="CartoDB dark_matter")
    add_blinking_marker(m, 12.9716, 77.5946, popup="Study table - free", color="#B8F34A")
    st_folium(m, height=520, use_container_width=True)
"""
import folium

# Injected once per map so the animation works inside the folium iframe.
BLINK_CSS = """
<style>
  .blink-pin { position: relative; width: 22px; height: 22px; }
  .blink-pin .core {
      position: absolute; inset: 4px; border-radius: 50%;
      background: var(--pin); border: 2px solid #fff;
      box-shadow: 0 0 10px var(--pin);
      animation: pin-blink 1.2s ease-in-out infinite;
  }
  .blink-pin .ring {
      position: absolute; inset: 0; border-radius: 50%;
      border: 2px solid var(--pin);
      animation: pin-ring 1.8s ease-out infinite;
  }
  .blink-pin .ring.two { animation-delay: 0.9s; }
  @keyframes pin-blink {
      0%, 100% { opacity: 1;   transform: scale(1); }
      50%      { opacity: 0.35; transform: scale(0.8); }
  }
  @keyframes pin-ring {
      0%   { transform: scale(0.6); opacity: 0.9; }
      100% { transform: scale(3.2); opacity: 0; }
  }
  @media (prefers-reduced-motion: reduce) {
      .blink-pin .core, .blink-pin .ring { animation: none; }
  }
</style>
"""


def _ensure_css(m: folium.Map) -> None:
    if not getattr(m, "_blink_css_added", False):
        m.get_root().header.add_child(folium.Element(BLINK_CSS))
        m._blink_css_added = True


def add_blinking_marker(m, lat, lon, popup=None, tooltip=None, color="#B8F34A"):
    """Add a pulsing, blinking pin to a folium map."""
    _ensure_css(m)
    icon = folium.DivIcon(
        html=(
            f'<div class="blink-pin" style="--pin:{color}">'
            '<span class="ring"></span><span class="ring two"></span>'
            '<span class="core"></span></div>'
        ),
        icon_size=(22, 22),
        icon_anchor=(11, 11),
    )
    folium.Marker(
        location=[lat, lon],
        icon=icon,
        popup=folium.Popup(popup, max_width=260) if popup else None,
        tooltip=tooltip,
    ).add_to(m)