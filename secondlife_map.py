import streamlit as st
import pandas as pd


def render_secondlife_map():
    st.markdown("## 📍 SecondLife Circular Economy Map")

    st.caption(
        "Find nearby recycling, repair, reuse and donation hubs in Bengaluru."
    )

    category_filter = st.selectbox(
        "🔎 Filter by Hub Type",
        [
            "All",
            "Recycle (DWCC / E-Waste)",
            "Repair Hubs",
            "Reuse / Donation"
        ]
    )

    locations = [
        {
            "name": "Indiranagar DWCC",
            "lat": 12.9784,
            "lon": 77.6408,
            "type": "Recycle (DWCC / E-Waste)"
        },
        {
            "name": "Koramangala Repair Cafe",
            "lat": 12.9352,
            "lon": 77.6245,
            "type": "Repair Hubs"
        },
        {
            "name": "Hennur Community Donation Drop",
            "lat": 13.0358,
            "lon": 77.6394,
            "type": "Reuse / Donation"
        },
        {
            "name": "Whitefield E-Waste Centre",
            "lat": 12.9698,
            "lon": 77.7500,
            "type": "Recycle (DWCC / E-Waste)"
        }
    ]

    df = pd.DataFrame(locations)

    if category_filter != "All":
        df = df[df["type"] == category_filter]

    st.map(df[["lat", "lon"]])

    st.markdown("### 🏢 Available Circular Economy Hubs")

    st.dataframe(
        df[["name", "type"]],
        use_container_width=True,
        hide_index=True
    )
