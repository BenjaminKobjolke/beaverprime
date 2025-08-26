"""
Display Settings Service for BeaverHabits application.

This service manages user display preferences including font size and UI display options.
All settings are stored in app.storage.user and persist across sessions.
"""

from nicegui import app
from typing import Dict, Any
from beaverhabits.logging import logger


class DisplaySettingsService:
    """Service for managing display preferences."""
    
    # Default settings
    DEFAULT_SETTINGS = {
        "font_size": 1.0,
        "show_consecutive_weeks": True,
    }
    
    # Validation ranges
    MIN_FONT_SIZE = 1.0
    MAX_FONT_SIZE = 3.0
    
    @classmethod
    def get_display_settings(cls) -> Dict[str, Any]:
        """Get all display settings as a dictionary."""
        try:
            print(f"[DISPLAY] Getting display settings from storage")
            stored_settings = app.storage.user.get("display_settings", {})
            print(f"[DISPLAY] Raw stored settings: {stored_settings}")
            
            # Merge with defaults to handle missing keys
            settings = cls.DEFAULT_SETTINGS.copy()
            settings.update(stored_settings)
            
            # Validate and clamp values
            settings["font_size"] = max(cls.MIN_FONT_SIZE, min(cls.MAX_FONT_SIZE, settings["font_size"]))
            settings["show_consecutive_weeks"] = bool(settings["show_consecutive_weeks"])
            
            print(f"[DISPLAY] Final settings: {settings}")
            return settings
            
        except Exception as e:
            print(f"[DISPLAY] Error getting settings, using defaults: {e}")
            logger.warning(f"Error getting display settings, using defaults: {e}")
            return cls.DEFAULT_SETTINGS.copy()
    
    @classmethod
    def save_display_settings(cls, settings: Dict[str, Any]) -> bool:
        """Save display settings to user storage."""
        try:
            print(f"[DISPLAY] Attempting to save settings: {settings}")
            
            # Validate settings
            if not isinstance(settings, dict):
                print(f"[DISPLAY] Invalid settings type: {type(settings)}")
                return False
            
            # Create validated settings object
            validated_settings = {}
            
            # Validate font size
            if "font_size" in settings:
                font_size = float(settings["font_size"])
                validated_settings["font_size"] = max(cls.MIN_FONT_SIZE, min(cls.MAX_FONT_SIZE, font_size))
            
            # Validate show_consecutive_weeks
            if "show_consecutive_weeks" in settings:
                validated_settings["show_consecutive_weeks"] = bool(settings["show_consecutive_weeks"])
            
            print(f"[DISPLAY] Validated settings: {validated_settings}")
            
            # Store in user preferences
            print(f"[DISPLAY] Current storage before update: {dict(app.storage.user)}")
            app.storage.user.update({"display_settings": validated_settings})
            print(f"[DISPLAY] Current storage after update: {dict(app.storage.user)}")
            
            # Verify storage
            stored_back = app.storage.user.get("display_settings", {})
            print(f"[DISPLAY] Verified stored settings: {stored_back}")
            
            logger.info(f"Display settings saved successfully: {validated_settings}")
            return True
            
        except Exception as e:
            print(f"[DISPLAY] Error saving settings: {e}")
            logger.error(f"Error saving display settings: {e}", exc_info=True)
            return False
    
    @classmethod
    def get_font_size(cls) -> float:
        """Get the current font size setting."""
        settings = cls.get_display_settings()
        return settings["font_size"]
    
    @classmethod
    def get_show_consecutive_weeks(cls) -> bool:
        """Get the show consecutive weeks setting."""
        settings = cls.get_display_settings()
        return settings["show_consecutive_weeks"]
    
    @classmethod
    def get_font_size_css(cls) -> str:
        """Generate CSS custom properties for font size scaling."""
        font_size = cls.get_font_size()
        
        # Calculate specific font sizes for different elements
        # Base sizes: habit title (default), goal label (text-sm ≈ 0.875em), consecutive weeks (text-xs ≈ 0.75em)
        habit_title_size = font_size  # Main habit title
        goal_size = font_size * 0.875  # Goal indicators like "3x" 
        weeks_size = font_size * 0.75  # Consecutive weeks like "2w"
        
        css = f"""
        :root {{
            --habit-font-size: {habit_title_size};
            --goal-font-size: {goal_size};
            --weeks-font-size: {weeks_size};
        }}
        
        /* Apply font sizes to habit elements */
        .habit-title {{
            font-size: calc(var(--habit-font-size) * 1em) !important;
        }}
        
        .habit-goal {{
            font-size: calc(var(--goal-font-size) * 1em) !important;
        }}
        
        .habit-weeks {{
            font-size: calc(var(--weeks-font-size) * 1em) !important;
        }}
        """
        
        return css
    
    @classmethod
    def init_display_settings(cls) -> None:
        """Initialize display settings with defaults if not present."""
        try:
            if "display_settings" not in app.storage.user:
                print(f"[DISPLAY] Initializing default display settings")
                cls.save_display_settings(cls.DEFAULT_SETTINGS)
            else:
                print(f"[DISPLAY] Display settings already exist")
        except Exception as e:
            print(f"[DISPLAY] Error initializing display settings: {e}")
            logger.warning(f"Error initializing display settings: {e}")


# Convenience functions for backward compatibility and easy access
def get_display_settings() -> Dict[str, Any]:
    """Get all display settings."""
    return DisplaySettingsService.get_display_settings()


def save_display_settings(settings: Dict[str, Any]) -> bool:
    """Save display settings."""
    return DisplaySettingsService.save_display_settings(settings)


def get_font_size() -> float:
    """Get current font size."""
    return DisplaySettingsService.get_font_size()


def get_show_consecutive_weeks() -> bool:
    """Get show consecutive weeks setting."""
    return DisplaySettingsService.get_show_consecutive_weeks()


def get_font_size_css() -> str:
    """Get font size CSS."""
    return DisplaySettingsService.get_font_size_css()


def init_display_settings() -> None:
    """Initialize display settings."""
    DisplaySettingsService.init_display_settings()