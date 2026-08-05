from django import forms

from apps.sessions_log.models import Session


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            "kind",
            "goal",
            "started_at",
            "duration_min",
            "stretch_goal",
            "feedback_received",
            "refinement",
            "discomfort",
            "challenge",
            "skill",
            "absorption",
            "enjoyment",
            "had_clear_goal",
            "had_immediate_feedback",
            "notes",
        ]
        widgets = {
            "started_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "stretch_goal": forms.Textarea(attrs={"rows": 2}),
            "feedback_received": forms.Textarea(attrs={"rows": 2}),
            "refinement": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
