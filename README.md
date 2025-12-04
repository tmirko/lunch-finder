# 🍽️ Lunch Finder Vienna

A Streamlit web application to discover lunch menu options around your office in Vienna, Austria.

## Features

- 📅 **Day Selection**: Choose any weekday (Monday-Friday) with the current day pre-selected
- 🇦🇹🇬🇧 **Bilingual Menus**: Dish names displayed in both German (original) and English (translated)
- 🖼️ **Dish Images**: Visual representation of dishes fetched automatically
- 📱 **Mobile-Friendly**: Designed to be accessed from your phone
- 🔌 **Extensible**: Easy to add new restaurant providers

## Current Providers

- **The Nice Guys** - [theniceguys.at](https://www.theniceguys.at)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/lunch-finder.git
cd lunch-finder
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
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
├── providers/
│   ├── __init__.py
│   ├── base.py           # Base provider class
│   └── nice_guys.py      # The Nice Guys provider
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
5. Add the provider instance to the `providers` list in `app.py`

## Technologies Used

- **Streamlit** - Web framework
- **PyPDF2** - PDF parsing for menu extraction
- **deep-translator** - German to English translation
- **requests** - HTTP requests
- **BeautifulSoup4** - Web scraping for images

## License

MIT License

## Contributing

Contributions are welcome! Feel free to add new restaurant providers or improve existing features.
