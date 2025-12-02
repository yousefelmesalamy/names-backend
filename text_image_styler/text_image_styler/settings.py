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
    'jazzmin',  # Jazzmin Admin - MUST BE FIRST

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

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (user uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =================== JAZZMIN CONFIGURATION - START ===================
JAZZMIN_SETTINGS = {
    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header)
    "site_brand": "Text Image Styler",

    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header)
    "site_header": "Text Image Styler",

    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header)
    "site_title": "Text Image Styler",

    # Welcome text on the login screen
    "welcome_sign": "Welcome to Text Image Styler Admin",

    # Copyright on the footer
    "copyright": "Text Image Styler Ltd",

    # The model admin to search from the search bar, search bar omitted if excluded
    "search_model": "auth.User",

    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,

    # #############
    # Top Menu #
    # #############

    # Links to put along the top menu
    "topmenu_links": [
        # Url that gets reversed (Permissions can be added)
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},

        # external url that opens in a new window (Permissions can be added)
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},

        # model admin to link to (Permissions checked against model)
        {"model": "auth.User"},

        # App with dropdown menu to all its models pages (Permissions checked against models)
        {"app": "styler"},
    ],

    # #############
    # User Menu #
    # #############

    # Additional links to include in the user menu on the top right ("app" url type is not allowed)
    "usermenu_links": [
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "auth.user"}
    ],

    # #############
    # Side Menu #
    # #############

    # Whether to display the side menu
    "show_sidebar": True,

    # Whether to aut expand the menu
    "navigation_expanded": True,

    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": [],

    # Hide these models when generating side menu (e.g auth.user)
    "hide_models": [],

    # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
    "order_with_respect_to": ["auth", "styler"],

    # Custom links to append to app groups, keyed on app name
    "custom_links": {
        "styler": [{
            "name": "Generate Styles",
            "url": "/",
            "icon": "fas fa-palette",
            "permissions": ["styler.view_style"]
        }]
    },

    # Custom icons for side menu apps/models
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "styler": "fas fa-palette",
    },

    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # ############
    # UI Tweaks #
    # ############

    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": None,
    "custom_js": None,

    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": True,

    # ############
    # Change view #
    # ############

    # Render out the change view as a single form, or in tabs, current options are
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "horizontal_tabs",

    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},

    # Add a language dropdown into the admin
    "language_chooser": False,

    # #############
    # Theme Settings #
    # #############

    # Theme to use
    "theme": "light",  # Using light theme

    # Primary color
    "primary_color": "#4a6fa5",  # Soft blue

    # Secondary color
    "secondary_color": "#f8f9fa",  # Light gray

    # Background color
    "background_color": "#ffffff",  # White

    # Hover color
    "hover_color": "#e9ecef",  # Light gray

    # Navbar color
    "navbar": "navbar-white navbar-light",

    # No navbar border
    "no_navbar_border": False,

    # Body classes
    "body_classes": "",

    # Sidebar classes
    "sidebar_classes": "sidebar-light-primary",

    # Brand classes
    "brand_classes": "brand-link",

    # Brand background color
    "brand_background_color": None,

    # Logo to use for your site, must be present in static files, used for brand on top left
    "site_logo": None,

    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    "login_logo": None,

    # Logo to use for login form in dark themes (defaults to login_logo)
    "login_logo_dark": None,

    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",

    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": None,

    # List of model admins to search from the search bar, search bar omitted if excluded
    "search_model": ["auth.User", "styler.Style"],

    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,
}

# Jazzmin UI Tweaks for better appearance
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-light-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    "actions_sticky_top": True
}
# =================== JAZZMIN CONFIGURATION - END ===================