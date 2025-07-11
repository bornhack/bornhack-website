# Generated by Django 4.2.21 on 2025-07-07 13:37
from __future__ import annotations

from django.db import migrations

CATEGORIES = {
    "Unknown": "Unknown category for unrecognized token hints/categories",
    "Roads": "Auto created, make a new description",
    "Website": "Auto created, make a new description",
    "Physical": "Auto created, make a new description",
    "Ether": "Auto created, make a new description",
    "DNS": "Auto created, make a new description",
    "Internet": "Auto created, make a new description",
    "Git": "Auto created, make a new description",
    "Invisible": "Auto created, make a new description",
    "Web": "Auto created, make a new description",
    "Phone": "Auto created, make a new description",
    "Electrical": "Auto created, make a new description",
    "Aural": "Auto created, make a new description",
    "Virtual": "Auto created, make a new description",
    "ASN": "Auto created, make a new description",
    "Visual": "Auto created, make a new description",
    "Network": "Auto created, make a new description",
    "IRC": "Auto created, make a new description",
    "Audio": "Auto created, make a new description",
    "Minecraft": "Auto created, make a new description",
    "Lights": "Auto created, make a new description",
    "Badge": "Auto created, make a new description",
    "Video": "Auto created, make a new description",
    "Talk": "Auto created, make a new description",
    "SSH": "Auto created, make a new description",
}


def create_and_populate_category_fk_for_tokens(apps, schema_editor):
    """
    Create categories and check if a hint contains a match with
    a token category, the category FK gets added to the token.
    """
    Token = apps.get_model("tokens", "Token")
    Category = apps.get_model("tokens", "TokenCategory")

    created_categories = {}
    for key, value in CATEGORIES.items():
        defaults = {"description": value}
        category, _ = Category.objects.get_or_create(name=key, defaults=defaults)
        created_categories[key.lower()] = category

    for token in Token.objects.all():
        if not token.hint:
            token.category = created_categories["unknown"]
            token.save()
            continue

        for word in token.hint.split(" "):
            word = word.replace(",", "").replace(".", "").strip()
            if word.lower() in created_categories:
                token.category = created_categories[word.lower()]
                break
            token.category = created_categories["unknown"]

        token.save()


class Migration(migrations.Migration):
    dependencies = [
        ("tokens", "0013_alter_tokencategory_options_tokencategory_created_and_more"),
    ]

    operations = [
        migrations.RunPython(create_and_populate_category_fk_for_tokens),
    ]
