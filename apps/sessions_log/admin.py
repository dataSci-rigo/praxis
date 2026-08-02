from django.contrib import admin

from apps.sessions_log.models import Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["kind", "goal", "started_at", "duration_min"]
    list_filter = ["kind", "goal__domain"]
    date_hierarchy = "started_at"
