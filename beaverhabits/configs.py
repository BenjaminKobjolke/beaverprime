import calendar
import logging
import configparser
import os
from pathlib import Path

import dotenv
from pydantic_settings import BaseSettings

logging.getLogger("niceGUI").setLevel(logging.INFO)
dotenv.load_dotenv()

# Read database settings from settings.ini
config = configparser.ConfigParser()
config.read('settings.ini')

db_config = config['database']
db_host = db_config.get('host', 'localhost')
db_port = db_config.get('port', '3306')
db_name = db_config.get('database', 'beaverhabits')
db_user = db_config.get('user', 'root')
db_password = db_config.get('password', '')

# Construct database URL
db_password_part = f":{db_password}@" if db_password else "@"
DATABASE_URL = f"mysql+aiomysql://{db_user}{db_password_part}{db_host}:{db_port}/{db_name}"

# Email configuration
try:
    email_config = dict(config['email']) if 'email' in config else {}
except KeyError:
    email_config = {}

try:
    app_config = dict(config['app']) if 'app' in config else {}
except KeyError:
    app_config = {}

class Settings(BaseSettings):
    ENV: str = "dev"
    DEBUG: bool = False
    SENTRY_DSN: str = ""

    # NiceGUI
    NICEGUI_STORAGE_SECRET: str = "dev"
    GUI_MOUNT_PATH: str = "/gui"
    DEMO_MOUNT_PATH: str = "/demo"

    # Database
    DATABASE_URL: str = DATABASE_URL
    ENABLE_AUTOSAVE: bool = False  # Set to True to enable autosave (may cause issues with concurrent edits)
    MAX_USER_COUNT: int = -1
    JWT_SECRET: str = "54o53o847gdlfjfdljgd"
    JWT_LIFETIME_SECONDS: int = 60 * 60 * 24 * 30

    # Auth
    TRUSTED_EMAIL_HEADER: str = ""
    TRUSTED_LOCAL_EMAIL: str = ""
    SKIP_OLD_PASSWORD_CHECK_ON_CHANGE: bool = True # Added for temporarily skipping old password check

    # Email Configuration
    SMTP_HOST: str = email_config.get('smtp_host', 'localhost')
    SMTP_PORT: int = int(email_config.get('smtp_port', '587'))
    SMTP_USER: str = email_config.get('smtp_user', '')
    SMTP_PASSWORD: str = email_config.get('smtp_password', '')
    SMTP_USE_TLS: bool = str(email_config.get('smtp_use_tls', 'true')).lower() == 'true'
    FROM_EMAIL: str = email_config.get('from_email', 'noreply@example.com')
    FROM_NAME: str = email_config.get('from_name', 'Beaver Habits')

    # App Configuration  
    ROOT_URL: str = app_config.get('root_url', 'http://localhost:8000')
    REQUIRE_VERIFICATION: bool = str(app_config.get('require_verification', 'true')).lower() == 'true'
    VERIFICATION_SUBJECT: str = app_config.get('verification_subject', 'Please verify your account')
    RESET_SUBJECT: str = app_config.get('reset_subject', 'Reset your password')

    # Customization
    FIRST_DAY_OF_WEEK: int = calendar.MONDAY
    ENABLE_IOS_STANDALONE: bool = False
    ENABLE_DESKTOP_ALGIN_CENTER: bool = True

    INDEX_SHOW_HABIT_COUNT: bool = False
    INDEX_SHOW_PRIORITY: bool = False  # Set to False to hide priority numbers
    INDEX_HABIT_NAME_COLUMNS: int = 8
    INDEX_HABIT_DATE_COLUMNS: int = -1  # -1 for week view (Mon-Sun), positive number for past N days

    # Colors
    HABIT_COLOR_COMPLETED: str = "lightgreen"
    HABIT_COLOR_INCOMPLETE: str = "yellow"
    HABIT_COLOR_SKIPPED: str = "grey"
    HABIT_COLOR_LAST_WEEK_INCOMPLETE: str = "red"
    HABIT_COLOR_DAY_NUMBER: str = "grey"

    # Features
    ENABLE_HABIT_NOTES: bool = False  # Set to False to disable notes
    ENABLE_LETTER_FILTER: bool = True  # Set to False to disable letter filter bar

    # Logging
    LOG_LEVEL: str = config.get('logging', 'level', fallback=os.environ.get("LOGURU_LEVEL", "WARNING"))  # Can be DEBUG, INFO, WARNING, ERROR, CRITICAL

    def is_dev(self):
        return self.ENV == "dev"

    def is_trusted_env(self):
        return self.TRUSTED_LOCAL_EMAIL


settings = Settings()
