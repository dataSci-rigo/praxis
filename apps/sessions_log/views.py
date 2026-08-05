from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView

from apps.goals.models import Goal
from apps.sessions_log.forms import SessionForm
from apps.sessions_log.models import Session


class SessionListView(LoginRequiredMixin, ListView):
    model = Session
    template_name = "sessions_log/list.html"
    context_object_name = "sessions"
    paginate_by = 50

    def get_queryset(self):
        qs = Session.objects.select_related("goal").order_by("-started_at")
        kind = self.request.GET.get("kind")
        goal_id = self.request.GET.get("goal")
        date_from = self.request.GET.get("from")
        date_to = self.request.GET.get("to")
        if kind:
            qs = qs.filter(kind=kind)
        if goal_id:
            qs = qs.filter(goal_id=goal_id)
        if date_from:
            qs = qs.filter(started_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(started_at__date__lte=date_to)
        return qs

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "kind_choices": Session.KIND_CHOICES,
            "goals": Goal.objects.order_by("domain", "title"),
            "selected_kind": self.request.GET.get("kind", ""),
            "selected_goal": self.request.GET.get("goal", ""),
            "date_from": self.request.GET.get("from", ""),
            "date_to": self.request.GET.get("to", ""),
        }


class SessionUpdateView(LoginRequiredMixin, UpdateView):
    model = Session
    form_class = SessionForm
    template_name = "sessions_log/session_form.html"
    success_url = reverse_lazy("session-list")
