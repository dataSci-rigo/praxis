from django.core.exceptions import ValidationError
from django.db import models


class Goal(models.Model):
    TOP = "TOP"
    MID = "MID"
    LOW = "LOW"
    LEVEL_CHOICES = [(TOP, "Top-level"), (MID, "Mid-level"), (LOW, "Low-level")]

    ACTIVE = "ACTIVE"
    ACHIEVED = "ACHIEVED"
    DROPPED = "DROPPED"
    STATUS_CHOICES = [(ACTIVE, "Active"), (ACHIEVED, "Achieved"), (DROPPED, "Dropped")]

    title = models.CharField(max_length=200)
    level = models.CharField(max_length=3, choices=LEVEL_CHOICES)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    domain = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=ACTIVE)
    target_date = models.DateField(null=True, blank=True)
    is_demo = models.BooleanField(
        default=False, help_text="Seeded by `make seed`; removable via `make unseed`."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["domain", "level", "title"]

    def __str__(self) -> str:
        return f"[{self.level}] {self.title}"

    def clean(self) -> None:
        if self.level == self.TOP and self.parent is not None:
            raise ValidationError("A TOP-level goal cannot have a parent.")
        if self.level in (self.MID, self.LOW) and self.parent is None:
            raise ValidationError(f"A {self.level}-level goal requires a parent.")
        if self.level == self.MID and self.parent is not None and self.parent.level != self.TOP:
            raise ValidationError("A MID-level goal's parent must be a TOP-level goal.")
        if self.level == self.LOW and self.parent is not None and self.parent.level != self.MID:
            raise ValidationError("A LOW-level goal's parent must be a MID-level goal.")
