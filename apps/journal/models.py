from django.core.exceptions import ValidationError
from django.db import models

from apps.goals.models import Goal
from apps.journal.mindset_lang import score_text


class Entry(models.Model):
    JOURNAL = "JOURNAL"
    SETBACK = "SETBACK"
    KIND_CHOICES = [(JOURNAL, "Journal"), (SETBACK, "Setback")]

    kind = models.CharField(max_length=7, choices=KIND_CHOICES)
    body = models.TextField()
    reframe = models.TextField(blank=True, default="")
    goal = models.ForeignKey(
        Goal, null=True, blank=True, on_delete=models.SET_NULL, related_name="journal_entries"
    )
    fixed_score = models.PositiveIntegerField(default=0, editable=False)
    growth_score = models.PositiveIntegerField(default=0, editable=False)
    is_demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "entries"

    def __str__(self) -> str:
        return f"{self.kind} ({self.created_at:%Y-%m-%d})"

    @property
    def growth_ratio(self) -> float | None:
        total = self.fixed_score + self.growth_score
        return (self.growth_score / total) if total else None

    def clean(self) -> None:
        if self.kind == self.SETBACK and not self.reframe:
            raise ValidationError("A setback entry requires a growth reframe.")

    def save(self, *args, **kwargs) -> None:
        self.fixed_score, self.growth_score = score_text(self.body)
        super().save(*args, **kwargs)
