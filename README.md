# 🍽️ Lunch Finder Vienna

A Streamlit web application to discover lunch menu options around your office in Vienna, Austria.

## Features

- 📅 **Day Selection**: Choose any weekday (Monday-Friday) with the current day pre-selected
- 🇦🇹🇬🇧 **Bilingual Menus**: Dish names displayed in both German (original) and English (translated)
- 🖼️ **Dish Images**: Visual representation of dishes fetched automatically
- 📱 **Mobile-Friendly**: Designed to be accessed from your phone
- 🔌 **Extensible**: Easy to add new restaurant providers
- 🔄 **Auto-updating**: Menu providers automatically fetch the latest weekly menus

## Current Providers

- **The Nice Guys** - [theniceguys.at](https://www.theniceguys.at)
- **Food Garden** - [foodgarden.wien](https://foodgarden.wien)
- **T-Marx by Eurest** - [menu.mitarbeiterrestaurant.at](https://menu.mitarbeiterrestaurant.at/menu/t-marx-by-eurest.pdf)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/tmirko/lunch-finder.git
cd lunch-finder
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install system dependencies (required for OCR-based menu providers):
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-deu poppler-utils

# macOS
brew install tesseract tesseract-lang poppler
```

4. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the App

Start the Streamlit server:

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Access from your phone

To access from your phone on the same network:

```bash
streamlit run app.py --server.address 0.0.0.0
```

Then open `http://YOUR_COMPUTER_IP:8501` on your phone.

## Project Structure

```
lunch-finder/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── packages.txt           # System dependencies (for Streamlit Cloud)
├── providers/
│   ├── __init__.py
│   ├── base.py           # Base provider class
│   ├── nice_guys.py      # The Nice Guys provider
│   ├── food_garden.py    # Food Garden provider (OCR-based)
│   └── t_marx.py         # T-Marx by Eurest provider (OCR-based)
└── utils/
    ├── __init__.py
    ├── translator.py     # German to English translation
    └── image_search.py   # Dish image search
```

## Adding a New Provider

1. Create a new file in `providers/` (e.g., `my_restaurant.py`)
2. Inherit from `MenuProvider` base class
3. Implement the required methods:
   - `name` property
   - `url` property
   - `get_menu(day)` method
   - `fetch_weekly_menu()` method
4. Add the provider to `providers/__init__.py`
5. Add the provider instance to the `providers` dict in `app.py`

### OCR-based Providers

For restaurants that publish menus as image-based PDFs, use the OCR approach:
- Use `pdf2image` to convert PDF pages to images
- Use `pytesseract` for text extraction
- Dynamic column detection for table-based menus (see `food_garden.py` or `t_marx.py` for examples)

## Technologies Used

- **Streamlit** - Web framework
- **PyPDF2** - PDF parsing for text-based menus
- **pdf2image** + **pytesseract** - OCR for image-based PDF menus
- **deep-translator** - German to English translation
- **requests** - HTTP requests
- **BeautifulSoup4** - Web scraping for images
- **Pillow** - Image processing
