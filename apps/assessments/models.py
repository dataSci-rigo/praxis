from django.db import models


class ScaleItem(models.Model):
    GRIT = "GRIT"
    MINDSET = "MINDSET"
    KIND_CHOICES = [(GRIT, "Grit Scale"), (MINDSET, "Mindset Assessment")]

    kind = models.CharField(max_length=7, choices=KIND_CHOICES)
    number = models.PositiveSmallIntegerField()
    text = models.TextField()
    reverse_scored = models.BooleanField(default=False)

    class Meta:
        ordering = ["kind", "number"]
        unique_together = [("kind", "number")]

    def __str__(self) -> str:
        return f"{self.kind} #{self.number}"


class Assessment(models.Model):
    GRIT = ScaleItem.GRIT
    MINDSET = ScaleItem.MINDSET
    KIND_CHOICES = ScaleItem.KIND_CHOICES

    kind = models.CharField(max_length=7, choices=KIND_CHOICES)
    taken_at = models.DateTimeField()
    total_score = models.FloatField()
    subscale_json = models.JSONField(default=dict, blank=True)
    is_demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-taken_at"]

    def __str__(self) -> str:
        return f"{self.kind} — {self.taken_at:%Y-%m-%d} ({self.total_score})"


class ItemResponse(models.Model):
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="item_responses"
    )
    item_number = models.PositiveSmallIntegerField()
    value = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["item_number"]

    def __str__(self) -> str:
        return f"{self.assessment}: item {self.item_number} = {self.value}"
