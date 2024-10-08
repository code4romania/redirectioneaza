from .constants import HOUR, MINUTE
from .environment import env

# Cache settings
TIMEOUT_CACHE_SHORT = 1 * MINUTE
TIMEOUT_CACHE_NORMAL = 15 * MINUTE
TIMEOUT_CACHE_LONG = 2 * HOUR

ENABLE_CACHE = env.bool("ENABLE_CACHE")
if ENABLE_CACHE:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "redirect_cache_default",
            "TIMEOUT": TIMEOUT_CACHE_NORMAL,  # default cache timeout in seconds
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
