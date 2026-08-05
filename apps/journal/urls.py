from django.urls import path

from apps.journal import views

urlpatterns = [
    path("", views.EntryListView.as_view(), name="journal-list"),
    path("<int:pk>/edit/", views.EntryUpdateView.as_view(), name="journal-edit"),
]
