from .environment import env

# Feature flags
ENABLE_FLAG_CONTACT = env.bool("ENABLE_FLAG_CONTACT", False)

# Configurations for the NGO Hub integration
UPDATE_ORGANIZATION_METHOD = env("UPDATE_ORGANIZATION_METHOD")

# Other settings
ENABLE_FULL_CUI_VALIDATION = env.bool("ENABLE_FULL_CUI_VALIDATION")

# Form download settings
ENABLE_FORMS_DOWNLOAD = env.bool("ENABLE_FORMS_DOWNLOAD", True)
TIMEDELTA_FORMS_DOWNLOAD_MINUTES = env.int("TIMEDELTA_FORMS_DOWNLOAD_MINUTES")
