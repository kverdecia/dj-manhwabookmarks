# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _
from django.db import models

from . import validators


class ManhwaBookmark(models.Model):
    name = models.CharField(_("Name"), max_length=255, unique=True)

    url = models.URLField(_("Url"), blank=True, null=True, unique=True, editable=False)
    url_selector = models.CharField(max_length=255, blank=True,
        validators=[validators.validate_selector_syntax])

    title = models.CharField(_("Title"), max_length=255, blank=True, editable=False)
    title_selector = models.CharField(max_length=255, blank=True,
        validators=[validators.validate_selector_syntax])

    description = models.TextField(_("Description"), blank=True, editable=False)
    description_selector = models.CharField(max_length=255, blank=True,
        validators=[validators.validate_selector_syntax])

    chapter_url = models.URLField(_("Chapter url"), unique=True)
    chapter_number = models.PositiveIntegerField(_("Chapter number"), blank=True, null=True, editable=False)
    chapter_number_selector = models.CharField(max_length=255, blank=True,
        validators=[validators.validate_selector_syntax])
    chapter_number_regex = models.CharField(max_length=255, blank=True,
        validators=[validators.validate_regex_syntax])

    next_chapter_url = models.URLField(_("Next chapter url"), blank=True, null=True, unique=True, editable=False)
    next_chapter_url_selector = models.CharField(max_length=255, blank=True,
        validators=[validators.validate_selector_syntax])
    next_chapter_opened = models.BooleanField(_("Next chapter opened"), default=False)

    class Meta:
        verbose_name = _("Manhwa bookmark")
        verbose_name_plural = _("Manhwa bookmarks")

    def __str__(self):
        return self.title or self.name
