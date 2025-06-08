"""
Django settings for eventhub project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# === Configuración general ===

SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-default-secret")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")

# === Apps instaladas ===

INSTALLED_APPS = [
    "app",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
]

# === Middlewares ===

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "eventhub.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "eventhub.wsgi.application"

# === Base de datos ===

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
    }
}

# === Validación de contraseñas ===

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# === Internacionalización ===

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

# === Usuario custom ===

AUTH_USER_MODEL = "app.User"

# === Archivos estáticos y media ===

STATIC_URL = os.getenv("STATIC_URL", "/static/")
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles" 

MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(BASE_DIR, "media"))

# === Autenticación ===

LOGIN_REDIRECT_URL = "/events/"
LOGIN_URL = "/accounts/login/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# === Default PK ===

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
