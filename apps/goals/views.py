from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.views.generic.base import TemplateView

from apps.goals.forms import GoalForm
from apps.goals.models import Goal
from apps.goals.services import build_goal_tree, orphan_sessions


class GoalTreeView(LoginRequiredMixin, TemplateView):
    template_name = "goals/tree.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "domains": build_goal_tree(),
            "orphans": orphan_sessions(),
        }


class GoalCreateView(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = "goals/goal_form.html"
    success_url = reverse_lazy("goal-tree")


class GoalUpdateView(LoginRequiredMixin, UpdateView):
    model = Goal
    form_class = GoalForm
    template_name = "goals/goal_form.html"
    success_url = reverse_lazy("goal-tree")
