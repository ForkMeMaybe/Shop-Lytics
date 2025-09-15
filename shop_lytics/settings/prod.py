from .common import *
import dj_database_url
import os

ALLOWED_HOSTS = []

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

CLIENT_ID = os.environ.get("CLIENT_ID")
BASE_URL = os.environ.get("BASE_URL")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

CORS_ALLOWED_ORIGINS = [
    "null",
]

SECRET_KEY = os.environ.get("SECRET_KEY")

DEBUG = os.environ.get("DEBUG")

DATABASES = {"default": {dj_database_url.config()}}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
