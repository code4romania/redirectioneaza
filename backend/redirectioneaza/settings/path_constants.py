import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASE_DIR = os.path.abspath(os.path.join(ROOT, "backend"))

ENV_FILE_NAME = os.environ.get("ENV_FILE_NAME", ".env.local")
ENV_FILE_PATH = os.path.join(BASE_DIR, os.pardir, ENV_FILE_NAME)
