import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from beaverhabits.logging import logger


class TranslationService:
    """Service for handling internationalization and translations."""
    
    def __init__(self, default_language: str = "en"):
        self.default_language = default_language
        self.current_language = default_language
        self.translations: Dict[str, Dict[str, Any]] = {}
        self._load_translations()
    
    def _load_translations(self):
        """Load all available translation files."""
        # Get the project root directory (where statics folder is located)
        project_root = Path(__file__).parent.parent.parent
        lang_dir = project_root / "statics" / "lang"
        
        if not lang_dir.exists():
            logger.warning(f"Language directory not found: {lang_dir}")
            return
        
        # Load all JSON files in the language directory
        for lang_file in lang_dir.glob("*.json"):
            language_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[language_code] = json.load(f)
                logger.info(f"Loaded translations for language: {language_code}")
            except Exception as e:
                logger.error(f"Error loading translations for {language_code}: {e}")
    
    def set_language(self, language_code: str):
        """Set the current language."""
        if language_code in self.translations:
            self.current_language = language_code
            logger.info(f"Language set to: {language_code}")
        else:
            logger.warning(f"Language not available: {language_code}, using {self.default_language}")
    
    def get_available_languages(self) -> list[str]:
        """Get list of available language codes."""
        return list(self.translations.keys())
    
    def get_language_display_names(self) -> Dict[str, str]:
        """Get display names for all available languages."""
        language_names = {
            "en": "English",
            "de": "Deutsch",
            "es": "Español",
            "fr": "Français",
            "it": "Italiano",
            "pt": "Português",
            "ru": "Русский",
            "zh": "中文",
            "ja": "日本語"
        }
        # Only return names for available languages
        return {code: language_names.get(code, code.upper()) for code in self.get_available_languages()}
    
    def get_user_language(self) -> str:
        """Get current user's language from storage."""
        try:
            from nicegui import app
            return app.storage.user.get("language", self.default_language)
        except Exception as e:
            logger.warning(f"Could not get user language from storage: {e}")
            return self.current_language
    
    def set_user_language(self, language_code: str) -> bool:
        """Set user's language preference and update current language."""
        if language_code in self.translations:
            self.current_language = language_code
            try:
                from nicegui import app
                app.storage.user.update({"language": language_code})
                logger.info(f"User language set to: {language_code}")
                return True
            except Exception as e:
                logger.error(f"Could not save user language to storage: {e}")
                return False
        else:
            logger.warning(f"Language not available: {language_code}")
            return False
    
    def init_user_language(self):
        """Initialize language from user storage or browser preference."""
        try:
            user_lang = self.get_user_language()
            if user_lang and user_lang != self.current_language:
                self.set_language(user_lang)
        except Exception as e:
            logger.warning(f"Could not initialize user language: {e}")
    
    def t(self, key: str, **kwargs) -> str:
        """
        Translate a key to the current language.
        
        Args:
            key: Translation key in dot notation (e.g., 'auth.login_title')
            **kwargs: Variables to substitute in the translation string
        
        Returns:
            Translated string with variables substituted
        """
        return self.translate(key, **kwargs)
    
    def translate(self, key: str, language: Optional[str] = None, **kwargs) -> str:
        """
        Translate a key to the specified or current language.
        
        Args:
            key: Translation key in dot notation (e.g., 'auth.login_title')
            language: Language code to use (defaults to current language)
            **kwargs: Variables to substitute in the translation string
        
        Returns:
            Translated string with variables substituted
        """
        lang = language or self.current_language
        
        # If language not available, fall back to default
        if lang not in self.translations:
            lang = self.default_language
        
        # If default language also not available, return the key itself
        if lang not in self.translations:
            logger.warning(f"No translations available, returning key: {key}")
            return key
        
        # Navigate through the nested dictionary structure
        translation_dict = self.translations[lang]
        keys = key.split('.')
        
        try:
            for k in keys:
                translation_dict = translation_dict[k]
            
            # If we got a string, substitute variables
            if isinstance(translation_dict, str):
                return translation_dict.format(**kwargs)
            else:
                logger.warning(f"Translation key does not point to a string: {key}")
                return key
                
        except (KeyError, TypeError) as e:
            logger.warning(f"Translation key not found: {key} (error: {e})")
            
            # Try to fall back to default language if we weren't already using it
            if lang != self.default_language:
                return self.translate(key, self.default_language, **kwargs)
            
            # If all else fails, return the key itself
            return key
    
    def reload_translations(self):
        """Reload translation files from disk."""
        self.translations.clear()
        self._load_translations()
        logger.info("Translations reloaded")


# Global translation service instance
translation_service = TranslationService()

# Convenience functions for easier usage
def t(key: str, **kwargs) -> str:
    """Shorthand function for translation."""
    return translation_service.translate(key, **kwargs)

def set_language(language_code: str):
    """Set the current language globally."""
    translation_service.set_language(language_code)

def get_available_languages() -> list[str]:
    """Get list of available languages."""
    return translation_service.get_available_languages()

def get_language_display_names():
    """Get display names for all available languages."""
    return translation_service.get_language_display_names()

def get_current_language() -> str:
    """Get current language code."""
    return translation_service.current_language

def set_user_language(language_code: str) -> bool:
    """Set user's language preference."""
    return translation_service.set_user_language(language_code)

def init_user_language():
    """Initialize user's language from storage."""
    return translation_service.init_user_language()

# Example usage:
# from beaverhabits.services.i18n import t
# 
# # Simple translation
# title = t("auth.login_title")
# 
# # Translation with variables  
# message = t("habits.successfully_added_habit", name="Morning Exercise")
# 
# # Check if translation exists
# if "de" in get_available_languages():
#     set_language("de")