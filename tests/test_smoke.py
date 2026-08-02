from django.conf import settings


def test_settings_load():
    assert settings.INSTALLED_APPS
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"


def test_wal_mode_configured():
    assert "WAL" in settings.DATABASES["default"]["OPTIONS"]["init_command"]
