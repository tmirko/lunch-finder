"""
Lunch Finder - A Streamlit app to find lunch menu options around your office.
Designed for Vienna, Austria with German to English translations.
"""
import streamlit as st
from datetime import datetime
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers import NiceGuysProvider, MenuItem, DailyMenu
from utils import Translator, ImageSearch


# Page configuration
st.set_page_config(
    page_title="🍽️ Lunch Finder",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode and clean UI
st.markdown("""
<style>
    /* Dark mode background */
    .stApp {
        background-color: #1a1a2e;
        color: #eaeaea;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #16162a;
        padding: 1rem;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stCheckbox label {
        color: #a0a0a0 !important;
        font-size: 0.9rem !important;
    }
    
    /* Sidebar header - bigger */
    .sidebar-header {
        font-size: 1.6rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 1.5rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid #3d3d5c;
    }
    
    /* Dish names - bigger, prominent */
    .dish-german {
        font-size: 1.5rem;
        font-weight: 600;
        color: #ffffff;
        margin: 0;
        padding: 0;
        line-height: 1.4;
    }
    .dish-english {
        font-size: 1.5rem;
        font-weight: 400;
        color: #b0b0b0;
        font-style: italic;
        margin: 0;
        padding: 0;
        line-height: 1.4;
    }
    .dish-price {
        font-size: 1rem;
        color: #ffd700;
        margin-top: 0.5rem;
    }
    
    /* Provider section */
    .provider-name {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 1rem;
    }
    
    /* Links */
    a {
        color: #6c9fff !important;
        font-size: 0.85rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Divider */
    hr {
        border-color: #3d3d5c;
        margin: 1rem 0;
    }
    
    /* Image container */
    .img-container {
        position: relative;
        display: inline-block;
    }
    
    .dish-thumb {
        width: 280px;
        height: 200px;
        object-fit: cover;
        border-radius: 10px;
        cursor: pointer;
        transition: opacity 0.3s ease;
    }
    
    .dish-thumb:hover {
        opacity: 0.7;
    }
    
    /* Overlay for expanded image - centered on screen */
    .img-container::after {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.85);
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease;
        z-index: 9998;
        pointer-events: none;
    }
    
    .img-container:hover::after {
        opacity: 1;
        visibility: visible;
    }
    
    /* Expanded image - fixed center */
    .img-expanded {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        max-width: 80vw;
        max-height: 80vh;
        object-fit: contain;
        border-radius: 12px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.9);
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease;
        z-index: 9999;
        pointer-events: none;
    }
    
    .img-container:hover .img-expanded {
        opacity: 1;
        visibility: visible;
    }
</style>
""", unsafe_allow_html=True)


def get_current_weekday() -> str:
    """Get the current day of the week (Monday-Friday)."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = days[datetime.now().weekday()]
    
    # If it's weekend, default to Monday
    if today in ["Saturday", "Sunday"]:
        return "Monday"
    return today


def get_day_index(day: str) -> int:
    """Get the index of a day for the selectbox."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    return days.index(day) if day in days else 0


@st.cache_resource
def get_translator() -> Translator:
    """Get cached translator instance."""
    return Translator()


@st.cache_resource
def get_image_search() -> ImageSearch:
    """Get cached image search instance."""
    return ImageSearch()


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_provider_menu(_provider, day: str) -> DailyMenu:
    """Get cached menu for a provider and day."""
    return _provider.get_menu(day)


@st.cache_data(ttl=86400)  # Cache translations for 24 hours
def translate_text(text: str) -> str:
    """Translate text from German to English."""
    translator = get_translator()
    return translator.translate(text)


@st.cache_data(ttl=3600)  # Cache images for 1 hour  
def get_dish_image(query: str) -> str:
    """Get image URL for a dish."""
    image_search = get_image_search()
    return image_search.search_image(query)


def display_menu_item(item: MenuItem, show_image: bool = True, item_index: int = 0):
    """Display a single menu item with translation and image."""
    
    # Translate if not already translated
    if not item.name_english:
        item.name_english = translate_text(item.name_german)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # German name
        st.markdown(f'<p class="dish-german">🇦🇹 {item.name_german}</p>', unsafe_allow_html=True)
        # English translation - same size
        st.markdown(f'<p class="dish-english">🇬🇧 {item.name_english}</p>', unsafe_allow_html=True)
        # Price if available
        if item.price:
            st.markdown(f'<p class="dish-price">💰 {item.price}</p>', unsafe_allow_html=True)
    
    with col2:
        if show_image:
            image_url = get_dish_image(item.name_german)
            if image_url:
                try:
                    # Display thumbnail with hover-to-expand overlay
                    st.markdown(
                        f'''<div class="img-container">
                            <img src="{image_url}" class="dish-thumb" alt="{item.name_german}">
                            <img src="{image_url}" class="img-expanded" alt="{item.name_german}">
                        </div>''',
                        unsafe_allow_html=True
                    )
                except Exception:
                    pass
    
    st.markdown("<hr>", unsafe_allow_html=True)


def main():
    """Main application."""
    
    # Sidebar with all controls
    with st.sidebar:
        st.markdown('<p class="sidebar-header">🍽️ Lunch Finder</p>', unsafe_allow_html=True)
        
        # Day selector
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        day_labels = {
            "Monday": "Monday / Montag",
            "Tuesday": "Tuesday / Dienstag", 
            "Wednesday": "Wednesday / Mittwoch",
            "Thursday": "Thursday / Donnerstag",
            "Friday": "Friday / Freitag"
        }
        
        current_day = get_current_weekday()
        default_index = get_day_index(current_day)
        
        selected_day = st.selectbox(
            "📅 Day",
            options=days,
            index=default_index,
            format_func=lambda x: day_labels.get(x, x)
        )
        
        st.markdown("")  # Spacer
        
        # Image toggle
        show_images = st.checkbox("🖼️ Show images", value=True)
        
        st.markdown("---")
        
        # Providers info
        st.markdown("**Restaurants**")
        providers = [
            NiceGuysProvider(),
        ]
        for provider in providers:
            st.markdown(f"📍 [{provider.name}]({provider.url})")
    
    # Main content - dishes only
    for provider in providers:
        try:
            menu = get_provider_menu(provider, selected_day)
            
            if menu.items:
                for idx, item in enumerate(menu.items):
                    display_menu_item(item, show_image=show_images, item_index=idx)
            else:
                st.markdown('<p style="color: #888; font-size: 1rem;">No menu available for this day</p>', unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown(f'<p style="color: #ff6b6b; font-size: 1rem;">Error loading menu</p>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
