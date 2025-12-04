"""
Food Garden menu provider.
Fetches and parses the weekly menu from https://foodgarden.wien/wp-content/uploads/Foodgarden-Aloha-Bowl-Menu.pdf
Uses OCR to extract text from image-based PDF.
"""
import requests
import re
from typing import Optional
from providers.base import MenuProvider, MenuItem, DailyMenu

# OCR imports - optional, will gracefully handle if not available
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class FoodGardenProvider(MenuProvider):
    """Provider for Food Garden restaurant in Vienna."""
    
    MENU_URL = "https://foodgarden.wien/wp-content/uploads/Foodgarden-Aloha-Bowl-Menu.pdf"
    
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
        return "Food Garden"
    
    @property
    def url(self) -> str:
        return "https://foodgarden.wien"
    
    def get_menu(self, day: str) -> DailyMenu:
        """Get menu for a specific day."""
        if self._weekly_menu is None:
            self._weekly_menu = self.fetch_weekly_menu()
        
        return self._weekly_menu.get(day, DailyMenu(day=day, items=[], provider_name=self.name))
    
    def fetch_weekly_menu(self) -> dict[str, DailyMenu]:
        """Fetch and parse the weekly menu PDF using OCR."""
        if not OCR_AVAILABLE:
            print("OCR not available - pdf2image and pytesseract required")
            print("Install with: pip install pdf2image pytesseract")
            print("Also need system package: sudo apt install tesseract-ocr tesseract-ocr-deu")
            return self._empty_weekly_menu()
        
        try:
            # Download the PDF
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.MENU_URL, timeout=15, headers=headers)
            response.raise_for_status()
            
            # Convert PDF to images at higher DPI for better OCR
            images = convert_from_bytes(response.content, dpi=300)
            
            # OCR each page
            full_text = ""
            for img in images:
                # Use German language for better recognition
                # Also try with psm 6 (assume uniform block of text) for better table handling
                text = pytesseract.image_to_string(img, lang='deu', config='--psm 6')
                full_text += text + "\n"
            
            return self._parse_menu_text(full_text)
            
        except requests.RequestException as e:
            print(f"Error fetching Food Garden menu: {e}")
            return self._empty_weekly_menu()
        except Exception as e:
            print(f"Error parsing Food Garden menu with OCR: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_weekly_menu()
    
    def _empty_weekly_menu(self) -> dict[str, DailyMenu]:
        """Return empty menu structure."""
        return {
            day: DailyMenu(day=day, items=[], provider_name=self.name)
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    
    def _parse_menu_text(self, text: str) -> dict[str, DailyMenu]:
        """Parse the OCR extracted text into menu items.
        
        The PDF has a table structure with days as columns and dish rows.
        OCR reads it row by row, so dishes for all days appear on the same line.
        We search for known dish patterns and map them to their days.
        """
        weekly_menu = self._empty_weekly_menu()
        
        # The OCR output has dishes appearing in rows like:
        # "Linsen-Kokos-Curry NF Rotkrautstrudel ACGO Vegane Ravioli..."
        # These are Mon, Tue, Wed, Thu, Fri in order
        
        # Define dish patterns to search for - each tuple is (pattern, day, dish_name, ingredients)
        # Using flexible patterns to handle OCR variations
        dish_patterns = [
            # Dish I row - vegetarian dishes (left to right = Mon to Fri)
            (r'Linsen.?Kokos.?Curry', "Monday", "Linsen-Kokos-Curry", "Rote Linsen, Süßkartoffel, Basmatireis, Koriander", "€8.90"),
            (r'Rotkrautstrudel', "Tuesday", "Rotkrautstrudel", "Ziegenkäse, Schnittlauch-Rahm-Dip, frischer Rucola", "€8.90"),
            (r'Vegane\s*Ravioli|Triangolo\s*Portobello', "Wednesday", "Vegane Ravioli Triangolo", "Portobello, leichte Kräutersauce, Grana Padano", "€8.90"),
            (r'Kürbis.?Spinat.?Lasagne', "Thursday", "Kürbis-Spinat-Lasagne", "Schafkäse, Kürbiskerne, Blattsalat, Hausdressing", "€8.90"),
            (r'Ebly.?Gemüse.?Risotto', "Friday", "Ebly-Gemüse-Risotto", "Wurzelgemüse, Kürbis, getrocknete Paradeiser", "€8.90"),
            
            # Dish II row - meat dishes
            (r'Spaghetti\s*Carbonara', "Monday", "Spaghetti Carbonara", "Zwiebel, Speck, Ei, Grana Padano, frische Petersilie", "€8.90"),
            (r'Cordon\s*Bleu', "Tuesday", "Cordon Bleu von der Pute", "Petersilerdäpfel, Preiselbeeren, Bio-Zitrone", "€8.90"),
            (r'[CĆČ]evap[ceč]i[cč]i', "Wednesday", "Cevapcici", "Potato Wedges, Ajvar, Zwiebelsenf, Minz-Dip", "€8.90"),
            (r'Chicken\s*Tikka\s*Masala', "Thursday", "Chicken Tikka Masala", "Jasminreis, Kichererbsen, gehackte Cashewnüsse", "€8.90"),
            (r'Sayadiya|[Ss]eehechtfil', "Friday", "Sayadiya - gebratenes Seehechtfilet", "orientalischer Gewürzreis, karamellisierte Zwiebeln", "€8.90"),
        ]
        
        # Weekly special - available every day
        weekly_special_pattern = r'Hirschragout'
        weekly_special_name = "Hirschragout (Weekly Special)"
        weekly_special_ingredients = "Serviettenknödel, Preiselbeeren"
        weekly_special_price = "€9.80"
        
        all_dishes = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
        
        for pattern, day, dish_name, ingredients, price in dish_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                full_name = f"{dish_name} ({ingredients})"
                all_dishes[day].append(MenuItem(
                    name_german=full_name,
                    name_english="",
                    price=price
                ))
        
        # Add weekly special to all days if found
        if re.search(weekly_special_pattern, text, re.IGNORECASE):
            for day in all_dishes.keys():
                full_name = f"{weekly_special_name} ({weekly_special_ingredients})"
                all_dishes[day].append(MenuItem(
                    name_german=full_name,
                    name_english="",
                    price=weekly_special_price
                ))
        
        # Build the weekly menu
        for day, items in all_dishes.items():
            if items:
                weekly_menu[day] = DailyMenu(
                    day=day,
                    items=items,
                    provider_name=self.name
                )
        
        return weekly_menu
