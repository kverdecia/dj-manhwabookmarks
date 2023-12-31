# Generated by Django 4.2.5 on 2023-11-12 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("djmanhwabookmarks", "0005_manhwabookmark_priority_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="manhwabookmark",
            options={
                "ordering": ("-priority", "-updated_at"),
                "verbose_name": "Manhwa bookmark",
                "verbose_name_plural": "Manhwa bookmarks",
            },
        ),
        migrations.AddField(
            model_name="manhwabookmark",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated at"),
        ),
    ]
