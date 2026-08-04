from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR.parent  # ~/Documents, holds the master .env

env = environ.Env()
# Master .env first (shared secrets across ~/Documents projects), then this
# project's own .env overrides — mirrors the pattern used by wp_instinct/bot/config.py.
environ.Env.read_env(DOCS_DIR / ".env")
environ.Env.read_env(BASE_DIR / ".env", overwrite=True)

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-insecure-key")
DEBUG = env.bool("DJANGO_DEBUG", default=True)
# "*" is fine here: the VM only accepts inbound traffic over Tailscale (see
# server/vm_setup.sh's nginx block + firewall), so there's no public Host-header
# spoofing surface. Override with a comma-separated DJANGO_ALLOWED_HOSTS if that changes.
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_OWNER_ID = int(env("TELEGRAM_OWNER_ID", default="0") or 0)
ESM_PINGS_PER_DAY = env.int("ESM_PINGS_PER_DAY", default=3)
ESM_WINDOW = env("ESM_WINDOW", default="09:00-21:00")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.goals",
    "apps.sessions_log",
    "apps.journal",
    "apps.esm",
    "apps.assessments",
    "apps.insights",
    "apps.bot",
    "apps.library",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "praxis.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "praxis.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        # WAL mode lets the web process and the bot process read/write concurrently.
        "OPTIONS": {"init_command": "PRAGMA journal_mode=WAL;"},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="America/Los_Angeles")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

# Single-user site: reuse the admin login form instead of building a second one.
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
