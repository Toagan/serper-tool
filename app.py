import streamlit as st
import requests
import pandas as pd
import json

# --- 1. APP CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Serper.dev Ultimate Suite",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .result-card { background-color: #262730; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #444; }
    .tag { background-color: #4CAF50; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-right: 5px; }
    .source-text { color: #aaa; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

# --- 2. BACKEND LOGIC ---

@st.cache_data(show_spinner=False)
def query_serper(api_key, query_term, search_type, location, gl, hl, num_results, page_token=None):
    # 1. Determine Host and Endpoint
    if search_type == "Webpage Scraper":
        base_url = "https://scrape.serper.dev"
        endpoint = "" # Root endpoint
    else:
        base_url = "https://google.serper.dev"
        endpoint_map = {
            "Search": "search", "News": "news", "Videos": "videos",
            "Images": "images", "Shopping": "shopping", "Places": "places",
            "Maps": "maps", "Scholar": "scholar", "Patents": "patents",
            "Autocomplete": "autocomplete", "Lens (Reverse Image)": "lens",
            "Reviews": "reviews"
        }
        endpoint = endpoint_map.get(search_type, "search")

    url = f"{base_url}/{endpoint}" if endpoint else base_url

    # 2. Construct Payload based on Type
    payload = {
        "gl": gl,
        "hl": hl
    }
    
    # Special Handling for inputs
    if search_type in ["Webpage Scraper", "Lens (Reverse Image)"]:
        payload["url"] = query_term
    elif search_type == "Reviews":
        # For reviews, we treat the input as a Place ID or CID
        # Heuristic: If it starts with 'Ch', it's likely a PlaceID
        if query_term.startswith("Ch"): 
            payload["placeId"] = query_term
        else:
            payload["cid"] = query_term # Fallback
    else:
        payload["q"] = query_term
        payload["num"] = num_results
        if location and location != "Auto":
            payload["location"] = location

    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def safe_normalize(data, key):
    """Safely extracts a list from JSON and converts to DataFrame"""
    if key in data and isinstance(data[key], list):
        return pd.json_normalize(data[key])
    return pd.DataFrame()

# --- 3. UI LAYOUT ---

with st.sidebar:
    st.header("🎛️ Serper Control")
    
    if "serper_api_key" not in st.session_state:
        st.session_state.serper_api_key = ""
    
    api_key = st.text_input("API Key", type="password", value=st.session_state.serper_api_key)
    if api_key: st.session_state.serper_api_key = api_key

    st.divider()
    
    # Grouped Verticals
    category = st.selectbox("Category", ["Standard Search", "Media", "Geo & Local", "Academic", "Tools"])
    
    if category == "Standard Search":
        search_type = st.radio("Type", ["Search", "News", "Shopping", "Autocomplete"])
    elif category == "Media":
        search_type = st.radio("Type", ["Images", "Videos", "Lens (Reverse Image)"])
    elif category == "Geo & Local":
        search_type = st.radio("Type", ["Places", "Maps", "Reviews"])
    elif category == "Academic":
        search_type = st.radio("Type", ["Scholar", "Patents"])
    else:
        search_type = st.radio("Type", ["Webpage Scraper"])

    st.divider()
    
    # Dynamic Location Controls (Only show if relevant)
    if search_type not in ["Webpage Scraper", "Lens (Reverse Image)", "Reviews"]:
        st.subheader("🌍 Locale")
        gl = st.text_input("Country (gl)", "us", max_chars=2)
        hl = st.text_input("Language (hl)", "en", max_chars=2)
        location = st.text_input("Specific Location", placeholder="e.g. New York, NY")
    else:
        gl, hl, location = "us", "en", "Auto"

    num = st.slider("Results", 10, 100, 20)

# --- 4. MAIN SCREEN ---

st.title(f"🔭 Serper: {search_type}")

# Dynamic Input Label
input_label_map = {
    "Webpage Scraper": "Enter URL to Scrape",
    "Lens (Reverse Image)": "Enter Image URL",
    "Reviews": "Enter Place ID (starts with 'Ch...') or CID",
    "Maps": "Search Query or Lat,Long"
}
input_label = input_label_map.get(search_type, "Search Query")
placeholder_text = "Enter URL..." if "URL" in input_label else "Type here..."

col1, col2 = st.columns([4, 1])
with col1:
    query_input = st.text_input(input_label, placeholder=placeholder_text)
with col2:
    run_btn = st.button("🚀 Run", type="primary", use_container_width=True)

if run_btn and query_input and api_key:
    with st.spinner("Connecting to Google Serper API..."):
        data = query_serper(api_key, query_input, search_type, location, gl, hl, num)
        
        if "error" in data:
            st.error(f"API Error: {data['error']}")
        else:
            # --- RESULT PARSERS ---
            
            # 1. VISUALS (Images / Lens)
            if search_type in ["Images", "Lens (Reverse Image)"]:
                key = "images" if search_type == "Images" else "images"
                df = safe_normalize(data, key)
                if not df.empty:
                    st.success(f"Found {len(df)} images.")
                    cols = st.columns(4)
                    for i, row in df.iterrows():
                        with cols[i%4]:
                            img = row.get('imageUrl') or row.get('thumbnailUrl')
                            if img: st.image(img, use_container_width=True)
                            st.caption(f"[{row.get('title', 'Link')}]({row.get('link', '#')})")
            
            # 2. VIDEOS
            elif search_type == "Videos":
                df = safe_normalize(data, "videos")
                for i, row in df.iterrows():
                    with st.container():
                        c1, c2 = st.columns([1, 3])
                        with c1:
                            if 'imageUrl' in row: st.image(row['imageUrl'], use_container_width=True)
                        with c2:
                            st.markdown(f"### [{row.get('title')}]({row.get('link')})")
                            st.caption(f"{row.get('channel', '')} • {row.get('date', '')}")
                            st.write(row.get('snippet', ''))

            # 3. SHOPPING
            elif search_type == "Shopping":
                df = safe_normalize(data, "shopping")
                cols = st.columns(4)
                for i, row in df.iterrows():
                    with cols[i%4]:
                        if 'imageUrl' in row: st.image(row['imageUrl'], use_container_width=True)
                        st.markdown(f"**{row.get('price', '')}**")
                        st.markdown(f"[{row.get('title')}]({row.get('link')})")
                        st.caption(row.get('source', ''))

            # 4. PLACES / MAPS
            elif search_type in ["Places", "Maps"]:
                key = "places"
                df = safe_normalize(data, key)
                if not df.empty:
                    # Try to map it
                    if 'latitude' in df.columns:
                        st.map(df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})[['lat', 'lon']].dropna())
                    
                    st.dataframe(df[['title', 'address', 'rating', 'ratingCount', 'category']], use_container_width=True)

            # 5. ACADEMIC (Scholar / Patents)
            elif search_type in ["Scholar", "Patents"]:
                key = "organic" # Serper often returns these under 'organic' or specific keys
                if search_type == "Patents" and "organic" not in data: key = "patents" # fallback
                
                results = data.get(key, [])
                for res in results:
                    st.markdown(f"### [{res.get('title')}]({res.get('link')})")
                    st.markdown(f"<span class='tag'>{res.get('publication_info', {}).get('summary', '')}</span>", unsafe_allow_html=True)
                    st.write(res.get('snippet', ''))
                    st.divider()

            # 6. SCRAPER / WEBPAGE
            elif search_type == "Webpage Scraper":
                st.subheader("📄 Scraped Content")
                st.code(data.get("text", "No text content found."), language="text")
                with st.expander("View HTML Source"):
                    st.code(data.get("html", "")[:2000] + "...", language="html")
            
            # 7. AUTOCOMPLETE
            elif search_type == "Autocomplete":
                st.subheader("Suggestions")
                suggs = data.get("suggestions", [])
                for s in suggs:
                    st.write(f"👉 {s.get('value')}")

            # 8. REVIEWS
            elif search_type == "Reviews":
                reviews = data.get("reviews", [])
                for r in reviews:
                    st.markdown(f"**{r.get('author', 'User')}** {r.get('stars', '')}⭐")
                    st.info(r.get('text', ''))
                    st.caption(r.get('date', ''))

            # DEFAULT (News, Search)
            else:
                key = "news" if search_type == "News" else "organic"
                df = safe_normalize(data, key)
                if not df.empty:
                    for i, row in df.iterrows():
                        st.markdown(f"### [{row.get('title')}]({row.get('link')})")
                        st.caption(f"{row.get('source', '')} • {row.get('date', '')}")
                        st.write(row.get('snippet', ''))
                        st.divider()
            
            # RAW DATA DUMP (Always available)
            with st.expander("🔍 View Raw JSON Response"):
                st.json(data)

elif run_btn and not api_key:
    st.warning("Please enter your API Key in the sidebar.")