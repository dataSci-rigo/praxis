from django.db import models


class Ping(models.Model):
    PENDING = "PENDING"
    SENT = "SENT"
    ANSWERED = "ANSWERED"
    EXPIRED = "EXPIRED"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (SENT, "Sent"),
        (ANSWERED, "Answered"),
        (EXPIRED, "Expired"),
    ]

    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_for"]

    def __str__(self) -> str:
        return f"Ping {self.scheduled_for:%Y-%m-%d %H:%M} ({self.status})"


class PingResponse(models.Model):
    ping = models.OneToOneField(Ping, on_delete=models.CASCADE, related_name="response")
    activity = models.CharField(max_length=200)
    challenge = models.PositiveSmallIntegerField()
    skill = models.PositiveSmallIntegerField()
    absorption = models.PositiveSmallIntegerField()
    mood = models.PositiveSmallIntegerField()
    wish_doing_else = models.BooleanField()
    autotelic = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Response to {self.ping} — {self.activity}"
