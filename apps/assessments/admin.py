from django.contrib import admin

from apps.assessments.models import Assessment, ItemResponse, ScaleItem


@admin.register(ScaleItem)
class ScaleItemAdmin(admin.ModelAdmin):
    list_display = ["kind", "number", "reverse_scored", "text"]
    list_filter = ["kind", "reverse_scored"]


class ItemResponseInline(admin.TabularInline):
    model = ItemResponse
    extra = 0


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ["kind", "taken_at", "total_score", "is_demo"]
    list_filter = ["kind", "is_demo"]
    inlines = [ItemResponseInline]
