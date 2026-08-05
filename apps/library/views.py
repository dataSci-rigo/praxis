from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.library.forms import BookCardForm
from apps.library.models import BookCard


class BookCardListView(LoginRequiredMixin, ListView):
    model = BookCard
    template_name = "library/list.html"
    context_object_name = "cards"


class BookCardCreateView(LoginRequiredMixin, CreateView):
    model = BookCard
    form_class = BookCardForm
    template_name = "library/bookcard_form.html"
    success_url = reverse_lazy("bookcard-list")


class BookCardUpdateView(LoginRequiredMixin, UpdateView):
    model = BookCard
    form_class = BookCardForm
    template_name = "library/bookcard_form.html"
    success_url = reverse_lazy("bookcard-list")


class BookCardDeleteView(LoginRequiredMixin, DeleteView):
    model = BookCard
    template_name = "library/bookcard_confirm_delete.html"
    success_url = reverse_lazy("bookcard-list")
