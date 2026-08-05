from django.urls import path

from apps.goals import views

urlpatterns = [
    path("", views.GoalTreeView.as_view(), name="goal-tree"),
    path("add/", views.GoalCreateView.as_view(), name="goal-add"),
    path("<int:pk>/edit/", views.GoalUpdateView.as_view(), name="goal-edit"),
]
