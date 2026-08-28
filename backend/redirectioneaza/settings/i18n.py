# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
import os

from .environment import env
from .path_constants import BASE_DIR

LANGUAGE_CODE = env.str("LANGUAGE_CODE")

TIME_ZONE = "Europe/Bucharest"

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
    os.path.join(BASE_DIR, "locale_localflavor"),
]
