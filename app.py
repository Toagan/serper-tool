import streamlit as st
import requests
import pandas as pd
import json

# --- 1. APP CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Serper.dev Intelligence Hub",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for cleaner cards and metrics
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 24px; }
    .result-card {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border: 1px solid #333;
    }
    .price-tag {
        background-color: #4CAF50;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. BACKEND FUNCTIONS (OPTIMIZED) ---

# @st.cache_data ensures we don't pay for the same search twice in one session
@st.cache_data(show_spinner=False)
def query_serper(api_key, query, search_type, location, gl, hl, num_results):
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
    
    # Only add location if it's specific
    if location and location != "Auto":
        payload["location"] = location

    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() # Raise error for bad status codes
        return response.json()
    except requests.exceptions.HTTPError as err:
        if response.status_code == 401:
            return {"error": "⛔ Unauthorized: Invalid API Key"}
        if response.status_code == 403:
            return {"error": "⛔ Forbidden: API Key invalid or out of credits"}
        return {"error": f"API Error: {err}"}
    except Exception as e:
        return {"error": f"Connection Error: {e}"}

def clean_dataframe(df):
    """Cleans up columns for the Analyst View"""
    # Drop useless columns that clutter the view
    drop_cols = ['position', 'sitelinks', 'snippetHighlighted']
    for col in drop_cols:
        if col in df.columns:
            df = df.drop(columns=[col])
    return df

# --- 3. UI LAYOUT ---

# Sidebar
with st.sidebar:
    st.header("🕵️‍♂️ Control Panel")
    
    # API Key Management
    if "serper_api_key" not in st.session_state:
        st.session_state.serper_api_key = ""
    
    api_key = st.text_input("Serper API Key", type="password", value=st.session_state.serper_api_key, help="Get key at serper.dev")
    if api_key:
        st.session_state.serper_api_key = api_key

    st.divider()
    
    # Search Parameters
    st.subheader("🌍 Geography & Language")
    geo_mode = st.radio("Location Mode", ["Quick Select", "Advanced Custom"], horizontal=True)
    
    location_str = "Auto"
    gl = "us"
    hl = "en"
    
    if geo_mode == "Quick Select":
        c_map = {"🇺🇸 United States": "us", "🇬🇧 United Kingdom": "gb", "🇩🇪 Germany": "de", "🇨🇦 Canada": "ca", "🇫🇷 France": "fr"}
        sel_c = st.selectbox("Country", list(c_map.keys()))
        gl = c_map[sel_c]
    else:
        location_str = st.text_input("City/Region", placeholder="e.g. Manhattan, NY")
        col_g1, col_g2 = st.columns(2)
        gl = col_g1.text_input("Country Code", "us", max_chars=2, help="2-letter code (e.g. 'us')")
        hl = col_g2.text_input("Lang Code", "en", max_chars=2, help="2-letter code (e.g. 'en')")

    st.divider()
    num_results = st.slider("Max Results", 10, 100, 20)

# Main Area
st.title("Serper Intelligence Hub")
st.caption("Top 1% Engineering Implementation • v2.0 Optimized")

col_search, col_type = st.columns([3, 1])
with col_search:
    query = st.text_input("Search Query", placeholder="What are you looking for?", key="query_input")
with col_type:
    search_type = st.selectbox("Vertical", ["Organic Search", "News", "Places (Maps)", "Images", "Shopping"])

# Action
if st.button("🔍 Execute Search", type="primary"):
    if not api_key:
        st.warning("⚠️ Please enter your API Key in the sidebar.")
    elif not query:
        st.warning("⚠️ Please enter a query.")
    else:
        with st.spinner(f"Querying Google {search_type} via Serper..."):
            data = query_serper(api_key, query, search_type, location_str, gl, hl, num_results)
            
            if "error" in data:
                st.error(data["error"])
            else:
                # Determine result key
                res_key_map = {
                    "Organic Search": "organic", "News": "news", 
                    "Places (Maps)": "places", "Images": "images", "Shopping": "shopping"
                }
                target_key = res_key_map[search_type]
                results = data.get(target_key, [])
                
                if not results:
                    st.warning(f"No results found for '{query}'")
                else:
                    # Metrics
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Results", len(results))
                    if "searchParameters" in data:
                        m2.metric("Location Used", data["searchParameters"].get("gl", "N/A").upper())
                        m3.metric("Language", data["searchParameters"].get("hl", "N/A").upper())
                    st.divider()

                    # Parse to DF
                    df = pd.json_normalize(results)
                    
                    # --- VIEW LOGIC BASED ON TYPE ---
                    
                    # 1. PLACES VIEW (Map + List)
                    if search_type == "Places (Maps)":
                        # Map Logic: Streamlit requires 'lat' and 'lon' columns
                        if 'latitude' in df.columns and 'longitude' in df.columns:
                            map_df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
                            st.map(map_df[['lat', 'lon']].dropna())
                        
                        st.subheader("📍 Locations Found")
                        for i, row in df.iterrows():
                            with st.expander(f"{i+1}. {row.get('title', 'Unknown')}"):
                                st.write(f"**Address:** {row.get('address', 'N/A')}")
                                st.write(f"**Rating:** ⭐ {row.get('rating', 'N/A')} ({row.get('ratingCount', 0)} reviews)")
                    
                    # 2. IMAGES / SHOPPING VIEW (Grid)
                    elif search_type in ["Images", "Shopping"]:
                        cols = st.columns(4) # 4 Column Grid
                        for i, row in df.iterrows():
                            with cols[i % 4]:
                                # Show Image
                                img_url = row.get('imageUrl') or row.get('thumbnailUrl')
                                if img_url:
                                    st.image(img_url, use_container_width=True)
                                
                                # Show Title/Price
                                if search_type == "Shopping":
                                    price = row.get('price', '')
                                    st.markdown(f"<span class='price-tag'>{price}</span>", unsafe_allow_html=True)
                                    st.caption(row.get('source', ''))
                                
                                st.markdown(f"[{row.get('title', 'Link')}]({row.get('link', '#')})")

                    # 3. DEFAULT LIST VIEW (Search, News)
                    else:
                        for i, row in df.iterrows():
                            st.markdown(f"### [{row.get('title', 'No Title')}]({row.get('link', '#')})")
                            st.caption(f"{row.get('source', '')} • {row.get('date', '')}")
                            if 'snippet' in row:
                                st.write(row['snippet'])
                            st.divider()

                    # RAW DATA EXPANDER
                    with st.expander("📊 View Raw Data (Analyst Mode)"):
                        clean_df = clean_dataframe(df)
                        st.dataframe(clean_df)
                        csv = clean_df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download CSV", csv, "results.csv", "text/csv")