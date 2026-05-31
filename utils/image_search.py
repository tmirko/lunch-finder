"""
Image search utilities for fetching dish images.
Uses Unsplash API to find relevant food images.
"""
import time
import requests


class ImageSearch:
    """Search for dish images using Unsplash API."""

    def __init__(self, access_key: str):
        self._cache: dict[str, str] = {}
        self._last_request_time: float = 0
        self._access_key = access_key
        self._base_url = "https://api.unsplash.com/search/photos"

    def search_image(self, query: str, english_query: str = "") -> str:
        if not query:
            return ""

        cache_key = query
        if cache_key in self._cache:
            return self._cache[cache_key]

        search_query = self._build_search_query(query, english_query)
        image_url = self._search_unsplash(search_query)

        if image_url:
            self._cache[cache_key] = image_url
            return image_url

        return ""

    def _build_search_query(self, german_name: str, english_name: str) -> str:
        if english_name:
            return english_name
        return german_name

    def _search_unsplash(self, query: str) -> str:
        try:
            elapsed = time.time() - self._last_request_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

            self._last_request_time = time.time()

            headers = {
                "Authorization": f"Client-ID {self._access_key}",
                "Accept-Version": "v1"
            }

            params = {
                "query": query,
                "per_page": 1,
                "orientation": "landscape",
                "content_filter": "high"
            }

            response = requests.get(
                self._base_url,
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    image_url = results[0].get("urls", {}).get("regular", "")
                    if image_url:
                        return image_url
            elif response.status_code == 403:
                print(f"Unsplash API rate limit exceeded for '{query}'")
            elif response.status_code != 200:
                print(f"Unsplash API error {response.status_code} for '{query}'")

        except requests.exceptions.Timeout:
            print(f"Unsplash API timeout for '{query}'")
        except Exception as e:
            print(f"Image search error for '{query}': {e}")

        return ""

    def search_images_batch(self, queries: list[str]) -> dict[str, str]:
        results = {}
        for query in queries:
            results[query] = self.search_image(query)
        return results
