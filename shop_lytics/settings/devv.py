from .common import *

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

SHOPIFY_API_KEY = "YOUR_SHOPIFY_CLIENT_ID_FROM_YOUR_APP"
BASE_URL = "https://127.0.0.1:8000"
SHOPIFY_API_SECRET = "YOUR_SHOPIFY_CLIENT_SECRET_FROM_YOUR_APP"

CORS_ALLOWED_ORIGINS = [
    "null",
]

DEFAULT_FROM_EMAIL = "YOUR_GMAIL"

DEBUG = True

# Postgres
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": "YOUR_DB_NAME",
#         "USER": "YOUR_DB_USER",
#         "PASSWORD": "YOUR_USER_PASSWORD",
#         "HOST": "localhost",
#     }
# }

# SQLite
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = "YOUR_GMAIL"
EMAIL_HOST_PASSWORD = "YOUR_GMAIL_APP_PASS"
EMAIL_PORT = 587
EMAIL_USE_TLS = True


SECRET_KEY = "django-insecure-yp-+@j7qll*cui-vq5i_a=g^!e=6e^6pb@mziv^z(tr20#(uq4"
