from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView

from apps.journal.forms import EntryForm
from apps.journal.models import Entry


class EntryListView(LoginRequiredMixin, ListView):
    model = Entry
    template_name = "journal/list.html"
    context_object_name = "entries"
    paginate_by = 50
    queryset = Entry.objects.select_related("goal").order_by("-created_at")


class EntryUpdateView(LoginRequiredMixin, UpdateView):
    model = Entry
    form_class = EntryForm
    template_name = "journal/entry_form.html"
    success_url = reverse_lazy("journal-list")
