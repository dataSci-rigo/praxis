from django import forms

from apps.journal.models import Entry


class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ["kind", "body", "reframe", "goal"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4}),
            "reframe": forms.Textarea(attrs={"rows": 3}),
        }
