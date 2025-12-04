"""
Nice Guys menu provider.
Fetches and parses the weekly menu from https://www.theniceguys.at/data/wochenmenue.pdf
"""
import requests
import io
import re
from typing import Optional
from PyPDF2 import PdfReader
from providers.base import MenuProvider, MenuItem, DailyMenu


class NiceGuysProvider(MenuProvider):
    """Provider for The Nice Guys restaurant in Vienna."""
    
    MENU_URL = "https://www.theniceguys.at/data/wochenmenue.pdf"
    
    # German day names mapping
    DAY_MAPPING = {
        "Monday": "Montag",
        "Tuesday": "Dienstag", 
        "Wednesday": "Mittwoch",
        "Thursday": "Donnerstag",
        "Friday": "Freitag"
    }
    
    GERMAN_TO_ENGLISH_DAYS = {v: k for k, v in DAY_MAPPING.items()}
    
    def __init__(self):
        self._weekly_menu: Optional[dict[str, DailyMenu]] = None
    
    @property
    def name(self) -> str:
        return "The Nice Guys"
    
    @property
    def url(self) -> str:
        return "https://www.theniceguys.at"
    
    def get_menu(self, day: str) -> DailyMenu:
        """Get menu for a specific day."""
        if self._weekly_menu is None:
            self._weekly_menu = self.fetch_weekly_menu()
        
        return self._weekly_menu.get(day, DailyMenu(day=day, items=[], provider_name=self.name))
    
    def fetch_weekly_menu(self) -> dict[str, DailyMenu]:
        """Fetch and parse the weekly menu PDF."""
        try:
            # Download the PDF
            response = requests.get(self.MENU_URL, timeout=10)
            response.raise_for_status()
            
            # Parse PDF
            pdf_file = io.BytesIO(response.content)
            reader = PdfReader(pdf_file)
            
            # Extract text from all pages
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            return self._parse_menu_text(full_text)
            
        except requests.RequestException as e:
            print(f"Error fetching menu: {e}")
            return self._empty_weekly_menu()
        except Exception as e:
            print(f"Error parsing menu: {e}")
            return self._empty_weekly_menu()
    
    def _empty_weekly_menu(self) -> dict[str, DailyMenu]:
        """Return empty menu structure."""
        return {
            day: DailyMenu(day=day, items=[], provider_name=self.name)
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    
    def _parse_menu_text(self, text: str) -> dict[str, DailyMenu]:
        """Parse the extracted PDF text into menu items."""
        weekly_menu = self._empty_weekly_menu()
        
        # Clean up the text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        current_day_english = None
        current_items = []
        
        # German day names to look for
        german_days = list(self.GERMAN_TO_ENGLISH_DAYS.keys())
        
        for line in lines:
            # Check if this line starts a new day
            day_found = None
            for german_day in german_days:
                if german_day.lower() in line.lower():
                    day_found = self.GERMAN_TO_ENGLISH_DAYS[german_day]
                    break
            
            if day_found:
                # Save previous day's items with correct prices
                if current_day_english and current_items:
                    self._assign_prices(current_items)
                    weekly_menu[current_day_english] = DailyMenu(
                        day=current_day_english,
                        items=current_items,
                        provider_name=self.name
                    )
                
                current_day_english = day_found
                current_items = []
                
                # Check if there's menu content on the same line after the day name
                remaining = line
                for german_day in german_days:
                    remaining = re.sub(german_day, '', remaining, flags=re.IGNORECASE)
                remaining = remaining.strip()
                
                if remaining and len(remaining) > 3:
                    item = self._parse_menu_item(remaining)
                    if item:
                        current_items.append(item)
            
            elif current_day_english:
                # This is a menu item line
                item = self._parse_menu_item(line)
                if item:
                    current_items.append(item)
        
        # Don't forget the last day
        if current_day_english and current_items:
            self._assign_prices(current_items)
            weekly_menu[current_day_english] = DailyMenu(
                day=current_day_english,
                items=current_items,
                provider_name=self.name
            )
        
        return weekly_menu
    
    def _assign_prices(self, items: list[MenuItem]) -> None:
        """Assign prices to menu items based on their order.
        
        First dish (Tagesteller): €11.20
        Second dish (Tagesteller vegetarisch): €10.30
        """
        for i, item in enumerate(items):
            if item.price is None:
                if i == 0:
                    item.price = "€11.20"  # Tagesteller
                elif i == 1:
                    item.price = "€10.30"  # Tagesteller vegetarisch
                else:
                    item.price = "€11.20"  # Default for any additional items
    
    def _is_allergen_line(self, line: str) -> bool:
        """Check if a line contains allergen information."""
        # Common allergen codes and their descriptions
        allergen_patterns = [
            # Single letter codes followed by allergen names
            r'\b[A-R]\s+(Gluten|Krebstiere|Eier|Fisch|Erdnüsse|Sojabohnen|Milch|Schalenfrüchte|Sellerie|Senf|Sesam|Sulfite|Lupinen|Weichtiere)',
            # Multiple allergen codes in sequence (e.g., "A G M O")
            r'^[A-R](\s+[A-R]){2,}',
            # Lines that are mostly single letters with spaces
            r'^([A-R]\s+\w+\s+){2,}',
        ]
        
        for pattern in allergen_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        # Check for high concentration of single capital letters (allergen codes)
        # Pattern: letter followed by space and a word, repeated
        allergen_code_pattern = r'[A-R]\s+\w+'
        matches = re.findall(allergen_code_pattern, line)
        if len(matches) >= 3:
            # If we have 3+ potential allergen codes, likely an allergen line
            return True
        
        return False
    
    def _parse_menu_item(self, line: str) -> Optional[MenuItem]:
        """Parse a single line into a MenuItem."""
        # Skip allergen information lines
        if self._is_allergen_line(line):
            return None
        
        # Skip empty lines and common non-food items
        skip_patterns = [
            'wochenmenu', 'weekly', 'menu', 'nice guys', 'www.', 
            'http', 'tel:', 'fax:', 'email', '@', 'reservierung',
            'öffnungszeiten', 'opening', 'closed', 'geschlossen',
            'allergene', 'allergen', 'enthält', 'contains'
        ]
        
        line_lower = line.lower()
        if any(pattern in line_lower for pattern in skip_patterns):
            return None
        
        if len(line) < 4:
            return None
        
        # Try to extract price (common formats: €X.XX, X,XX€, X.XX €)
        price = None
        price_patterns = [
            r'€\s*(\d+[.,]\d{2})',
            r'(\d+[.,]\d{2})\s*€',
            r'EUR\s*(\d+[.,]\d{2})',
        ]
        
        dish_name = line
        for pattern in price_patterns:
            match = re.search(pattern, line)
            if match:
                price = f"€{match.group(1).replace(',', '.')}"
                dish_name = re.sub(pattern, '', line).strip()
                break
        
        # Clean up the dish name
        dish_name = dish_name.strip(' -–|/')
        
        if len(dish_name) < 3:
            return None
        
        return MenuItem(
            name_german=dish_name,
            name_english="",  # Will be translated later
            price=price
        )
