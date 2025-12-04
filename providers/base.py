"""
Base provider class for lunch menu providers.
All menu providers should inherit from this class.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class MenuItem:
    """Represents a single menu item."""
    name_german: str
    name_english: str = ""
    price: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


@dataclass
class DailyMenu:
    """Represents a daily menu with multiple items."""
    day: str
    items: list[MenuItem]
    provider_name: str


class MenuProvider(ABC):
    """Abstract base class for menu providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the provider."""
        pass
    
    @property
    @abstractmethod
    def url(self) -> str:
        """Return the URL of the menu source."""
        pass
    
    @abstractmethod
    def get_menu(self, day: str) -> DailyMenu:
        """
        Get the menu for a specific day.
        
        Args:
            day: Day of the week (Monday, Tuesday, Wednesday, Thursday, Friday)
            
        Returns:
            DailyMenu object with the menu items for that day
        """
        pass
    
    @abstractmethod
    def fetch_weekly_menu(self) -> dict[str, DailyMenu]:
        """
        Fetch and parse the entire weekly menu.
        
        Returns:
            Dictionary mapping day names to DailyMenu objects
        """
        pass
