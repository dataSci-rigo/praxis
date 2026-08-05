from django import forms

from apps.library.models import BookCard


class BookCardForm(forms.ModelForm):
    class Meta:
        model = BookCard
        fields = ["book", "title", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 4})}
