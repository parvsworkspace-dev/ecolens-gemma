from datetime import datetime
import pandas as pd
import streamlit as st

# Emission & landfill diversion estimates per category
IMPACT_FACTORS = {
    "Electronics": {"co2_kg": 18.5, "waste_kg": 2.0},
    "Furniture": {"co2_kg": 42.0, "waste_kg": 15.0},
    "Plastic": {"co2_kg": 2.5, "waste_kg": 0.5},
    "Metal": {"co2_kg": 8.0, "waste_kg": 3.0},
    "Paper / Books": {"co2_kg": 1.2, "waste_kg": 1.0},
    "Other": {"co2_kg": 3.0, "waste_kg": 1.0},
}


def render_giveaway_tab():
  st.markdown("### 🎁 List an Item on SecondLife Map")
  st.caption("Donate or give away an item to keep it out of the landfill.")

  if "community_listings" not in st.session_state:
    st.session_state.community_listings = [
        {
            "item_name": "Ergonomic Office Chair",
            "category": "Furniture",
            "condition": "Gently Used",
            "location": "Koramangala, Bengaluru",
            "listed_on": "2026-10-07",
        },
        {
            "item_name": "Mechanical Keyboard",
            "category": "Electronics",
            "condition": "Working / Minor cosmetic wear",
            "location": "Indiranagar, Bengaluru",
            "listed_on": "2026-10-08",
        },
    ]

  default_title = st.session_state.get("ai_scanned_item", "")
  default_cat = st.session_state.get("ai_scanned_category", "Furniture")

  with st.form("giveaway_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
      title = st.text_input(
          "Item Title",
          value=default_title,
          placeholder="e.g., Wooden study table",
      )
      category = st.selectbox(
          "Category",
          list(IMPACT_FACTORS.keys()),
          index=(
              list(IMPACT_FACTORS.keys()).index(default_cat)
              if default_cat in IMPACT_FACTORS
              else 0
          ),
      )
      condition = st.selectbox(
          "Condition", ["Like New", "Gently Used", "Needs Repair", "For Parts"]
      )

    with col2:
      location = st.text_input(
          "Pickup Area / Landmark", placeholder="e.g., HSR Layout Sector 2"
      )
      contact_info = st.text_input(
          "Contact Email / Phone", placeholder="e.g., alex@example.com"
      )
      description = st.text_area(
          "Brief Description",
          placeholder="Mention any defects, dimensions, or pickup notes.",
      )

    submitted = st.form_submit_button(
        "Publish SecondLife Listing", use_container_width=True
    )

    if submitted:
      if not title or not location:
        st.error("Please provide both an item title and pickup location.")
      else:
        new_listing = {
            "item_name": title,
            "category": category,
            "condition": condition,
            "location": location,
            "listed_on": datetime.now().strftime("%Y-%m-%d"),
        }
        st.session_state.community_listings.append(new_listing)
        st.success(
            f"🎉 Listing '{title}' is live! Ready for community rehoming."
        )

  st.divider()
  st.markdown("#### 📦 Current Live Listings")
  listings_df = pd.DataFrame(st.session_state.community_listings)
  st.dataframe(listings_df, use_container_width=True)


def render_impact_tab():
  st.markdown("### 🌱 Community Circular Impact Dashboard")
  st.caption(
      "Quantifying total carbon footprint avoided and landfill volume spared."
  )

  listings = st.session_state.get("community_listings", [])
  total_items = len(listings)

  total_co2 = 0.0
  total_waste = 0.0

  for item in listings:
    cat = item.get("category", "Other")
    factors = IMPACT_FACTORS.get(cat, IMPACT_FACTORS["Other"])
    total_co2 += factors["co2_kg"]
    total_waste += factors["waste_kg"]

  col1, col2, col3 = st.columns(3)
  col1.metric(
      "Items Kept in Circulation", f"{total_items} items", delta="+12% this week"
  )
  col2.metric(
      "CO₂ Emissions Avoided",
      f"{total_co2:.1f} kg",
      delta="Equivalent to 180 km driven",
  )
  col3.metric(
      "Landfill Waste Diverted",
      f"{total_waste:.1f} kg",
      delta="Raw scrap avoided",
  )

  st.divider()

  if listings:
    cat_counts = (
        pd.DataFrame(listings)["category"].value_counts().reset_index()
    )
    cat_counts.columns = ["Category", "Total Items"]
    st.markdown("#### Diversion by Category")
    st.bar_chart(data=cat_counts.set_index("Category"))
