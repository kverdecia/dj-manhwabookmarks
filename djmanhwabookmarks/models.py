# -*- coding: utf-8 -*-
from typing import Optional
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.utils.translation import gettext_lazy as _
from django.db import models

from . import extractors


class ManhwaBookmarkQueryset(models.QuerySet['ManhwaBookmark']):
    def update_bookmarks(self) -> None:
        # process only bookmarks with no next chapter url
        queryset = self.filter(next_chapter_url__isnull=True)
        count = queryset.count()
        with ThreadPoolExecutor(10) as executor:
            futures = (executor.submit(bookmark.update_bookmark) for bookmark in queryset)
            for pos, future in enumerate(as_completed(futures)):  # noqa: B007
                print(f'{pos + 1}/{count}')


class ManhwaBookmarkManager(models.Manager):
    def get_queryset(self):
        return ManhwaBookmarkQueryset(self.model, using=self._db)

    def update_bookmarks(self):
        return self.get_queryset().update_bookmarks()


class ExtractorType(models.TextChoices):
    MECHANICAL_SOUP = 'mechanical_soup', _("MechanicalSoup")


EXTRACTOR_TYPES = {
    ExtractorType.MECHANICAL_SOUP: extractors.MechanicalSoupExtractor,
}


class ManhwaBookmark(models.Model):
    objects = ManhwaBookmarkManager()

    extractor_type = models.CharField(_("Extractor type"), max_length=100, choices=ExtractorType.choices,
        default=ExtractorType.MECHANICAL_SOUP)

    name = models.CharField(_("Name"), max_length=255, unique=True)

    url = models.URLField(_("Url"), max_length=1000, blank=True, null=True, unique=True, editable=False)
    url_selector = models.CharField(max_length=255, blank=True)

    title = models.CharField(_("Title"), max_length=255, blank=True, editable=False)
    title_selector = models.CharField(max_length=255, blank=True)

    description = models.TextField(_("Description"), blank=True, editable=False)
    description_selector = models.CharField(max_length=255, blank=True)

    chapter_url = models.URLField(_("Chapter url"), max_length=1000, unique=True)
    chapter_number = models.FloatField(_("Chapter number"), blank=True, null=True, editable=False)
    chapter_number_selector = models.CharField(max_length=255, blank=True)
    chapter_number_regex = models.CharField(max_length=255, blank=True)

    next_chapter_url = models.URLField(_("Next chapter url"), max_length=1000, blank=True, null=True, unique=True, editable=False)
    next_chapter_url_selector = models.CharField(max_length=255, blank=True)
    next_chapter_opened = models.BooleanField(_("Next chapter opened"), default=False)

    chapter_images_selector = models.CharField(_("Chapter images selector"), max_length=255, blank=True)
    chapter_image_attribute = models.CharField(_("Chapter image attribute"), max_length=255, blank=True,
        default='src')

    is_template = models.BooleanField(_("Is template"), default=False)

    priority = models.PositiveIntegerField(_("Priority"), default=0, editable=False)
    priority_multiplier = models.PositiveIntegerField(_("Priority multiplier"), default=1)

    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Manhwa bookmark")
        verbose_name_plural = _("Manhwa bookmarks")
        ordering = ('-priority', '-updated_at')

    def __str__(self):
        return self.title or self.name

    def clean(self):
        extractor = self.get_extractor_instance()
        extractor.validate_params()

    def save(self, *args, **kwargs):
        if self.pk is None and not self.is_template:
            self.copy_template_fields_if_empty()
        self.priority = 0 if self.next_chapter_url is None else self.priority_multiplier
        super().save(*args, **kwargs)

    def copy_template_fields_if_empty(self):
        template = self.get_available_template()
        if template is not None:
            if not self.url_selector:
                self.url_selector = template.url_selector
            if not self.title_selector:
                self.title_selector = template.title_selector
            if not self.description_selector:
                self.description_selector = template.description_selector
            if not self.chapter_number_selector:
                self.chapter_number_selector = template.chapter_number_selector
            if not self.chapter_number_regex:
                self.chapter_number_regex = template.chapter_number_regex
            if not self.next_chapter_url_selector:
                self.next_chapter_url_selector = template.next_chapter_url_selector

    def get_available_template(self) -> Optional['ManhwaBookmark']:
        parse_result = urlparse(self.chapter_url)
        parse_result = parse_result._replace(path='', query='', fragment='', params='')
        template_url = parse_result.geturl()
        return ManhwaBookmark.objects.filter(chapter_url__startswith=template_url, is_template=True).first()

    def is_modified_for_update(self):
        if self.pk is None:
            return True
        old = ManhwaBookmark.objects.get(pk=self.pk)
        return (
            self.url != old.url or  # noqa: W504
            self.title != old.title or  # noqa: W504
            self.description != old.description or  # noqa: W504
            self.chapter_url != old.chapter_url or  # noqa: W504
            self.chapter_number != old.chapter_number or  # noqa: W504
            self.next_chapter_url != old.next_chapter_url  # noqa: W504
        )

    def get_extractor_class(self) -> type[extractors.Extractor]:
        return EXTRACTOR_TYPES[ExtractorType(self.extractor_type)]

    def get_extractor_instance(self) -> extractors.Extractor:
        extractor_class = self.get_extractor_class()
        params = extractors.ExtractorParams(
            chapter_url=self.chapter_url,
            chapter_number_selector=self.chapter_number_selector,
            chapter_number_regex=self.chapter_number_regex,
            next_chapter_url_selector=self.next_chapter_url_selector,
            url_selector=self.url_selector,
            title_selector=self.title_selector,
            description_selector=self.description_selector,
        )
        return extractor_class(params)

    def update_bookmark(self, save=True):
        extractor = self.get_extractor_instance()
        extractor_result = extractor()
        self.url = extractor_result.url
        self.title = extractor_result.title
        self.description = extractor_result.description
        self.chapter_number = extractor_result.chapter_number
        self.next_chapter_url = extractor_result.next_chapter_url
        can_modify = save and self.is_modified_for_update()
        print(f"Modifying bookmark {self.pk}:'{self.title or self.name}': {can_modify}")
        if can_modify:
            self.save()

    def mark_next_chapter_opened(self):
        if self.next_chapter_url:
            self.next_chapter_opened = True
            self.save()

    def change_to_next_chapter(self) -> None:
        if self.next_chapter_url:
            self.chapter_url = self.next_chapter_url
            self.next_chapter_url = None
            self.next_chapter_opened = False
            self.update_bookmark(save=False)
            self.save()
