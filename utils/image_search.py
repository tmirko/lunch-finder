"""
Image search utilities for fetching dish images.
Uses Google Custom Search or web scraping as fallback.
"""
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import re


class ImageSearch:
    """Search for dish images using web scraping."""
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
        
        # Add food-related keywords to improve search results
        search_query = f"{query} Gericht Essen"
        
        try:
            # Use DuckDuckGo image search as it's more reliable for scraping
            url = self._search_duckduckgo(search_query)
            if url:
                self._cache[query] = url
                return url
        except Exception as e:
            print(f"Image search error: {e}")
        
        return ""
    
    def _search_duckduckgo(self, query: str) -> str:
        """Search for images using DuckDuckGo."""
        try:
            # DuckDuckGo image search
            search_url = f"https://duckduckgo.com/?q={quote_plus(query)}&iax=images&ia=images"
            
            response = requests.get(search_url, headers=self.HEADERS, timeout=5)
            
            # DuckDuckGo loads images via JavaScript, so let's try the API endpoint
            # This is a simpler approach using the vqd token
            vqd_match = re.search(r'vqd="([^"]+)"', response.text)
            if not vqd_match:
                return self._get_placeholder_image(query)
            
            vqd = vqd_match.group(1)
            
            api_url = f"https://duckduckgo.com/i.js?q={quote_plus(query)}&vqd={vqd}"
            api_response = requests.get(api_url, headers=self.HEADERS, timeout=5)
            
            if api_response.status_code == 200:
                data = api_response.json()
                results = data.get('results', [])
                if results:
                    return results[0].get('image', '')
            
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        
        return self._get_placeholder_image(query)
    
    def _get_placeholder_image(self, query: str) -> str:
        """Generate a placeholder image URL using a food placeholder service."""
        # Use a generic food placeholder
        return f"https://source.unsplash.com/300x200/?{quote_plus(query)},food"
    
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
