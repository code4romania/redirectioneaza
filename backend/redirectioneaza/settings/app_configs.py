from base64 import urlsafe_b64encode

from cryptography.fernet import Fernet

from utils.constants.time import MONTHS

from .environment import env

# Global parameters
TITLE = env.str("SITE_TITLE")

# Redirections deadline
REDIRECTIONS_LIMIT_TO_CURRENT_YEAR = env.bool("REDIRECTIONS_LIMIT_TO_CURRENT_YEAR")

REDIRECTIONS_DEADLINE_YEAR = env.int("REDIRECTIONS_LIMIT_YEAR")
REDIRECTIONS_DEADLINE_MONTH = env.int("REDIRECTIONS_LIMIT_MONTH")
REDIRECTIONS_DEADLINE_DAY = env.int("REDIRECTIONS_LIMIT_DAY")

DEFAULT_RUN_METHOD = env.str("DEFAULT_RUN_METHOD")
FORMS_DOWNLOAD_METHOD = env.str("FORMS_DOWNLOAD_METHOD", DEFAULT_RUN_METHOD)
DONATIONS_CSV_DOWNLOAD_METHOD = env.str("DONATIONS_CSV_DOWNLOAD_METHOD", DEFAULT_RUN_METHOD)
USER_ANONYMIZATION_METHOD = env.str("USER_ANONYMIZATION_METHOD", DEFAULT_RUN_METHOD)

DONATIONS_XML_LIMIT_PER_FILE = env.int("DONATIONS_XML_LIMIT_PER_FILE")
DONATIONS_CSV_LIMIT_PER_FILE = env.int("DONATIONS_CSV_LIMIT_PER_FILE")

REDIRECTIONS_LIMIT_MONTH_NAME = MONTHS[REDIRECTIONS_DEADLINE_MONTH - 1]["month"]

START_YEAR = 2016

CHART_COLORS = [
    # Colors from the Figma specifications
    # #3857B9
    {"r": 56, "g": 87, "b": 185},
    # #38B9A2
    {"r": 56, "g": 185, "b": 162},
    # #AF38B9
    {"r": 175, "g": 56, "b": 185},
    # #88B938
    {"r": 136, "g": 185, "b": 56},
    # Randomly generated colors
    {"r": 255, "g": 99, "b": 132},
    {"r": 54, "g": 162, "b": 235},
    {"r": 255, "g": 206, "b": 86},
    {"r": 75, "g": 192, "b": 192},
    {"r": 153, "g": 102, "b": 255},
    {"r": 255, "g": 159, "b": 64},
    {"r": 205, "g": 92, "b": 92},
    {"r": 50, "g": 205, "b": 50},
    {"r": 255, "g": 99, "b": 71},
    {"r": 255, "g": 215, "b": 0},
    {"r": 0, "g": 128, "b": 128},
    {"r": 0, "g": 0, "b": 128},
    {"r": 128, "g": 0, "b": 128},
    {"r": 128, "g": 0, "b": 0},
    {"r": 0, "g": 128, "b": 0},
    {"r": 0, "g": 0, "b": 0},
]

# Encryption settings
ENCRYPT_KEY = env.str("ENCRYPT_KEY", "%INVALID%")
if len(ENCRYPT_KEY) != 32 or ENCRYPT_KEY == "%INVALID%":
    raise Exception("ENCRYPT_KEY must be exactly 32 characters long")
FERNET_OBJECT = Fernet(urlsafe_b64encode(ENCRYPT_KEY.encode("utf-8")))

SEARCH_QUERY_MIN_LENGTH = env.int("SEARCH_QUERY_MIN_LENGTH", 3)
