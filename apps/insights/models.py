from django.db import models


class WeeklyReview(models.Model):
    week_start = models.DateField(unique=True)
    what_worked = models.TextField(blank=True, default="")
    what_to_change = models.TextField(blank=True, default="")
    next_stretch_goal = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-week_start"]

    def __str__(self) -> str:
        return f"Weekly review — {self.week_start}"
