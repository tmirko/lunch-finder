"""
Image search utilities for fetching dish images.
Uses Google Images search to find relevant food images.
"""
import requests
from urllib.parse import quote_plus
import re


class ImageSearch:
    """Search for dish images using Google Images."""
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
    }
    
    def __init__(self):
        self._cache: dict[str, str] = {}
    
    def search_image(self, query: str) -> str:
        """
        Search for an image based on the query using Google Images.
        
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
        
        # Try Google Images search
        image_url = self._search_google_images(query)
        
        if image_url:
            self._cache[query] = image_url
            return image_url
        
        return ""
    
    def _search_google_images(self, query: str) -> str:
        """Search Google Images and extract the first result."""
        try:
            # Add "Gericht" (dish) to improve food-related results
            search_query = f"{query} Gericht"
            
            # Google Images search URL
            url = f"https://www.google.com/search?q={quote_plus(search_query)}&tbm=isch&hl=de"
            
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            
            # Google embeds image URLs in the page in various formats
            # Look for image URLs in the response
            
            # Pattern 1: Look for direct image URLs in data attributes
            # Google uses base64 encoded data and actual URLs
            patterns = [
                # Match image URLs from Google's image data
                r'\["(https?://[^"]+\.(?:jpg|jpeg|png|webp))[^"]*",\d+,\d+\]',
                # Alternative pattern for image sources
                r'"ou":"(https?://[^"]+)"',
                # Another common pattern
                r'src="(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                for match in matches:
                    # Filter out Google's own URLs and thumbnails
                    if self._is_valid_image_url(match):
                        return match
            
            # Fallback: Try to find any reasonable image URL
            all_urls = re.findall(r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)', response.text, re.IGNORECASE)
            for url in all_urls:
                if self._is_valid_image_url(url):
                    return url
                    
        except Exception as e:
            print(f"Google Images search error: {e}")
        
        return ""
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL is a valid external image (not Google's internal)."""
        if not url:
            return False
        
        # Skip Google's own domains and encrypted thumbnails
        skip_domains = [
            'google.com',
            'gstatic.com', 
            'googleapis.com',
            'googleusercontent.com',
            'encrypted-tbn',
            'data:image',
        ]
        
        url_lower = url.lower()
        for domain in skip_domains:
            if domain in url_lower:
                return False
        
        # Must be a reasonable length (not too short, not too long)
        if len(url) < 20 or len(url) > 500:
            return False
            
        return True
    
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
