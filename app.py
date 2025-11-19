import streamlit as st
import requests
import pandas as pd
import json

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Serper Backend V3", layout="wide")

# --- BACKEND LOGIC (The "Engine") ---
@st.cache_data(show_spinner=False)
def query_serper(api_key, query_term, search_type, location, gl, hl, num_results):
    """
    Dispatcher function that handles the logic for all 12 Serper endpoints.
    """
    # 1. Select Base URL (Scraper uses a different host)
    if search_type == "Webpage Scraper":
        base_url = "https://scrape.serper.dev"
        endpoint = "" 
    else:
        base_url = "https://google.serper.dev"
        # Map readable names to API endpoints
        endpoint_map = {
            "Organic Search": "search",
            "News": "news",
            "Images": "images",
            "Videos": "videos",
            "Shopping": "shopping",
            "Places": "places",
            "Maps": "maps",
            "Reviews": "reviews",
            "Patents": "patents",
            "Scholar": "scholar",
            "Autocomplete": "autocomplete",
            "Lens (Reverse Image)": "lens"
        }
        endpoint = endpoint_map.get(search_type, "search")

    url = f"{base_url}/{endpoint}" if endpoint else base_url

    # 2. Build Payload (Logic varies by type)
    payload = {
        "gl": gl,
        "hl": hl
    }

    # CASE A: URL-based tools (Lens, Scraper)
    if search_type in ["Webpage Scraper", "Lens (Reverse Image)"]:
        payload["url"] = query_term

    # CASE B: ID-based tools (Reviews)
    elif search_type == "Reviews":
        # Logic: If input looks like a PlaceID (starts with 'Ch'), use placeId, else CID
        if query_term.startswith("Ch"):
            payload["placeId"] = query_term
        else:
            payload["cid"] = query_term # You can also treat the query as a keyword if needed

    # CASE C: Standard Search tools
    else:
        payload["q"] = query_term
        payload["num"] = num_results
        if location and location != "Auto":
            payload["location"] = location

    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    # 3. Execute Request
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- SIMPLE UI (For Testing the Backend) ---
with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("API Key", type="password")
    
    # Grouping the tools logically
    tool_category = st.selectbox("Select Tool Category", 
        ["General Search", "Media & Visual", "Academic & Research", "Local & Maps", "Dev Tools"])
    
    if tool_category == "General Search":
        search_type = st.radio("Endpoint", ["Organic Search", "News", "Shopping", "Autocomplete"])
    elif tool_category == "Media & Visual":
        search_type = st.radio("Endpoint", ["Images", "Videos", "Lens (Reverse Image)"])
    elif tool_category == "Academic & Research":
        search_type = st.radio("Endpoint", ["Scholar", "Patents"])
    elif tool_category == "Local & Maps":
        search_type = st.radio("Endpoint", ["Places", "Maps", "Reviews"])
    else:
        search_type = st.radio("Endpoint", ["Webpage Scraper"])

    st.divider()
    # Global Parameters
    gl = st.text_input("Country Code (gl)", "us")
    hl = st.text_input("Language (hl)", "en")
    if search_type not in ["Webpage Scraper", "Lens (Reverse Image)", "Reviews"]:
        location = st.text_input("Location", "Auto")
    else:
        location = None
    
    num = st.slider("Results", 10, 100, 20)

st.subheader(f"Testing: {search_type}")

# Dynamic Input Field based on type
if search_type == "Lens (Reverse Image)":
    query = st.text_input("Enter Image URL to analyze:")
elif search_type == "Webpage Scraper":
    query = st.text_input("Enter Website URL to scrape:")
elif search_type == "Reviews":
    query = st.text_input("Enter Place ID or CID:")
else:
    query = st.text_input("Enter Search Query:")

if st.button("Run Request"):
    if not api_key:
        st.error("Need API Key")
    elif not query:
        st.error("Need Query")
    else:
        data = query_serper(api_key, query, search_type, location, gl, hl, num)
        
        if "error" in data:
            st.error(data["error"])
        else:
            st.success("Backend Received Data")
            st.json(data) # Dumping raw JSON to verify backend accuracy