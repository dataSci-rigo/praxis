from django.urls import path

from apps.insights import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("insights/", views.insights, name="insights"),
]
