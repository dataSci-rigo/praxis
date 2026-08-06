from django import forms

from apps.insights.models import WeeklyReview


class WeeklyReviewForm(forms.ModelForm):
    class Meta:
        model = WeeklyReview
        fields = ["what_worked", "what_to_change", "next_stretch_goal"]
        widgets = {
            "what_worked": forms.Textarea(attrs={"rows": 3}),
            "what_to_change": forms.Textarea(attrs={"rows": 3}),
            "next_stretch_goal": forms.Textarea(attrs={"rows": 2}),
        }
