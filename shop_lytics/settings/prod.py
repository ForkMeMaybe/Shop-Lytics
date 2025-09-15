from .common import *
import dj_database_url
import os

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS").split(" ")

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

SHOPIFY_API_KEY = os.environ.get("SHOPIFY_API_KEY")
BASE_URL = os.environ.get("BASE_URL")
SHOPIFY_API_SECRET = os.environ.get("SHOPIFY_API_SECRET")

CORS_ALLOWED_ORIGINS = [
    "https://shop-lytics-frontend.onrender.com",
]

SECRET_KEY = os.environ.get("SECRET_KEY")

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

DEBUG = os.environ.get("DEBUG")

DATABASES = {"default": dj_database_url.config()}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
