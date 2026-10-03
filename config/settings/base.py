from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="redux-dev-secret-key-change-in-production")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost,testserver", cast=Csv())

PLATFORM_NAME = config("PLATFORM_NAME", default="REDUX")
ADMIN_URL_PATH = config("ADMIN_URL_PATH", default="cpanel-redux")
DEFAULT_COUNTRY_CODE = config("DEFAULT_COUNTRY_CODE", default="BJ")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",

    # Tiers
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "django_filters",
    "storages",

    # Apps Redux
    "apps.core",
    "apps.countries",
    "apps.accounts",
    "apps.merchants",
    "apps.stores",
    "apps.catalog",
    "apps.pricing",
    "apps.campaigns",
    "apps.orders",
    "apps.payments",
    "apps.deliveries",
    "apps.purchase_requests",
    "apps.reviews",
    "apps.disputes",
    "apps.notifications",
    "apps.commissions",
    "apps.pages",
    "apps.api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.countries.middleware.CountryMiddleware",
]

ROOT_URLCONF = "config.urls"

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailOrPhoneBackend",
]

LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/dashboard"
LOGOUT_REDIRECT_URL = "/"

import sys

IS_TESTING = "test" in sys.argv or any("pytest" in arg for arg in sys.argv) or "pytest" in sys.modules

DATABASE_URL = config("DATABASE_URL", default="").strip()
DB_ENGINE = config("DB_ENGINE", default="sqlite")

if IS_TESTING:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
elif DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True if ("supabase" in DATABASE_URL or "sslmode=require" in DATABASE_URL) else False,
        )
    }
elif DB_ENGINE in ("postgres", "postgresql"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("POSTGRES_DB", default=config("PGDATABASE", default="postgres")),
            "USER": config("POSTGRES_USER", default=config("PGUSER", default="postgres")),
            "PASSWORD": config("POSTGRES_PASSWORD", default=config("PGPASSWORD", default="")),
            "HOST": config("POSTGRES_HOST", default=config("PGHOST", default="localhost")),
            "PORT": config("POSTGRES_PORT", default=config("PGPORT", default="5432")),
            "CONN_MAX_AGE": 600,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                "sslmode": config("POSTGRES_SSLMODE", default="require"),
            },
        }
    }
elif DB_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": config("MYSQL_DATABASE", default="redux"),
            "USER": config("MYSQL_USER", default="root"),
            "PASSWORD": config("MYSQL_PASSWORD", default=""),
            "HOST": config("MYSQL_HOST", default="127.0.0.1"),
            "PORT": config("MYSQL_PORT", default="3306"),
            "OPTIONS": {"charset": "utf8mb4"},
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.platform",
                "apps.countries.context_processors.country",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

LANGUAGE_CODE = "fr"
LANGUAGES = [("fr", "Français"), ("en", "English")]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
USE_TZ = True
TIME_ZONE = "UTC"

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ==============================================================================
# MEDIA & STOCKAGE CLOUD (SUPABASE STORAGE S3)
# ==============================================================================
USE_SUPABASE_STORAGE = config("USE_SUPABASE_STORAGE", default=False, cast=bool)
SUPABASE_STORAGE_BUCKET = config("SUPABASE_STORAGE_BUCKET", default="redux-media")
SUPABASE_PROJECT_REF = config("SUPABASE_PROJECT_REF", default="wztfqyeegftiazuxbgod")
SUPABASE_URL = config("SUPABASE_URL", default=f"https://{SUPABASE_PROJECT_REF}.supabase.co")

if USE_SUPABASE_STORAGE and not IS_TESTING:
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
    AWS_STORAGE_BUCKET_NAME = SUPABASE_STORAGE_BUCKET
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="eu-central-1")
    AWS_S3_ENDPOINT_URL = config(
        "AWS_S3_ENDPOINT_URL",
        default=f"https://{SUPABASE_PROJECT_REF}.supabase.co/storage/v1/s3"
    )
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_SIGNATURE_VERSION = "s3v4"

    # URL publique directe pour servir les médias via le CDN Supabase
    supabase_custom_domain = config(
        "AWS_S3_CUSTOM_DOMAIN",
        default=f"{SUPABASE_PROJECT_REF}.supabase.co/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}"
    )
    if supabase_custom_domain:
        AWS_S3_CUSTOM_DOMAIN = supabase_custom_domain
        MEDIA_URL = f"https://{supabase_custom_domain}/"
    else:
        MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{SUPABASE_STORAGE_BUCKET}/"

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    MEDIA_URL = "media/"
    MEDIA_ROOT = BASE_DIR / "media"
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "240/min"},
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/0"),
    }
}

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/1")
CELERY_TASK_ALWAYS_EAGER = False
