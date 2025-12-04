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
    initial_sidebar_state="collapsed"
)

# Custom CSS for better mobile experience
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .dish-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .dish-name-german {
        font-size: 1.4rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .dish-name-english {
        font-size: 1.1rem;
        font-style: italic;
        opacity: 0.9;
        margin-bottom: 0.5rem;
    }
    .dish-price {
        font-size: 1.2rem;
        font-weight: bold;
        color: #ffd700;
    }
    .provider-header {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: white;
    }
    .stSelectbox > div > div {
        font-size: 1.2rem;
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


@st.cache_data(ttl=86400)  # Cache images for 24 hours  
def get_dish_image(query: str) -> str:
    """Get image URL for a dish."""
    image_search = get_image_search()
    return image_search.search_image(query)


def display_menu_item(item: MenuItem, show_image: bool = True):
    """Display a single menu item with translation and image."""
    
    # Translate if not already translated
    if not item.name_english:
        item.name_english = translate_text(item.name_german)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # German name (original)
        st.markdown(f"### 🇦🇹 {item.name_german}")
        
        # English translation
        st.markdown(f"*🇬🇧 {item.name_english}*")
        
        # Price if available
        if item.price:
            st.markdown(f"**💰 {item.price}**")
        
        # Description if available
        if item.description:
            st.markdown(f"_{item.description}_")
    
    with col2:
        if show_image:
            image_url = get_dish_image(item.name_german)
            if image_url:
                try:
                    st.image(image_url, width=150, caption="")
                except Exception:
                    st.markdown("🍽️")
    
    st.divider()


def main():
    """Main application."""
    
    # Header
    st.title("🍽️ Lunch Finder Vienna")
    st.markdown("*Find your perfect lunch near the office!*")
    
    # Day selector
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    day_labels = {
        "Monday": "🌙 Monday / Montag",
        "Tuesday": "🔥 Tuesday / Dienstag", 
        "Wednesday": "🌊 Wednesday / Mittwoch",
        "Thursday": "⚡ Thursday / Donnerstag",
        "Friday": "🎉 Friday / Freitag"
    }
    
    current_day = get_current_weekday()
    default_index = get_day_index(current_day)
    
    selected_day = st.selectbox(
        "📅 Select Day",
        options=days,
        index=default_index,
        format_func=lambda x: day_labels.get(x, x)
    )
    
    # Image toggle
    show_images = st.checkbox("🖼️ Show dish images", value=True)
    
    st.markdown("---")
    
    # Initialize providers
    providers = [
        NiceGuysProvider(),
    ]
    
    # Display menus from all providers
    for provider in providers:
        with st.expander(f"🏪 {provider.name}", expanded=True):
            st.markdown(f"[Visit website]({provider.url})")
            
            try:
                with st.spinner(f"Loading menu from {provider.name}..."):
                    menu = get_provider_menu(provider, selected_day)
                
                if menu.items:
                    st.success(f"Found {len(menu.items)} dishes for {selected_day}")
                    
                    for item in menu.items:
                        display_menu_item(item, show_image=show_images)
                else:
                    st.warning(f"No menu items found for {selected_day}. The menu might not be available yet.")
                    st.info("💡 Tip: The restaurant updates their menu weekly. Try again later or check their website directly.")
                    
            except Exception as e:
                st.error(f"Error loading menu: {str(e)}")
                st.info("Please try again later or check the restaurant's website directly.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 0.8rem;'>
            Made with ❤️ in Vienna | Data refreshes hourly
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
