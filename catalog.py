import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import requests
from io import BytesIO

flags = {
    "Andorra": ":flag-ad:",
    "Austria": ":flag-at:",
    "Belgium": ":flag-be:",
    "Croatia": ":flag-hr:",
    "Cyprus": ":flag-cy:",
    "Estonia": ":flag-ee:",
    "Euro area countries": "Euro area countries",
    "Finland": ":flag-fi:",
    "France": ":flag-fr:",
    "Germany": ":flag-de:",
    "Greece": ":flag-gr:",
    "Ireland": ":flag-ie:",
    "Italy": ":flag-it:",
    "Latvia": ":flag-lv:",
    "Lithuania": ":flag-lt:",
    "Luxembourg": ":flag-lu:",
    "Malta": ":flag-mt:",
    "Monaco": ":flag-mc:",
    "Netherlands": ":flag-nl:",
    "Portugal": ":flag-pt:",
    "San Marino": ":flag-sm:",
    "Slovakia": ":flag-sk:",
    "Slovenia": ":flag-si:",
    "Spain": ":flag-es:",
    "Vatican City": ":flag-va:"
}

# Page configuration
st.set_page_config(
    page_title="Euro Coins Catalog",
    page_icon="🪙",
    layout="wide"
)

@st.cache_data
def load_data():
    """Load the coins catalog data"""
    try:
        df = pd.read_csv('data/catalog.csv')
        return df
    except FileNotFoundError:
        st.error("Catalog file not found. Please ensure 'data/catalog.csv' exists.")
        return pd.DataFrame()

def format_value(value):
    """Format coin value for display"""
    if value >= 1:
        return f"€{value:.0f}"
    else:
        return f"{int(value * 100)}¢"

def format_country_with_flag(country):
    """Format country name with flag emoji"""
    flag = flags.get(country, "")
    if flag and flag != country:  # Don't add flag if it's the same as country name (like "Euro area countries")
        return f"{flag} {country}"
    else:
        return country

def display_coin_image(image_url, coin_id, width=150):
    """Display coin image with error handling"""
    try:
        if image_url and image_url.strip():
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                # Center the image
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.image(img, width=width, caption=f"ID: {coin_id}")
            else:
                # Simple placeholder for unavailable image
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown(f'<div style="height: {width}px; display: flex; align-items: center; justify-content: center; border: 2px dashed #ccc; border-radius: 8px; background-color: #f8f8f8;"><span style="color: #888;">🖼️ Image unavailable</span></div>', unsafe_allow_html=True)
                    st.caption(f"ID: {coin_id}")
        else:
            # Simple placeholder for no image
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f'<div style="height: {width}px; display: flex; align-items: center; justify-content: center; border: 2px dashed #ccc; border-radius: 8px; background-color: #f8f8f8;"><span style="color: #888;">🖼️ No image</span></div>', unsafe_allow_html=True)
                st.caption(f"ID: {coin_id}")
    except Exception as e:
        # Simple placeholder for image load error
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f'<div style="height: {width}px; display: flex; align-items: center; justify-content: center; border: 2px dashed #ccc; border-radius: 8px; background-color: #f8f8f8;"><span style="color: #888;">🖼️ Image load error</span></div>', unsafe_allow_html=True)
            st.caption(f"ID: {coin_id}")

def main():
    st.title("🪙 Euro Coins Catalog")
    st.markdown("Explore the comprehensive catalog of Euro coins including regular and commemorative issues.")
    
    # Load data
    df = load_data()
    
    if df.empty:
        st.stop()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Coin type filter
    coin_types = {'All': 'All', 'Regular Coins (RE)': 'RE', 'Commemorative Coins (CC)': 'CC'}
    selected_type = st.sidebar.selectbox("Coin Type", list(coin_types.keys()))
    
    # Country filter
    countries = ['All'] + sorted(df['country'].unique().tolist())
    selected_country = st.sidebar.selectbox("Country", countries)
    
    # Year filter
    years = ['All'] + sorted(df['year'].unique().tolist(), reverse=True)
    selected_year = st.sidebar.selectbox("Year", years)
    
    # Value filter
    values = ['All'] + sorted(df['value'].unique().tolist(), reverse=True)
    selected_value = st.sidebar.selectbox("Value", values)
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_type != 'All':
        filtered_df = filtered_df[filtered_df['type'] == coin_types[selected_type]]
    
    if selected_country != 'All':
        filtered_df = filtered_df[filtered_df['country'] == selected_country]
    
    if selected_year != 'All':
        filtered_df = filtered_df[filtered_df['year'] == selected_year]
    
    if selected_value != 'All':
        filtered_df = filtered_df[filtered_df['value'] == selected_value]
    
    # Display statistics
    st.markdown("### 📊 Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Coins", len(filtered_df))
    
    with col2:
        regular_count = len(filtered_df[filtered_df['type'] == 'RE'])
        st.metric("Regular Coins", regular_count)
    
    with col3:
        commemorative_count = len(filtered_df[filtered_df['type'] == 'CC'])
        st.metric("Commemorative Coins", commemorative_count)
    
    with col4:
        countries_count = len(filtered_df['country'].unique())
        st.metric("Countries", countries_count)
    
    # Display mode selection
    st.markdown("### 📋 Display Options")
    display_mode = st.radio(
        "Choose display mode:",
        ["Table View", "Card View", "Gallery View"],
        horizontal=True
    )
    
    if len(filtered_df) == 0:
        st.warning("No coins match the selected filters.")
        return
    
    # Display results based on selected mode
    if display_mode == "Table View":
        st.markdown("### 📋 Coins Table")
        
        # Prepare display dataframe
        display_df = filtered_df.copy()
        
        # Format the type column for display
        display_df['type'] = display_df['type'].map({'RE': 'Regular', 'CC': 'Commemorative'})
        
        # # Format country names with flags
        # display_df['country'] = display_df['country'].apply(format_country_with_flag)
        
        # Show the table with images
        st.data_editor(
            display_df,
            hide_index=True,
            column_config={
                "type": st.column_config.TextColumn(label="Type"),
                "year": st.column_config.NumberColumn(label="Year", format="%d"),
                "country": st.column_config.TextColumn(label="Country"),
                "series": st.column_config.TextColumn(label="Series"),
                "value": st.column_config.NumberColumn(label="Value", format="%.2f"),
                "id": st.column_config.TextColumn(label="ID"),
                "image": st.column_config.ImageColumn(label="Image"),
                "feature": st.column_config.TextColumn(label="Feature"),
                "volume": st.column_config.TextColumn(label="Volume")
            },
            disabled=True,
            column_order=('image', 'type', 'year', 'country', 'value', 'series', 'feature', 'volume', 'id'),
            use_container_width=True
        )
    
    elif display_mode == "Card View":
        st.markdown("### 🎴 Coins Cards")
        
        # Pagination
        coins_per_page = 12
        total_pages = (len(filtered_df) + coins_per_page - 1) // coins_per_page
        
        if total_pages > 1:
            page = st.selectbox("Page", range(1, total_pages + 1)) - 1
        else:
            page = 0
        
        start_idx = page * coins_per_page
        end_idx = min(start_idx + coins_per_page, len(filtered_df))
        page_df = filtered_df.iloc[start_idx:end_idx]
        
        # Display cards in grid
        cols = st.columns(3)
        
        for idx, (_, coin) in enumerate(page_df.iterrows()):
            col = cols[idx % 3]
            c_type = 'Regular' if coin['type'] == 'RE' else 'Commemorative'
            c_country = coin['country']
            c_country_flag = format_country_with_flag(c_country)
            c_series = coin['series'] if pd.notna(coin['series']) else '---'
            c_value = format_value(coin['value'])
            c_year = coin['year']
            c_id = coin['id']
            c_image = coin['image']
            c_feature = coin['feature'] if pd.notna(coin['feature']) else '---'
            c_volume = coin['volume'] if pd.notna(coin['volume']) else '---'

            with col:
                with st.container():
                    st.markdown(f"{c_country_flag} ({c_year})")
                    display_coin_image(c_image, c_id, width=160)
                    st.markdown(f"**Type:** {c_value} / {c_type}")
                    st.markdown(f"**Series:** {c_series}")
                    st.markdown(f"**Volume:** {c_volume}")
                    st.markdown(f"**Feature:** {c_feature}")
                    st.markdown("---")
    
    else:  # Gallery View
        st.markdown("### 🖼️ Coins Gallery")
        
        # Pagination for gallery
        coins_per_page = 20
        total_pages = (len(filtered_df) + coins_per_page - 1) // coins_per_page
        
        if total_pages > 1:
            page = st.selectbox("Page", range(1, total_pages + 1)) - 1
        else:
            page = 0
        
        start_idx = page * coins_per_page
        end_idx = min(start_idx + coins_per_page, len(filtered_df))
        page_df = filtered_df.iloc[start_idx:end_idx]
        
        # Display images in grid
        cols = st.columns(5)
        
        for idx, (_, coin) in enumerate(page_df.iterrows()):
            col = cols[idx % 5]
            
            with col:
                st.markdown(f"**{format_country_with_flag(coin['country'])}**")
                st.markdown(f"{format_value(coin['value'])} ({coin['year']})")
                display_coin_image(coin['image'], coin['id'])
                if coin['feature'] and pd.notna(coin['feature']) and coin['type'] == 'CC':
                    st.caption(coin['feature'][:50] + "..." if len(str(coin['feature'])) > 50 else coin['feature'])
    
    # Search functionality
    st.markdown("### 🔍 Search")
    search_term = st.text_input("Search in features, countries, or series:")
    
    if search_term:
        search_results = df[
            df['country'].str.contains(search_term, case=False, na=False) |
            df['feature'].str.contains(search_term, case=False, na=False) |
            df['series'].str.contains(search_term, case=False, na=False)
        ]
        
        if len(search_results) > 0:
            st.markdown(f"Found {len(search_results)} results:")
            
            # Display search results in a compact format
            for _, coin in search_results.head(10).iterrows():
                with st.expander(f"{format_country_with_flag(coin['country'])} - {format_value(coin['value'])} ({coin['year']})"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        display_coin_image(coin['image'], coin['id'])
                    
                    with col2:
                        st.markdown(f"**Type:** {'Regular' if coin['type'] == 'RE' else 'Commemorative'}")
                        st.markdown(f"**Series:** {coin['series']}")
                        if coin['feature'] and pd.notna(coin['feature']):
                            st.markdown(f"**Feature:** {coin['feature']}")
                        if coin['volume'] and pd.notna(coin['volume']):
                            st.markdown(f"**Volume:** {coin['volume']}")
                        st.markdown(f"**ID:** `{coin['id']}`")
            
            if len(search_results) > 10:
                st.info(f"Showing first 10 results. Total found: {len(search_results)}")
        else:
            st.warning("No results found for your search term.")

if __name__ == "__main__":
    main()
