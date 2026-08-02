from django.core.exceptions import ValidationError
from django.db import models

from apps.goals.models import Goal


class Session(models.Model):
    DELIBERATE_PRACTICE = "DP"
    FLOW_PERFORMANCE = "FLOW"
    LEARNING = "LEARN"
    KIND_CHOICES = [
        (DELIBERATE_PRACTICE, "Deliberate practice"),
        (FLOW_PERFORMANCE, "Flow / performance"),
        (LEARNING, "Learning"),
    ]

    kind = models.CharField(max_length=5, choices=KIND_CHOICES)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="sessions")
    started_at = models.DateTimeField()
    duration_min = models.PositiveIntegerField()

    # Deliberate-practice-only fields — null unless kind=DP.
    stretch_goal = models.TextField(blank=True, default="")
    feedback_received = models.TextField(blank=True, default="")
    refinement = models.TextField(blank=True, default="")
    discomfort = models.PositiveSmallIntegerField(null=True, blank=True)

    # Flow-only fields — null unless kind=FLOW_PERFORMANCE.
    challenge = models.PositiveSmallIntegerField(null=True, blank=True)
    skill = models.PositiveSmallIntegerField(null=True, blank=True)
    absorption = models.PositiveSmallIntegerField(null=True, blank=True)
    enjoyment = models.PositiveSmallIntegerField(null=True, blank=True)
    had_clear_goal = models.BooleanField(null=True, blank=True)
    had_immediate_feedback = models.BooleanField(null=True, blank=True)

    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    _DP_FIELDS = ["stretch_goal", "feedback_received", "refinement", "discomfort"]
    _FLOW_FIELDS = [
        "challenge",
        "skill",
        "absorption",
        "enjoyment",
        "had_clear_goal",
        "had_immediate_feedback",
    ]

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.kind} — {self.goal.title} ({self.started_at:%Y-%m-%d})"

    def _field_is_set(self, name: str) -> bool:
        value = getattr(self, name)
        return bool(value) if isinstance(value, str) else value is not None

    def clean(self) -> None:
        if self.goal_id and self.goal.level not in (Goal.MID, Goal.LOW):
            raise ValidationError("Sessions must link to a MID or LOW goal.")

        forbidden = []
        if self.kind != self.DELIBERATE_PRACTICE:
            forbidden += [f for f in self._DP_FIELDS if self._field_is_set(f)]
        if self.kind != self.FLOW_PERFORMANCE:
            forbidden += [f for f in self._FLOW_FIELDS if self._field_is_set(f)]
        if forbidden:
            raise ValidationError(
                f"{', '.join(forbidden)}: field(s) not valid for a {self.kind} session."
            )
