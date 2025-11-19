import streamlit as st
import requests
import pandas as pd
import json

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Serper.dev Intelligence Suite",
    page_icon="🔍",
    layout="wide"
)

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e6e6e6;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC ---
def query_serper(api_key, query, search_type, location_str, gl, hl, num_results=10):
    base_url = "https://google.serper.dev"
    
    endpoint_map = {
        "Organic Search": "search",
        "News": "news",
        "Images": "images",
        "Shopping": "shopping",
        "Places (Maps)": "places",
        "Patents": "patents"
    }
    
    endpoint = endpoint_map.get(search_type, "search")
    url = f"{base_url}/{endpoint}"
    
    payload = {
        "q": query,
        "gl": gl,
        "hl": hl,
        "num": num_results
    }
    
    if location_str and location_str != "Auto":
        payload["location"] = location_str

    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": f"Connection Error: {e}"}

def parse_results(data, search_type):
    results = []
    if search_type == "Organic Search" and "organic" in data:
        results = data["organic"]
    elif search_type == "News" and "news" in data:
        results = data["news"]
    elif search_type == "Places (Maps)" and "places" in data:
        results = data["places"]
    elif search_type == "Images" and "images" in data:
        results = data["images"]
    elif search_type == "Shopping" and "shopping" in data:
        results = data["shopping"]
    
    if not results:
        return pd.DataFrame()

    return pd.json_normalize(results)

# --- 4. UI LAYOUT ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_input = st.text_input("Serper API Key", type="password", help="Paste your key from serper.dev")
    st.divider()
    st.subheader("📍 Geography")
    geo_mode = st.radio("Location Mode", ["Preset Countries", "Custom Input"])
    
    location_str = "Auto"
    gl_code = "us"
    
    if geo_mode == "Preset Countries":
        country_map = {"United States": "us", "United Kingdom": "gb", "Germany": "de", "Canada": "ca"}
        selected_country = st.selectbox("Select Country", list(country_map.keys()))
        gl_code = country_map[selected_country]
    else:
        location_str = st.text_input("Specific Location", placeholder="e.g. London, UK")
        gl_code = st.text_input("Country Code (gl)", value="us", max_chars=2)

    hl_code = st.text_input("Language Code (hl)", value="en", max_chars=2)

st.title("🔍 Serper Intelligence Hub")

col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Search Query", placeholder="Enter your search term...")
with col2:
    search_type = st.selectbox("Vertical", ["Organic Search", "News", "Places (Maps)", "Images", "Shopping"])

if st.button("Run Search"):
    if not api_key_input:
        st.error("Please enter your API Key in the sidebar.")
    elif not query:
        st.warning("Please enter a search query.")
    else:
        with st.spinner(f"Searching..."):
            data = query_serper(api_key_input, query, search_type, location_str, gl_code, hl_code)
            
            if "error" in data:
                st.error(data["error"])
            else:
                df = parse_results(data, search_type)
                if not df.empty:
                    st.success(f"Found {len(df)} results.")
                    tab1, tab2, tab3 = st.tabs(["🖼️ Visual Cards", "📊 Analyst Data", "📄 Raw JSON"])
                    
                    with tab1:
                        for index, row in df.iterrows():
                            with st.container():
                                st.markdown(f"### {row.get('title', 'No Title')}")
                                if 'imageUrl' in row: st.image(row['imageUrl'], width=200)
                                st.markdown(f"**Link:** {row.get('link', '#')}")
                                if 'snippet' in row: st.info(row['snippet'])
                                st.divider()
                    with tab2:
                        st.dataframe(df)
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download CSV", csv, "results.csv", "text/csv")
                    with tab3:
                        st.json(data)
                else:
                    st.warning("No results found.")