"""Minimal parser check for The Oak's text PDF."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from providers.oak import OakProvider


menu = OakProvider()._parse_menu_text("""Monday 13.7.26
Soup
(G, L)
Main course
Tuesday 14.7.26
Another soup
Another main
Vegetarian Menu Monday to Wednesday
Vegetarian dish
Vegetarian Menu Thursday and Friday
Another vegetarian dish""")

assert [item.name_german for item in menu["Monday"].items] == ["Soup", "Main course", "Vegetarian dish"]
assert [item.name_german for item in menu["Tuesday"].items] == ["Another soup", "Another main", "Vegetarian dish"]
assert menu["Friday"].items[-1].name_german == "Another vegetarian dish"
