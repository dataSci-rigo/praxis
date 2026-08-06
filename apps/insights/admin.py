from django.contrib import admin

from apps.insights.models import WeeklyReview


@admin.register(WeeklyReview)
class WeeklyReviewAdmin(admin.ModelAdmin):
    list_display = ["week_start", "created_at", "updated_at"]
