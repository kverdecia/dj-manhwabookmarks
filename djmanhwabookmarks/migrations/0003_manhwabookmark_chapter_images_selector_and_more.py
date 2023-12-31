# Generated by Django 4.2.5 on 2023-09-22 08:46

from django.db import migrations, models
import djmanhwabookmarks.validators


class Migration(migrations.Migration):

    dependencies = [
        ("djmanhwabookmarks", "0002_manhwabookmark_is_template"),
    ]

    operations = [
        migrations.AddField(
            model_name="manhwabookmark",
            name="chapter_images_selector",
            field=models.CharField(
                blank=True,
                max_length=255,
                validators=[djmanhwabookmarks.validators.validate_selector_syntax],
            ),
        ),
        migrations.AlterField(
            model_name="manhwabookmark",
            name="chapter_number",
            field=models.FloatField(
                blank=True, editable=False, null=True, verbose_name="Chapter number"
            ),
        ),
    ]
