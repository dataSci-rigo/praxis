from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.insights.urls")),
    path("goals/", include("apps.goals.urls")),
    path("sessions/", include("apps.sessions_log.urls")),
    path("journal/", include("apps.journal.urls")),
    path("library/", include("apps.library.urls")),
]
