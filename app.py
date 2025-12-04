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

from providers import NiceGuysProvider, FoodGardenProvider, MenuItem, DailyMenu
from utils import Translator, ImageSearch


# Page configuration
st.set_page_config(
    page_title="Lunch Finder",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode and mobile-first UI
st.markdown("""
<style>
    /* Dark mode background */
    .stApp {
        background-color: #1a1a2e;
        color: #eaeaea;
    }
    
    /* Main content area - tight padding for mobile */
    .main .block-container {
        padding-top: 0.5rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
        max-width: 100%;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #16162a;
        padding: 0.5rem;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stCheckbox label {
        color: #a0a0a0 !important;
        font-size: 0.85rem !important;
    }
    
    /* Sidebar header */
    .sidebar-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #3d3d5c;
    }
    
    /* Dish row container */
    .dish-row {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        padding: 0.5rem 0;
        border-bottom: 1px solid #2d2d44;
        margin-bottom: 0.5rem;
    }
    
    .dish-text {
        flex: 1;
        min-width: 0;
    }
    
    /* Dish names - compact for mobile */
    .dish-german {
        font-size: 1.1rem;
        font-weight: 600;
        color: #ffffff;
        margin: 0;
        padding: 0;
        line-height: 1.3;
    }
    .dish-english {
        font-size: 1.1rem;
        font-weight: 400;
        color: #a0a0a0;
        font-style: italic;
        margin: 0;
        padding: 0;
        line-height: 1.3;
    }
    .dish-location {
        font-size: 0.8rem;
        color: #6c9fff;
        margin: 0.2rem 0 0 0;
        padding: 0;
    }
    .dish-price {
        font-size: 0.85rem;
        color: #ffd700;
        margin: 0.2rem 0 0 0;
    }
    
    /* Links */
    a {
        color: #6c9fff !important;
        font-size: 0.8rem;
        text-decoration: none;
    }
    
    /* Hide Streamlit branding but keep header */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Hide default streamlit padding */
    .block-container {
        padding-bottom: 0 !important;
    }
    
    /* Image container - right side */
    .img-container {
        flex-shrink: 0;
    }
    
    .dish-thumb {
        width: 120px;
        height: 90px;
        object-fit: cover;
        border-radius: 8px;
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
        background: rgba(0, 0, 0, 0.9);
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
        max-width: 90vw;
        max-height: 85vh;
        object-fit: contain;
        border-radius: 10px;
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
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .dish-german, .dish-english {
            font-size: 1rem;
        }
        .dish-thumb {
            width: 100px;
            height: 75px;
        }
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


@st.cache_resource
def get_providers():
    """Get cached provider instances."""
    return {
        "The Nice Guys": NiceGuysProvider(),
        "Food Garden": FoodGardenProvider(),
    }


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_provider_menu(provider_name: str, day: str) -> DailyMenu:
    """Get cached menu for a provider and day."""
    providers = get_providers()
    provider = providers.get(provider_name)
    if provider:
        return provider.get_menu(day)
    return DailyMenu(day=day, items=[], provider_name=provider_name)


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


def display_menu_item(item: MenuItem, provider_name: str, show_image: bool = True):
    """Display a single menu item with translation, location, and image."""
    import html
    
    # Translate if not already translated
    if not item.name_english:
        item.name_english = translate_text(item.name_german)
    
    # Escape HTML special characters in text
    name_german_safe = html.escape(item.name_german)
    name_english_safe = html.escape(item.name_english)
    provider_safe = html.escape(provider_name)
    
    # Get image URL
    image_url = ""
    if show_image:
        image_url = get_dish_image(item.name_german)
    
    # Build image HTML
    image_html = ""
    if image_url:
        image_html = f'''<div class="img-container"><img src="{html.escape(image_url)}" class="dish-thumb" alt="{name_german_safe}"><img src="{html.escape(image_url)}" class="img-expanded" alt="{name_german_safe}"></div>'''
    
    # Build price HTML
    price_html = f'<p class="dish-price">💰 {html.escape(item.price)}</p>' if item.price else ''
    
    # Render dish row with flexbox layout
    st.markdown(
        f'''<div class="dish-row"><div class="dish-text"><p class="dish-german">🇦🇹 {name_german_safe}</p><p class="dish-english">🇬🇧 {name_english_safe}</p><p class="dish-location">📍 {provider_safe}</p>{price_html}</div>{image_html}</div>''',
        unsafe_allow_html=True
    )


def main():
    """Main application."""
    
    # Get cached providers
    providers = get_providers()
    
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
        for name, provider in providers.items():
            st.markdown(f"📍 [{provider.name}]({provider.url})")
    
    # Main content - dishes only
    for provider_name, provider in providers.items():
        try:
            menu = get_provider_menu(provider_name, selected_day)
            
            if menu.items:
                for item in menu.items:
                    display_menu_item(item, provider_name=provider_name, show_image=show_images)
            else:
                st.markdown(f'<p style="color: #888; font-size: 0.9rem;">No menu from {provider_name} for this day</p>', unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown(f'<p style="color: #ff6b6b; font-size: 0.9rem;">Error loading {provider_name} menu</p>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
