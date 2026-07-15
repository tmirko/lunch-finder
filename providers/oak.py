"""The Oak weekly lunch-menu provider."""
import io
import re
from typing import Optional

import requests
from PyPDF2 import PdfReader

from providers.base import MenuProvider, MenuItem, DailyMenu


class OakProvider(MenuProvider):
    """Provider for The Oak restaurant in Vienna."""

    MENU_URL = "https://theoak1030.at/menu/lunch-menu/"
    DAYS = {day.lower(): day for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
    PRICE = "€10.90"

    def __init__(self):
        self._weekly_menu: Optional[dict[str, DailyMenu]] = None

    @property
    def name(self) -> str:
        return "The Oak"

    @property
    def url(self) -> str:
        return self.MENU_URL

    def get_menu(self, day: str) -> DailyMenu:
        if self._weekly_menu is None:
            self._weekly_menu = self.fetch_weekly_menu()
        return self._weekly_menu.get(day, DailyMenu(day=day, items=[], provider_name=self.name))

    def fetch_weekly_menu(self) -> dict[str, DailyMenu]:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            page = requests.get(self.MENU_URL, timeout=15, headers=headers)
            page.raise_for_status()
            match = re.search(r'https?[^"\']+\.pdf', page.text)
            if not match:
                print("The Oak lunch-menu PDF not found")
                return self._empty_weekly_menu()
            pdf = requests.get(match.group(), timeout=15, headers=headers)
            pdf.raise_for_status()
            text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf.content)).pages)
            return self._parse_menu_text(text)
        except (requests.RequestException, ValueError) as error:
            print(f"Error fetching The Oak menu: {error}")
            return self._empty_weekly_menu()

    def _parse_menu_text(self, text: str) -> dict[str, DailyMenu]:
        menu = self._empty_weekly_menu()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for index, line in enumerate(lines):
            day = self.DAYS.get(line.split()[0].lower()) if line.split() else None
            if day:
                dishes = []
                for item in lines[index + 1:]:
                    if item.split()[0].lower() in self.DAYS or item.lower().startswith("vegetarian menu"):
                        break
                    if not item.startswith("("):
                        dishes.append(item)
                    if len(dishes) == 2:
                        break
                menu[day].items.extend(MenuItem(item, price=self.PRICE) for item in dishes)
            elif line.lower().startswith("vegetarian menu") and index + 1 < len(lines):
                dish = lines[index + 1]
                days = [day for day in self.DAYS.values() if day.lower() in line.lower()]
                if " to " in line.lower() and len(days) == 2:
                    day_order = list(self.DAYS.values())
                    days = day_order[day_order.index(days[0]):day_order.index(days[1]) + 1]
                for day in days:
                    menu[day].items.append(MenuItem(dish, price=self.PRICE, description="Vegetarian"))
        return menu

    def _empty_weekly_menu(self) -> dict[str, DailyMenu]:
        return {day: DailyMenu(day=day, items=[], provider_name=self.name) for day in self.DAYS.values()}
