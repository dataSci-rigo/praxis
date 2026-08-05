from django.urls import path

from apps.library import views

urlpatterns = [
    path("", views.BookCardListView.as_view(), name="bookcard-list"),
    path("add/", views.BookCardCreateView.as_view(), name="bookcard-add"),
    path("<int:pk>/edit/", views.BookCardUpdateView.as_view(), name="bookcard-edit"),
    path("<int:pk>/delete/", views.BookCardDeleteView.as_view(), name="bookcard-delete"),
]
