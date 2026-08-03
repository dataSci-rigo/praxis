from django.db import migrations

CARDS = [
    {
        "book": "MINDSET",
        "title": "Not yet",
        "body": (
            "When a setback lands, add three words before you judge it: 'not yet'. "
            "'I can't do this — not yet' turns a verdict about who you are into a "
            "status update on where you are."
        ),
    },
    {
        "book": "FLOW",
        "title": "Stretch the goal, not the anxiety",
        "body": (
            "Flow lives right where challenge and skill are both high and roughly "
            "matched. If a task feels flat, raise the challenge a notch. If it feels "
            "like drowning, build the skill before you raise it again."
        ),
    },
    {
        "book": "GRIT",
        "title": "Suffer in practice, lose yourself in performance",
        "body": (
            "Deliberate practice is supposed to be uncomfortable — it's aimed at your "
            "weak spot on purpose. Save the effortless immersion for when you perform. "
            "Mixing the two up is how people end up doing neither well."
        ),
    },
]


def add_cards(apps, schema_editor):
    BookCard = apps.get_model("library", "BookCard")
    for card in CARDS:
        BookCard.objects.get_or_create(title=card["title"], defaults=card)


def remove_cards(apps, schema_editor):
    BookCard = apps.get_model("library", "BookCard")
    BookCard.objects.filter(title__in=[c["title"] for c in CARDS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_cards, remove_cards),
    ]
