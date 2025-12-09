"""
T-Marx by Eurest menu provider.
Fetches and parses the weekly menu from https://menu.mitarbeiterrestaurant.at/menu/t-marx-by-eurest.pdf
Uses column-based OCR extraction with pattern matching for automatic weekly updates.
"""
import requests
import re
from typing import Optional
from providers.base import MenuProvider, MenuItem, DailyMenu

# OCR imports
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class TMarxProvider(MenuProvider):
    """Provider for T-Marx by Eurest restaurant in Vienna."""
    
    MENU_URL = "https://menu.mitarbeiterrestaurant.at/menu/t-marx-by-eurest.pdf"
    
    # Column boundaries (x coordinates at 300 DPI)
    # Based on header positions: MONTAG=717, DIENSTAG=1269, MITTWOCH=1818, DONNERSTAG=2352, FREITAG=2961
    COLUMNS = {
        'Monday': (650, 1060),
        'Tuesday': (1060, 1625),
        'Wednesday': (1625, 2175),
        'Thursday': (2175, 2770),
        'Friday': (2770, 3508),
    }
    
    # Content area (y coordinates at 300 DPI)
    CONTENT_Y = (500, 1900)
    
    # Category prices
    PRICES = {
        'Suppe': '€2,50',
        'Tagesteller': '€8,00 - €9,10',
        'Vegetarisch': '€7,50 - €8,30',
        'Bowl': '€7,80 - €8,70',
        'Pasta & Co': '€8,20 - €9,60',
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
        """Get menu for a specific day."""
        if self._weekly_menu is None:
            self._weekly_menu = self.fetch_weekly_menu()
        
        return self._weekly_menu.get(day, DailyMenu(day=day, items=[], provider_name=self.name))
    
    def fetch_weekly_menu(self) -> dict[str, DailyMenu]:
        """Fetch and parse the weekly menu using column-based OCR."""
        if not OCR_AVAILABLE:
            print("OCR not available - pdf2image and pytesseract required")
            return self._empty_weekly_menu()
        
        try:
            # Download the PDF
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(self.MENU_URL, timeout=15, headers=headers)
            response.raise_for_status()
            
            # Convert PDF to images at 300 DPI
            images = convert_from_bytes(response.content, dpi=300)
            
            # Find and process the German page
            for img in images:
                # Quick check if this is German page
                sample_text = pytesseract.image_to_string(img.crop((0, 0, 500, 300)), lang='deu')
                if 'Monday' in sample_text or 'Week' in sample_text or 'WEEK' in sample_text:
                    continue
                
                # Process this German page
                return self._extract_menu_from_image(img)
            
            print("Could not find German menu page")
            return self._empty_weekly_menu()
            
        except requests.RequestException as e:
            print(f"Error fetching T-Marx menu: {e}")
            return self._empty_weekly_menu()
        except Exception as e:
            print(f"Error parsing T-Marx menu: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_weekly_menu()
    
    def _extract_menu_from_image(self, img) -> dict[str, DailyMenu]:
        """Extract menu by OCR'ing each day column and pattern matching."""
        weekly_menu = {}
        
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            x1, x2 = self.COLUMNS[day]
            y1, y2 = self.CONTENT_Y
            
            # Crop and OCR the full column
            col_img = img.crop((x1, y1, x2, y2))
            col_text = pytesseract.image_to_string(col_img, lang='deu', config='--psm 4')
            
            # Parse the column text
            parsed = self._parse_column_text(col_text)
            
            if parsed.get('closed'):
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
                items = []
                
                # Add soup
                if parsed.get('Suppe'):
                    items.append(MenuItem(
                        name_german=parsed['Suppe'],
                        name_english="",
                        price=self.PRICES['Suppe'],
                        description="Suppe"
                    ))
                
                # Add daily dish
                if parsed.get('Daily'):
                    items.append(MenuItem(
                        name_german=parsed['Daily'],
                        name_english="",
                        price=self.PRICES['Tagesteller'],
                        description="Tagesteller"
                    ))
                
                # Add veggie dish
                if parsed.get('Veggie'):
                    items.append(MenuItem(
                        name_german=parsed['Veggie'],
                        name_english="",
                        price=self.PRICES['Vegetarisch'],
                        description="Vegetarisch"
                    ))
                
                # Always add bowl option
                items.append(MenuItem(
                    name_german="Create your own Bowl",
                    name_english="",
                    price=self.PRICES['Bowl'],
                    description="Bowl"
                ))
                
                # Add pasta dish
                if parsed.get('Pasta'):
                    items.append(MenuItem(
                        name_german=parsed['Pasta'],
                        name_english="",
                        price=self.PRICES['Pasta & Co'],
                        description="Pasta & Co"
                    ))
                
                weekly_menu[day] = DailyMenu(
                    day=day,
                    items=items,
                    provider_name=self.name
                )
        
        return weekly_menu
    
    def _parse_column_text(self, text: str) -> dict:
        """Parse a column's OCR text to extract menu items by pattern matching."""
        if not text:
            return {}
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        full_text = ' '.join(lines)
        
        # Check for closure
        if 'FEIERTAG' in full_text.upper() or 'GESCHLOSSEN' in full_text.upper():
            return {'closed': True}
        
        # Clean the text for pattern matching
        clean_text = self._clean_text(full_text)
        
        result = {}
        
        # Extract soup (usually ends with "suppe" or is "Chef's choice")
        soup_patterns = [
            r'(Klare,?\s*kräftige\s*Rindssuppe)',
            r'(Bohnensuppe)',
            r'(Paradeisercremesuppe)',
            r'(Grießnockerlsuppe)',
            r'(Frittatensuppe)',
            r'(Gemüsesuppe)',
            r'([\w]+suppe)',
            r'(Chefs?\s*choice)',
        ]
        for pattern in soup_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                result['Suppe'] = match.group(1).strip()
                break
        
        # Extract daily dish (main meat dish)
        daily_patterns = [
            (r'Gratinierte?\s*Schinkenfleckerl(?:\s*\(Schwein\))?', 'Gratinierte Schinkenfleckerl (Schwein) mit Blattsalat'),
            (r'Gebackene[sr]?\s*Hühnerschnitzel', 'Gebackenes Hühnerschnitzel mit Beilage nach Wahl'),
            (r'Schweinsschopfbraten\s*(?:im\s*)?(?:Natursaft)?', 'Schweinsschopfbraten im Natursaft mit Erdäpfelknödel'),
            (r'Calamari\s*gebacken', 'Calamari gebacken mit Caesar Salat und Sauce Tartar'),
            (r'Wiener\s*Schnitzel', 'Wiener Schnitzel mit Beilage nach Wahl'),
            (r'Tafelspitz', 'Tafelspitz mit klassischen Beilagen'),
            (r'Backhendl', 'Backhendl mit Erdäpfelsalat'),
        ]
        for pattern, full_name in daily_patterns:
            if re.search(pattern, clean_text, re.IGNORECASE):
                result['Daily'] = full_name
                break
        
        # If no specific match, try to find generic daily
        if 'Daily' not in result:
            # Look for any dish followed by "Blattsalat" or "Beilage"
            match = re.search(r'(\w+(?:\s+\w+)?)\s+(?:mit\s+)?(?:Blattsalat|Beilage)', clean_text, re.IGNORECASE)
            if match:
                result['Daily'] = match.group(0).strip()
        
        # Extract veggie dish
        veggie_patterns = [
            (r'Cremespinat\s*(?:mit\s*)?(?:Spiegelei)?', 'Cremespinat mit Spiegelei und Röstkartoffel'),
            (r'Käsespätzle', 'Käsespätzle mit Röstzwiebeln und Blattsalat'),
            (r'(?:Süß-?Saures?\s*)?Wokgemüse.*?Tofu', 'Süß-Saures Wokgemüse mit Jasminreis und gegrilltem Tofu'),
            (r'Spinatknödel', 'Spinatknödel mit Salbeibutter'),
            (r'Gemüsecurry', 'Gemüsecurry mit Reis'),
            (r'Erdäpfelgulasch', 'Erdäpfelgulasch'),
        ]
        for pattern, full_name in veggie_patterns:
            if re.search(pattern, clean_text, re.IGNORECASE):
                result['Veggie'] = full_name
                break
        
        # If Friday and no veggie found, might be "Chef's choice"
        if 'Veggie' not in result and 'chefs choice' in clean_text.lower():
            result['Veggie'] = "Chef's choice"
        
        # Extract pasta/special dish
        pasta_patterns = [
            (r'Pizza\s*Della\s*Casa', 'Pizza Della Casa'),
            (r'Rosa\s*Kalbstafelspitz', 'Rosa Kalbstafelspitz mit Serviettenknödel und Waldpilzragout'),
            (r'Frische\s*Pasta.*?(?:Rinderbolognese|Pesto)', 'Frische Pasta mit Rinderbolognese oder Pesto'),
            (r'Rinderbolognese', 'Pasta mit Rinderbolognese'),
            (r'Lasagne', 'Lasagne'),
        ]
        for pattern, full_name in pasta_patterns:
            if re.search(pattern, clean_text, re.IGNORECASE):
                result['Pasta'] = full_name
                break
        
        return result
    
    def _clean_text(self, text: str) -> str:
        """Clean OCR text for pattern matching."""
        # Remove allergen codes
        text = re.sub(r'\b[A-Z](,[A-Z])+\b', '', text)
        text = re.sub(r'[|/][A-Z](,[A-Z])*', '', text)
        # Remove prices
        text = re.sub(r'€\s*\d+[,\.]\d{2}', '', text)
        text = re.sub(r'\d+[,\.]\d{2}', '', text)
        # Remove kcal
        text = re.sub(r'\d+\s*kcal', '', text, flags=re.IGNORECASE)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _empty_weekly_menu(self) -> dict[str, DailyMenu]:
        """Return empty menu structure."""
        return {
            day: DailyMenu(day=day, items=[], provider_name=self.name)
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
