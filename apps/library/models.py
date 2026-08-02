from django.db import models


class BookCard(models.Model):
    MINDSET = "MINDSET"
    FLOW = "FLOW"
    GRIT = "GRIT"
    BOOK_CHOICES = [(MINDSET, "Mindset"), (FLOW, "Flow"), (GRIT, "Grit")]

    book = models.CharField(max_length=7, choices=BOOK_CHOICES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    times_shown = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["book", "title"]

    def __str__(self) -> str:
        return f"[{self.book}] {self.title}"
