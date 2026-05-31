"""
Image search utilities for fetching dish images.
Uses DuckDuckGo image search to find relevant food images.
"""
import time
from ddgs import DDGS


class ImageSearch:
    """Search for dish images using DuckDuckGo."""
    
    def __init__(self):
        self._cache: dict[str, str] = {}
        self._last_request_time: float = 0
    
    def search_image(self, query: str) -> str:
        if not query:
            return ""
        
        if query in self._cache:
            return self._cache[query]
        
        image_url = self._search_ddg_images(query)
        
        if image_url:
            self._cache[query] = image_url
            return image_url
        
        return ""
    
    def _search_ddg_images(self, query: str) -> str:
        try:
            elapsed = time.time() - self._last_request_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            search_query = f"{query} Gericht"
            self._last_request_time = time.time()
            
            with DDGS() as ddgs:
                results = list(ddgs.images(search_query, max_results=3))
                for result in results:
                    image_url = result.get("image", "")
                    if image_url and self._is_valid_image_url(image_url):
                        return image_url
        except Exception as e:
            print(f"Image search error: {e}")
        
        return ""
    
    def _is_valid_image_url(self, url: str) -> bool:
        if not url:
            return False
        if len(url) < 20 or len(url) > 500:
            return False
        if not url.startswith("http"):
            return False
        return True
    
    def search_images_batch(self, queries: list[str]) -> dict[str, str]:
        results = {}
        for query in queries:
            results[query] = self.search_image(query)
        return results
