from django.contrib import admin

from apps.goals.models import Goal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ["title", "level", "domain", "parent", "status", "target_date", "is_demo"]
    list_filter = ["level", "domain", "status", "is_demo"]
    search_fields = ["title", "description"]
