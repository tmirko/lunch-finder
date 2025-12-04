"""
Translation utilities for the lunch finder app.
Uses deep-translator for German to English translation.
"""
from deep_translator import GoogleTranslator


class Translator:
    """Handles German to English translation."""
    
    def __init__(self):
        self._translator = GoogleTranslator(source='de', target='en')
        self._cache: dict[str, str] = {}
    
    def translate(self, text: str) -> str:
        """
        Translate German text to English.
        
        Args:
            text: German text to translate
            
        Returns:
            English translation
        """
        if not text:
            return ""
        
        # Check cache first
        if text in self._cache:
            return self._cache[text]
        
        try:
            translation = self._translator.translate(text)
            self._cache[text] = translation
            return translation
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original if translation fails
    
    def translate_batch(self, texts: list[str]) -> list[str]:
        """
        Translate multiple texts efficiently.
        
        Args:
            texts: List of German texts to translate
            
        Returns:
            List of English translations
        """
        results = []
        for text in texts:
            results.append(self.translate(text))
        return results
