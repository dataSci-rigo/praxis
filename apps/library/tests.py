from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.library.models import BookCard


class BookCardCRUDTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pw")

    def test_list_requires_login(self):
        self.assertEqual(self.client.get(reverse("bookcard-list")).status_code, 302)

    def test_add_card(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("bookcard-add"),
            {"book": BookCard.GRIT, "title": "Not yet", "body": "A short paraphrase."},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BookCard.objects.filter(title="Not yet").exists())

    def test_edit_card(self):
        self.client.force_login(self.user)
        card = BookCard.objects.create(book=BookCard.FLOW, title="Old", body="old body")
        response = self.client.post(
            reverse("bookcard-edit", args=[card.pk]),
            {"book": BookCard.FLOW, "title": "New", "body": "new body"},
        )
        self.assertEqual(response.status_code, 302)
        card.refresh_from_db()
        self.assertEqual(card.title, "New")

    def test_delete_card(self):
        self.client.force_login(self.user)
        card = BookCard.objects.create(book=BookCard.MINDSET, title="Gone soon", body="x")
        response = self.client.post(reverse("bookcard-delete", args=[card.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(BookCard.objects.filter(pk=card.pk).exists())
