# AGENTS.md

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
sudo apt install tesseract-ocr tesseract-ocr-deu poppler-utils  # macOS: brew install tesseract tesseract-lang poppler
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Testing

No test framework is configured. `test_fg.py` is a standalone debug script, not a test suite.

## Adding a provider

1. Create `providers/<name>.py`, inherit from `MenuProvider` (`providers/base.py`)
2. Implement: `name`, `url`, `get_menu(day)`, `fetch_weekly_menu()`
3. Export in `providers/__init__.py`
4. Register in `app.py` `get_providers()` dict

Two provider patterns exist:
- **Text PDF** (`nice_guys.py`): PyPDF2 text extraction
- **OCR PDF** (`food_garden.py`, `t_marx.py`): pdf2image + pytesseract with hardcoded pixel coordinates at 300 DPI

## Key conventions

- All menus are Monday-Friday only; weekends default to Monday
- Dish names are stored in German (`name_german`); English translation happens at display time via `deep-translator` (Google Translate, de->en)
- Streamlit caching: `@st.cache_resource` for singletons, `@st.cache_data(ttl=...)` for fetched data (1h menus, 24h translations)
- `packages.txt` lists apt packages for Streamlit Cloud deployment
- `.streamlit/secrets.toml` is gitignored
