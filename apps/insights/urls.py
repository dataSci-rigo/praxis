from django.urls import path

from apps.insights import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("insights/", views.insights, name="insights"),
    path("review/", views.review, name="review"),
    path("digest/", views.digest, name="digest"),
    path("export/", views.export_index, name="export-index"),
    path("export/<str:model_name>.csv", views.export_csv, name="export-csv"),
]
