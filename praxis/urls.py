from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    # "", dashboard view — added in Phase 2 (insights).
]
