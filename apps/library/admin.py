from django.contrib import admin

from apps.library.models import BookCard


@admin.register(BookCard)
class BookCardAdmin(admin.ModelAdmin):
    list_display = ["book", "title", "times_shown"]
    list_filter = ["book"]
