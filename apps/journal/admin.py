from django.contrib import admin

from apps.journal.models import Entry


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ["kind", "goal", "fixed_score", "growth_score", "created_at"]
    list_filter = ["kind"]
    readonly_fields = ["fixed_score", "growth_score"]
    search_fields = ["body", "reframe"]
