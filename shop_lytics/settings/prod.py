from .common import *
import dj_database_url
import os

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(" ")

REDIS_URL = os.environ.get("REDIS_URL")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

BASE_URL = os.environ.get("BASE_URL")

CORS_ALLOWED_ORIGINS = [
    "https://shop-lytics-frontend.onrender.com",
]


DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

DEBUG = False


DATABASES = {"default": dj_database_url.config()}

# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
# EMAIL_HOST = "smtp.sendgrid.net"
# EMAIL_HOST_USER = "apikey"
# EMAIL_HOST_PASSWORD = os.environ.get("SEND_GRID_API_KEY")
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True

SENDGRID_SANDBOX_MODE_IN_DEBUG = False
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

SECRET_KEY = os.environ.get("SECRET_KEY")

SHOPIFY_API_KEY = os.environ.get("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.environ.get("SHOPIFY_API_SECRET")
