from django.urls import reverse_lazy

from .environment import env

# Login & Auth settings
LOGIN_URL = reverse_lazy("login")
LOGIN_REDIRECT_URL = reverse_lazy("home")
LOGOUT_REDIRECT_URL = reverse_lazy("home")

AWS_COGNITO_DOMAIN = env.str("AWS_COGNITO_DOMAIN")
AWS_COGNITO_CLIENT_ID = env.str("AWS_COGNITO_CLIENT_ID")
AWS_COGNITO_CLIENT_SECRET = env.str("AWS_COGNITO_CLIENT_SECRET")
AWS_COGNITO_USER_POOL_ID = env.str("AWS_COGNITO_USER_POOL_ID")
AWS_COGNITO_REGION = env.str("AWS_COGNITO_REGION")

# Django Allauth settings
SOCIALACCOUNT_PROVIDERS = {
    "amazon_cognito": {
        "DOMAIN": "https://" + AWS_COGNITO_DOMAIN,
        "EMAIL_AUTHENTICATION": env.bool("AWS_COGNITO_EMAIL_AUTHENTICATION"),
        "VERIFIED_EMAIL": env.bool("AWS_COGNITO_VERIFIED_EMAIL"),
        "APPS": [
            {
                "client_id": AWS_COGNITO_CLIENT_ID,
                "secret": AWS_COGNITO_CLIENT_SECRET,
            },
        ],
    }
}

# Django Allauth Social Login adapter
SOCIALACCOUNT_ADAPTER = "redirectioneaza.social_adapters.UserOrgAdapter"

# Django Allauth allow only social logins
SOCIALACCOUNT_ONLY = False
SOCIALACCOUNT_ENABLED = True
ACCOUNT_EMAIL_VERIFICATION = "none"

# NGO Hub settings
NGOHUB_HOME_HOST = env("NGOHUB_HOME_HOST")
NGOHUB_HOME_BASE = f"https://{env('NGOHUB_HOME_HOST')}/"
NGOHUB_APP_BASE = f"https://{env('NGOHUB_APP_HOST')}/"
NGOHUB_API_HOST = env("NGOHUB_API_HOST")
NGOHUB_API_BASE = f"https://{NGOHUB_API_HOST}/"
NGOHUB_API_ACCOUNT = env("NGOHUB_API_ACCOUNT")
NGOHUB_API_KEY = env("NGOHUB_API_KEY")

# NGO Hub user roles
NGOHUB_ROLE_SUPER_ADMIN = "super-admin"
NGOHUB_ROLE_NGO_ADMIN = "admin"
NGOHUB_ROLE_NGO_EMPLOYEE = "employee"
