import os
from pathlib import Path

# Constants for memory sizes
KIBIBYTE = 1024
MEBIBYTE = KIBIBYTE * 1024
GIBIBYTE = MEBIBYTE * 1024
TEBIBYTE = GIBIBYTE * 1024

# Constants for time
SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY


# Build paths inside the project like this: BASE_DIR / 'subdir'.
ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASE_DIR = os.path.abspath(os.path.join(ROOT, "backend"))

ENV_FILE_NAME = os.environ.get("ENV_FILE_NAME", ".env.local")
ENV_FILE_PATH = os.path.join(BASE_DIR, os.pardir, ENV_FILE_NAME)
