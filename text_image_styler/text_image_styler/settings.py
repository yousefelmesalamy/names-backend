# Django settings for text_image_styler project.
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-3bc*us(5q+5dp&*c)rk3giv2thc=14c+(#9xv9!+=fm-b5%m!s'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']  # Allow all hosts

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',  # CORS headers app
    'styler'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Must be at the top
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'text_image_styler.urls'

# =================== NO CORS RESTRICTIONS - START ===================
CORS_ALLOW_ALL_ORIGINS = True  # Allow ALL origins
CORS_ALLOW_CREDENTIALS = True  # Allow credentials

# Remove all restrictions from headers
CORS_ALLOW_HEADERS = [
    '*',  # Allow ALL headers
]

# Remove all restrictions from methods
CORS_ALLOW_METHODS = [
    '*',  # Allow ALL methods
]

# Allow all origins without any restrictions
CORS_ALLOWED_ORIGINS = [
    "http://*",
    "https://*",
]

# Allow all origin regex patterns
CORS_ALLOWED_ORIGIN_REGEXES = [
    r".*",  # Match EVERYTHING
]

# Additional security headers that might block - DISABLE THEM
CORS_EXPOSE_HEADERS = ['*']
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours cache

# Disable CSRF for API if needed (for testing only)
CSRF_TRUSTED_ORIGINS = [
    'http://*',
    'https://*',
]
# =================== NO CORS RESTRICTIONS - END ===================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'text_image_styler.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (user uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# # Make sure these are in ALLOWED_HOSTS
# ALLOWED_HOSTS = ['yousefelmesalamy.pythonanywhere.com', '127.0.0.1', 'localhost']