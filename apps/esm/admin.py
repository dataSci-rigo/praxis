from django.contrib import admin

from apps.esm.models import Ping, PingResponse


@admin.register(Ping)
class PingAdmin(admin.ModelAdmin):
    list_display = ["scheduled_for", "sent_at", "status", "is_demo"]
    list_filter = ["status", "is_demo"]


@admin.register(PingResponse)
class PingResponseAdmin(admin.ModelAdmin):
    list_display = ["ping", "activity", "challenge", "skill", "absorption", "mood", "autotelic"]
