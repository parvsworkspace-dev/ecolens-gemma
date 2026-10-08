# ♻️ EcoLens: Smart Waste Classifier & Protocol Advisor

An open-source, vision-driven waste segregation assistant built during Hacktoberfest '26 at Kristu Jayanti University in collaboration with MLH.

## 🌟 Overview
EcoLens tackles municipal recycling contamination by classifying everyday waste items at the point of disposal using computer vision. Simply hold an object up to the camera to receive:
- Exact material detection (e.g., PET #1, Polystyrene, Acrylic).
- Prescriptive bin color routing (Blue, Green, Red, Black).
- Actionable disposal prep instructions.
- Circular upcycling recommendations.

## 🛠️ Architecture & Tech Stack
- **Model:** Google DeepMind's `gemma-4-26b-a4b-it` (MoE architecture, Apache 2.0 open-weight).
- **Interface:** Streamlit.
- **SDK:** `google-genai` Python library with multimodal image understanding and minimal-latency reasoning configuration.

## 🚀 How to Run Locally

```bash
git clone [https://github.com/parvsworkspace-dev/ecolens-gemma.git](https://github.com/parvsworkspace-dev/ecolens-gemma.git)
cd ecolens-gemma
pip install streamlit pillow google-genai
python -m streamlit run app.py