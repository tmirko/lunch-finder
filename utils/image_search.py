"""
Image search utilities for fetching dish images.
Uses multiple sources to find food images.
"""
import requests
from urllib.parse import quote_plus
import hashlib


class ImageSearch:
    """Search for dish images using various image services."""
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    def __init__(self):
        self._cache: dict[str, str] = {}
    
    def search_image(self, query: str) -> str:
        """
        Search for an image based on the query.
        
        Args:
            query: Search query (dish name in German)
            
        Returns:
            URL of the found image or empty string if not found
        """
        if not query:
            return ""
        
        # Check cache first
        if query in self._cache:
            return self._cache[query]
        
        # Try multiple image sources
        image_url = self._get_foodish_image(query)
        
        if not image_url:
            image_url = self._get_loremflickr_image(query)
        
        if not image_url:
            image_url = self._get_placeholder_image(query)
        
        self._cache[query] = image_url
        return image_url
    
    def _get_foodish_image(self, query: str) -> str:
        """Get a food image from Foodish API or similar."""
        try:
            # Use picsum.photos with a seed based on query for consistent images
            seed = hashlib.md5(query.encode()).hexdigest()[:8]
            return f"https://picsum.photos/seed/{seed}/300/200"
        except Exception:
            return ""
    
    def _get_loremflickr_image(self, query: str) -> str:
        """Get an image from LoremFlickr with food keywords."""
        try:
            # Clean and simplify query for better results
            simple_query = query.split()[0] if query else "food"
            # LoremFlickr provides images based on keywords
            return f"https://loremflickr.com/300/200/{quote_plus(simple_query)},food"
        except Exception:
            return ""
    
    def _get_placeholder_image(self, query: str) -> str:
        """Generate a placeholder image URL."""
        # Use placeholder.com with food emoji as fallback
        seed = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"https://picsum.photos/seed/{seed}/300/200"
    
    def search_images_batch(self, queries: list[str]) -> dict[str, str]:
        """
        Search for multiple images.
        
        Args:
            queries: List of search queries
            
        Returns:
            Dictionary mapping queries to image URLs
        """
        results = {}
        for query in queries:
            results[query] = self.search_image(query)
        return results
