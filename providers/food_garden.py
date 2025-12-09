"""
Food Garden menu provider.
Fetches and parses the weekly menu from https://foodgarden.wien/wp-content/uploads/Foodgarden-Aloha-Bowl-Menu.pdf
Uses column-based OCR extraction with dynamic day header detection for automatic weekly updates.
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
    
    # Row boundaries (y coordinates at 300 DPI) - these are relatively stable
    ROWS = {
        'Dish_I': (820, 1180),      # Vegetarian dish row
        'Dish_II': (1180, 1520),    # Meat dish row
    }
    
    # Weekly special region (x1, y1, x2, y2)
    WEEKLY_REGION = (700, 1520, 2200, 1750)
    
    # Prices
    DISH_PRICE = "€8.90"
    WEEKLY_PRICE = "€9.80"
    
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
        """Fetch and parse the weekly menu PDF using column-based OCR."""
        if not OCR_AVAILABLE:
            print("OCR not available - pdf2image and pytesseract required")
            return self._empty_weekly_menu()
        
        try:
            # Download the PDF
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.MENU_URL, timeout=15, headers=headers)
            response.raise_for_status()
            
            # Convert PDF to image at 300 DPI
            images = convert_from_bytes(response.content, dpi=300)
            
            if not images:
                print("No pages found in PDF")
                return self._empty_weekly_menu()
            
            # Process the first (and usually only) page
            return self._extract_menu_from_image(images[0])
            
        except requests.RequestException as e:
            print(f"Error fetching Food Garden menu: {e}")
            return self._empty_weekly_menu()
        except Exception as e:
            print(f"Error parsing Food Garden menu: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_weekly_menu()
    
    def _extract_menu_from_image(self, img) -> dict[str, DailyMenu]:
        """Extract menu by dynamically finding day columns and OCR'ing each cell."""
        weekly_menu = {}
        
        # Find day column boundaries dynamically
        columns = self._find_day_columns(img)
        
        if not columns:
            print("Could not find day columns in the menu")
            return self._empty_weekly_menu()
        
        # Extract weekly special (same for all days)
        weekly_special = self._extract_weekly_special(img)
        
        # Extract dishes for each day
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            if day not in columns:
                weekly_menu[day] = DailyMenu(day=day, items=[], provider_name=self.name)
                continue
            
            x1, x2 = columns[day]
            items = []
            is_holiday = False
            
            # Extract vegetarian dish (Dish I)
            veggie_dish = self._extract_cell(img, x1, x2, self.ROWS['Dish_I'])
            if veggie_dish:
                if 'HOLIDAY' in veggie_dish:
                    is_holiday = True
                else:
                    items.append(MenuItem(
                        name_german=veggie_dish,
                        name_english="",
                        price=self.DISH_PRICE,
                        description="Dish I (Vegetarian)"
                    ))
            
            # Extract meat dish (Dish II)
            if not is_holiday:
                meat_dish = self._extract_cell(img, x1, x2, self.ROWS['Dish_II'])
                if meat_dish:
                    items.append(MenuItem(
                        name_german=meat_dish,
                        name_english="",
                        price=self.DISH_PRICE,
                        description="Dish II (Meat/Fish)"
                    ))
            
            # Add weekly special (same for all days)
            if not is_holiday and weekly_special:
                items.append(MenuItem(
                    name_german=weekly_special,
                    name_english="",
                    price=self.WEEKLY_PRICE,
                    description="Weekly Special"
                ))
            
            if is_holiday:
                weekly_menu[day] = DailyMenu(
                    day=day,
                    items=[MenuItem(
                        name_german="Feiertag - Geschlossen",
                        name_english="Holiday - Closed",
                        price=None,
                        description=""
                    )],
                    provider_name=self.name
                )
            else:
                weekly_menu[day] = DailyMenu(
                    day=day,
                    items=items,
                    provider_name=self.name
                )
        
        return weekly_menu
    
    def _find_day_columns(self, img) -> dict[str, tuple[int, int]]:
        """Dynamically find day column boundaries from header positions."""
        data = pytesseract.image_to_data(img, lang='deu', output_type=pytesseract.Output.DICT)
        
        day_headers = {}
        days_map = {
            'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
            'thursday': 'Thursday', 'friday': 'Friday',
            'montag': 'Monday', 'dienstag': 'Tuesday', 'mittwoch': 'Wednesday',
            'donnerstag': 'Thursday', 'freitag': 'Friday'
        }
        
        for i, word in enumerate(data['text']):
            w_lower = word.lower().strip()
            if w_lower in days_map:
                x = data['left'][i]
                width = data['width'][i]
                y = data['top'][i]
                # Only consider headers in the top portion (y < 800)
                if y < 800:
                    day_headers[days_map[w_lower]] = x + width // 2
        
        if len(day_headers) < 3:
            return {}
        
        # Sort by x position and calculate boundaries
        sorted_days = sorted(day_headers.items(), key=lambda x: x[1])
        img_width = img.size[0]
        
        columns = {}
        for i, (day, center_x) in enumerate(sorted_days):
            if i == 0:
                left = 700  # Start after row labels
            else:
                prev_center = sorted_days[i-1][1]
                left = (prev_center + center_x) // 2
            
            if i == len(sorted_days) - 1:
                right = img_width - 200
            else:
                next_center = sorted_days[i+1][1]
                right = (center_x + next_center) // 2
            
            columns[day] = (left, right)
        
        return columns
    
    def _extract_cell(self, img, x1: int, x2: int, y_range: tuple[int, int]) -> Optional[str]:
        """Extract and clean text from a specific cell."""
        y1, y2 = y_range
        cell_img = img.crop((x1, y1, x2, y2))
        cell_text = pytesseract.image_to_string(cell_img, lang='deu', config='--psm 6')
        
        # Check for holiday
        if 'holiday' in cell_text.lower() or 'feiertag' in cell_text.lower():
            return "HOLIDAY"
        
        return self._clean_dish_text(cell_text)
    
    def _extract_weekly_special(self, img) -> Optional[str]:
        """Extract the weekly special dish."""
        # Weekly special is typically in the center-left area of the menu
        region = (1200, 1520, 2800, 1750)
        weekly_img = img.crop(region)
        weekly_text = pytesseract.image_to_string(weekly_img, lang='deu', config='--psm 4')
        
        lines = [l.strip() for l in weekly_text.split('\n') if l.strip()]
        if not lines:
            return None
        
        # First non-empty line is usually the main dish name
        main_dish = None
        ingredients = []
        
        for line in lines:
            # Skip kcal lines
            if 'kcal' in line.lower():
                continue
            
            # Clean the line
            cleaned = re.sub(r'\b[A-Z]{1,3}\b(?=\s|$|[|])', '', line)  # Remove allergen codes
            cleaned = re.sub(r'[|]', ',', cleaned)  # Replace | with comma
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            if not cleaned:
                continue
            
            if main_dish is None:
                main_dish = cleaned
            else:
                # This is the ingredients line
                ingredients.append(cleaned)
        
        if main_dish:
            if ingredients:
                ingredient_text = ', '.join(ingredients)
                # Clean up the ingredients - normalize spacing around commas
                ingredient_text = re.sub(r'\s*,\s*', ', ', ingredient_text)
                ingredient_text = re.sub(r',\s*,', ',', ingredient_text)
                ingredient_text = re.sub(r'^\s*,|,\s*$', '', ingredient_text).strip()
                return f"{main_dish} ({ingredient_text})"
            return main_dish
        
        return None
    
    def _clean_dish_text(self, text: str) -> str:
        """Clean OCR text to extract dish description."""
        if not text:
            return ""
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        cleaned_parts = []
        
        for line in lines:
            # Remove allergen codes (single/double uppercase letters)
            line = re.sub(r'\b[A-Z]{1,3}\b(?=\s|$|[^a-zA-Z])', '', line)
            # Remove kcal
            line = re.sub(r'\d+\s*kcal', '', line, flags=re.IGNORECASE)
            # Remove prices
            line = re.sub(r'€?\d+[.,]\d{2}', '', line)
            # Remove special characters
            line = re.sub(r'[|/\\®©™\[\]{}()]', ' ', line)
            # Clean whitespace
            line = re.sub(r'\s+', ' ', line).strip()
            
            if line and len(line) >= 3:
                alpha_count = sum(c.isalpha() for c in line)
                if alpha_count >= len(line) * 0.4:
                    cleaned_parts.append(line)
        
        result = ' '.join(cleaned_parts)
        # Remove trailing fragments (single letters)
        result = re.sub(r'\s+[a-z]{1,2}$', '', result)
        # Remove leading numbers/fragments
        result = re.sub(r'^[\d\s]+', '', result)
        # Fix common OCR errors
        result = re.sub(r'mitEi\b', 'mit Ei', result)
        result = re.sub(r'Paprikahendernl', 'Paprikahendl', result)
        
        return result.strip()
    
    def _empty_weekly_menu(self) -> dict[str, DailyMenu]:
        """Return empty menu structure."""
        return {
            day: DailyMenu(day=day, items=[], provider_name=self.name)
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
