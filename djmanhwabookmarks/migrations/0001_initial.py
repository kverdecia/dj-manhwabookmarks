# Generated by Django 4.2.5 on 2023-09-05 00:38

from django.db import migrations, models
import djmanhwabookmarks.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ManhwaBookmark",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, unique=True, verbose_name="Name"),
                ),
                (
                    "url",
                    models.URLField(
                        blank=True,
                        editable=False,
                        null=True,
                        unique=True,
                        verbose_name="Url",
                    ),
                ),
                (
                    "url_selector",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        validators=[
                            djmanhwabookmarks.validators.validate_selector_syntax
                        ],
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        blank=True, editable=False, max_length=255, verbose_name="Title"
                    ),
                ),
                (
                    "title_selector",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        validators=[
                            djmanhwabookmarks.validators.validate_selector_syntax
                        ],
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, editable=False, verbose_name="Description"
                    ),
                ),
                (
                    "description_selector",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        validators=[
                            djmanhwabookmarks.validators.validate_selector_syntax
                        ],
                    ),
                ),
                (
                    "chapter_url",
                    models.URLField(unique=True, verbose_name="Chapter url"),
                ),
                (
                    "chapter_number",
                    models.PositiveIntegerField(
                        blank=True,
                        editable=False,
                        null=True,
                        verbose_name="Chapter number",
                    ),
                ),
                (
                    "chapter_number_selector",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        validators=[
                            djmanhwabookmarks.validators.validate_selector_syntax
                        ],
                    ),
                ),
                (
                    "chapter_number_regex",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        validators=[djmanhwabookmarks.validators.validate_regex_syntax],
                    ),
                ),
                (
                    "next_chapter_url",
                    models.URLField(
                        blank=True,
                        editable=False,
                        null=True,
                        unique=True,
                        verbose_name="Next chapter url",
                    ),
                ),
                (
                    "next_chapter_url_selector",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        validators=[
                            djmanhwabookmarks.validators.validate_selector_syntax
                        ],
                    ),
                ),
                (
                    "next_chapter_opened",
                    models.BooleanField(
                        default=False, verbose_name="Next chapter opened"
                    ),
                ),
            ],
            options={
                "verbose_name": "Manhwa bookmark",
                "verbose_name_plural": "Manhwa bookmarks",
            },
        ),
    ]
