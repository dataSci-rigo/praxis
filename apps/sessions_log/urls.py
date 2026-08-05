from django.urls import path

from apps.sessions_log import views

urlpatterns = [
    path("", views.SessionListView.as_view(), name="session-list"),
    path("<int:pk>/edit/", views.SessionUpdateView.as_view(), name="session-edit"),
]
