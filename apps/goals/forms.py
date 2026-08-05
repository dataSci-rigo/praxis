from django import forms

from apps.goals.models import Goal


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ["title", "level", "parent", "domain", "description", "status", "target_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "target_date": forms.DateInput(attrs={"type": "date"}),
        }
