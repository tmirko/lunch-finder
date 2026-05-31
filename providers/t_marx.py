"""
T-Marx by Eurest menu provider.
Fetches and parses the weekly menu from https://menu.mitarbeiterrestaurant.at/menu/t-marx-by-eurest.pdf
Uses cell-based OCR extraction for automatic weekly updates.
"""
import requests
import re
from typing import Optional
from providers.base import MenuProvider, MenuItem, DailyMenu

try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class TMarxProvider(MenuProvider):
    """Provider for T-Marx by Eurest restaurant in Vienna."""
    
    MENU_URL = "https://menu.mitarbeiterrestaurant.at/menu/t-marx-by-eurest.pdf"
    
    COLUMNS = {
        'Monday': (650, 1060),
        'Tuesday': (1060, 1625),
        'Wednesday': (1625, 2175),
        'Thursday': (2175, 2770),
        'Friday': (2770, 3508),
    }
    
    ROWS = {
        'Suppe': (570, 780),
        'Daily': (780, 1010),
        'Veggie': (1010, 1250),
        'Bowl': (1250, 1490),
        'Pasta': (1490, 1760),
    }
    
    PRICES = {
        'Suppe': '€2,60',
        'Daily': '€8,30 - €9,60',
        'Veggie': '€7,80 - €8,75',
        'Bowl': '€8,10 - €9,15',
        'Pasta': '€8,50 - €11,75',
    }
    
    DESCRIPTIONS = {
        'Suppe': 'Suppe',
        'Daily': 'Tagesteller',
        'Veggie': 'Vegetarisch',
        'Bowl': 'Bowl',
        'Pasta': 'Pasta & Co',
    }
    
    def __init__(self):
        self._weekly_menu: Optional[dict[str, DailyMenu]] = None
    
    @property
    def name(self) -> str:
        return "T-Marx by Eurest"
    
    @property
    def url(self) -> str:
        return "https://menu.mitarbeiterrestaurant.at/menu/t-marx-by-eurest.pdf"
    
    def get_menu(self, day: str) -> DailyMenu:
        if self._weekly_menu is None:
            self._weekly_menu = self.fetch_weekly_menu()
        
        return self._weekly_menu.get(day, DailyMenu(day=day, items=[], provider_name=self.name))
    
    def fetch_weekly_menu(self) -> dict[str, DailyMenu]:
        if not OCR_AVAILABLE:
            print("OCR not available - pdf2image and pytesseract required")
            return self._empty_weekly_menu()
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(self.MENU_URL, timeout=15, headers=headers)
            response.raise_for_status()
            
            images = convert_from_bytes(response.content, dpi=300)
            
            if not images:
                print("No pages found in T-Marx PDF")
                return self._empty_weekly_menu()
            
            return self._extract_menu_from_image(images[0])
            
        except requests.RequestException as e:
            print(f"Error fetching T-Marx menu: {e}")
            return self._empty_weekly_menu()
        except Exception as e:
            print(f"Error parsing T-Marx menu: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_weekly_menu()
    
    def _extract_menu_from_image(self, img) -> dict[str, DailyMenu]:
        weekly_menu = {}
        
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            x1, x2 = self.COLUMNS[day]
            items = []
            is_holiday = False
            
            for category in ['Suppe', 'Daily', 'Veggie', 'Bowl', 'Pasta']:
                y1, y2 = self.ROWS[category]
                cell_img = img.crop((x1, y1, x2, y2))
                cell_text = pytesseract.image_to_string(cell_img, lang='deu', config='--psm 6')
                
                if self._is_holiday(cell_text):
                    is_holiday = True
                    break
                
                if category == 'Bowl':
                    if cell_text.strip():
                        items.append(MenuItem(
                            name_german="Create your own Bowl",
                            name_english="",
                            price=self.PRICES['Bowl'],
                            description=self.DESCRIPTIONS['Bowl']
                        ))
                    continue
                
                dish_name = self._clean_cell_text(cell_text)
                
                if not dish_name:
                    continue
                
                items.append(MenuItem(
                    name_german=dish_name,
                    name_english="",
                    price=self.PRICES[category],
                    description=self.DESCRIPTIONS[category]
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
    
    def _is_holiday(self, text: str) -> bool:
        upper = text.upper()
        return 'FEIERTAG' in upper or 'GESCHLOSSEN' in upper
    
    def _clean_cell_text(self, text: str) -> str:
        if not text:
            return ""
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        cleaned_lines = []
        
        for line in lines:
            if re.match(r'^[€\d\s,.\|]+$', line):
                continue
            if re.search(r'\d+\s*kcal', line, re.IGNORECASE):
                continue
            if re.match(r'^[A-Z](,[A-Z])+\s*€', line):
                continue
            if re.match(r'^[A-Z](,[A-Z])+$', line):
                continue
            if 'create your own bowl' in line.lower():
                continue
            if 'topping' in line.lower() and ('wahl' in line.lower() or 'inklusive' in line.lower() or '+1' in line):
                continue
            if 'xl topping' in line.lower():
                continue
            if 'frischer nishikirei' in line.lower():
                continue
            
            cleaned = re.sub(r'€\s*\d+[,\.]\d{2}', '', line)
            cleaned = re.sub(r'\d+[,\.]\d{2}', '', cleaned)
            cleaned = re.sub(r'\d+\s*kcal', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\b[A-Z](,[A-Z])+\b', '', cleaned)
            cleaned = re.sub(r'[|/][A-Z](,[A-Z])*', '', cleaned)
            cleaned = re.sub(r'\(?\d+stk\.?\s*', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'[®©™\[\]{}]', '', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            cleaned = cleaned.strip(' .,;:-|/>@#*~`')
            
            if len(cleaned) >= 3:
                alpha_count = sum(c.isalpha() or c.isspace() for c in cleaned)
                if alpha_count >= len(cleaned) * 0.5:
                    cleaned_lines.append(cleaned)
        
        if not cleaned_lines:
            return ""
        
        result = ' '.join(cleaned_lines)
        result = re.sub(r'\s+', ' ', result).strip()
        result = re.sub(r'^[\d\s>]+', '', result).strip()
        result = re.sub(r'^[a-z]{1,2}\s+', '', result).strip()
        result = re.sub(r'[()]\s*', '', result)
        result = re.sub(r'>\s*', '', result)
        result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)
        result = re.sub(r'\s+', ' ', result).strip()
        return result
    
    def _empty_weekly_menu(self) -> dict[str, DailyMenu]:
        return {
            day: DailyMenu(day=day, items=[], provider_name=self.name)
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
