import environ

from .constants import ENV_FILE_PATH, HOUR

env = environ.Env(
    # set casting, default value
    # Django settings
    DEBUG=(bool, False),
    DJANGO_VITE_DEV_MODE=(bool, False),
    DJANGO_VITE_DEV_SERVER_PORT=(int, 3000),
    ENVIRONMENT=(str, "production"),
    DATA_UPLOAD_MAX_NUMBER_FIELDS=(int, 1000),
    OLD_SESSION_KEY=(str, ""),
    LOG_LEVEL=(str, "WARNING"),
    ENABLE_CACHE=(bool, True),
    ENABLE_FORMS_DOWNLOAD=(bool, True),
    TIMEDELTA_FORMS_DOWNLOAD_MINUTES=(int, 6 * HOUR),
    TIMEDELTA_DONATIONS_LIMIT_DOWNLOAD_DAYS=(int, 31),
    IS_CONTAINERIZED=(bool, False),
    RECAPTCHA_ENABLED=(bool, True),
    # proxy headers
    USE_PROXY_FORWARDED_HOST=(bool, False),
    PROXY_SSL_HEADER=(str, "HTTP_CLOUDFRONT_FORWARDED_PROTO"),
    # db settings
    DATABASE_ENGINE=(str, "sqlite3"),
    DATABASE_NAME=(str, "default"),
    DATABASE_USER=(str, "root"),
    DATABASE_PASSWORD=(str, ""),
    DATABASE_HOST=(str, "localhost"),
    DATABASE_PORT=(str, "3306"),
    # site settings
    APEX_DOMAIN=(str, "redirectioneaza.ro"),
    BASE_WEBSITE=(str, "https://redirectioneaza.ro"),
    SITE_TITLE=(str, "redirectioneaza.ro"),
    DONATIONS_LIMIT_DAY=(int, 25),
    DONATIONS_LIMIT_MONTH=(int, 5),
    DONATIONS_LIMIT_YEAR=(int, 2016),
    DONATIONS_LIMIT_TO_CURRENT_YEAR=(bool, True),
    DONATIONS_XML_LIMIT_PER_FILE=(int, 100),
    # security settings
    ALLOWED_HOSTS=(list, ["*"]),
    CORS_ALLOWED_ORIGINS=(list, []),
    CORS_ALLOW_ALL_ORIGINS=(bool, False),
    # email settings
    EMAIL_SEND_METHOD=(str, "async"),
    EMAIL_BACKEND=(str, "django.core.mail.backends.console.EmailBackend"),
    EMAIL_HOST=(str, ""),
    EMAIL_PORT=(str, ""),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    EMAIL_USE_TLS=(str, ""),
    EMAIL_FAIL_SILENTLY=(bool, False),
    CONTACT_EMAIL_ADDRESS=(str, "redirectioneaza@code4.ro"),
    DEFAULT_FROM_EMAIL=(str, "no-reply@code4.ro"),
    NO_REPLY_EMAIL=(str, "no-reply@code4.ro"),
    # django-q2 settings
    DJANGO_Q_WORKERS_COUNT=(int, 1),
    DJANGO_Q_RECYCLE_RATE=(int, 100),
    DJANGO_Q_TIMEOUT_SECONDS=(int, 900),  # A task must finish in less than 15 minutes
    DJANGO_Q_RETRY_AFTER_TIMEOUT_SECONDS=(int, 300),  # Retry unfinished tasks 5 minutes after timeout
    DJANGO_Q_POLL_SECONDS=(int, 4),
    IMPORT_METHOD=(str, "async"),
    IMPORT_USE_BATCHES=(bool, True),
    IMPORT_BATCH_SIZE=(int, 100),
    # recaptcha settings
    CAPTCHA_PUBLIC_KEY=(str, ""),
    CAPTCHA_PRIVATE_KEY=(str, ""),
    CAPTCHA_REQUIRED_SCORE=(float, 0.5),
    CAPTCHA_VERIFY_URL=(str, "https://www.google.com/recaptcha/api/siteverify"),
    CAPTCHA_POST_PARAM=(str, "g-recaptcha-response"),
    # aws settings
    AWS_REGION_NAME=(str, ""),
    # S3
    USE_S3=(bool, False),
    AWS_S3_REGION_NAME=(str, ""),
    AWS_S3_SIGNATURE_VERSION=(str, "s3v4"),
    AWS_S3_ADDRESSING_STYLE=(str, "virtual"),
    AWS_S3_STORAGE_DEFAULT_BUCKET_NAME=(str, ""),
    AWS_S3_STORAGE_PUBLIC_BUCKET_NAME=(str, ""),
    AWS_S3_STORAGE_STATIC_BUCKET_NAME=(str, ""),
    AWS_S3_DEFAULT_ACL=(str, "private"),
    AWS_S3_PUBLIC_ACL=(str, ""),
    AWS_S3_STATIC_ACL=(str, ""),
    AWS_S3_DEFAULT_PREFIX=(str, ""),
    AWS_S3_PUBLIC_PREFIX=(str, ""),
    AWS_S3_STATIC_PREFIX=(str, ""),
    AWS_S3_DEFAULT_CUSTOM_DOMAIN=(str, ""),
    AWS_S3_PUBLIC_CUSTOM_DOMAIN=(str, ""),
    AWS_S3_STATIC_CUSTOM_DOMAIN=(str, ""),
    # SES
    AWS_SES_REGION_NAME=(str, ""),
    AWS_SES_USE_V2=(bool, True),
    AWS_SES_CONFIGURATION_SET_NAME=(str, None),
    AWS_SES_AUTO_THROTTLE=(float, 0.5),
    AWS_SES_REGION_ENDPOINT=(str, ""),
    # Cognito
    AWS_COGNITO_DOMAIN=(str, ""),
    AWS_COGNITO_CLIENT_ID=(str, ""),
    AWS_COGNITO_CLIENT_SECRET=(str, ""),
    AWS_COGNITO_USER_POOL_ID=(str, ""),
    AWS_COGNITO_REGION=(str, ""),
    AWS_COGNITO_EMAIL_AUTHENTICATION=(bool, True),
    AWS_COGNITO_VERIFIED_EMAIL=(bool, True),
    # NGO Hub
    NGOHUB_HOME_HOST=(str, "ngohub.ro"),
    NGOHUB_APP_HOST=(str, "app.ngohub.ro"),
    NGOHUB_API_HOST=(str, "api.ngohub.ro"),
    NGOHUB_API_ACCOUNT=(str, ""),
    NGOHUB_API_KEY=(str, ""),
    UPDATE_ORGANIZATION_METHOD=(str, "async"),
    # sentry
    SENTRY_DSN=(str, ""),
    SENTRY_TRACES_SAMPLE_RATE=(float, 0),
    SENTRY_PROFILES_SAMPLE_RATE=(float, 0),
    # Google Analytics:
    GOOGLE_ANALYTICS_ID=(str, ""),
    # App settings
    ENABLE_FULL_CUI_VALIDATION=(bool, True),
)

environ.Env.read_env(ENV_FILE_PATH)
