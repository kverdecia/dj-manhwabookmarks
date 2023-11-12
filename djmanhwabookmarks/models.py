# -*- coding: utf-8 -*-
from typing import cast, Optional
import re
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.utils.translation import gettext_lazy as _
from django.db import models

import bs4
import mechanicalsoup

from . import validators


class ManhwaBookmarkQueryset(models.QuerySet['ManhwaBookmark']):
    def update_bookmarks(self) -> None:
        count = self.count()
        with ThreadPoolExecutor(10) as executor:
            futures = (executor.submit(bookmark.update_bookmark) for bookmark in self.all())
            for pos, future in enumerate(as_completed(futures)):  # noqa: B007
                print(f'{pos + 1}/{count}')


class ManhwaBookmarkManager(models.Manager):
    def get_queryset(self):
        return ManhwaBookmarkQueryset(self.model, using=self._db)

    def update_bookmarks(self):
        return self.get_queryset().update_bookmarks()


class ManhwaBookmark(models.Model):
    objects = ManhwaBookmarkManager()

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
    chapter_number = models.FloatField(_("Chapter number"), blank=True, null=True, editable=False)
    chapter_number_selector = models.CharField(max_length=255, blank=True,
        validators=[validators.validate_selector_syntax])
    chapter_number_regex = models.CharField(max_length=255, blank=True,
        validators=[validators.validate_regex_syntax])

    next_chapter_url = models.URLField(_("Next chapter url"), blank=True, null=True, unique=True, editable=False)
    next_chapter_url_selector = models.CharField(max_length=255, blank=True,
        validators=[validators.validate_selector_syntax])
    next_chapter_opened = models.BooleanField(_("Next chapter opened"), default=False)

    chapter_images_selector = models.CharField(_("Chapter images selector"), max_length=255, blank=True,
        validators=[validators.validate_selector_syntax])
    chapter_image_attribute = models.CharField(_("Chapter image attribute"), max_length=255, blank=True,
        default='src')

    is_template = models.BooleanField(_("Is template"), default=False)

    class Meta:
        verbose_name = _("Manhwa bookmark")
        verbose_name_plural = _("Manhwa bookmarks")

    def __str__(self):
        return self.title or self.name

    def save(self, *args, **kwargs):
        if self.pk is None and not self.is_template:
            self.copy_template_fields_if_empty()
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

    def update_bookmark(self, save=True):
        self.update_chapter()
        self.update_bookmark_url()
        self.update_main_page()
        if save:
            self.save()

    def open_chapter(self) -> mechanicalsoup.StatefulBrowser:
        browser = mechanicalsoup.StatefulBrowser()
        browser.open(self.chapter_url)
        return browser

    def open_main_page(self) -> mechanicalsoup.StatefulBrowser | None:
        if not self.url:
            return None
        browser = mechanicalsoup.StatefulBrowser()
        browser.open(self.url)
        return browser

    def _get_page(self, browser: mechanicalsoup.StatefulBrowser) -> bs4.BeautifulSoup:
        return cast(bs4.BeautifulSoup, browser.page)

    def _get_selector_tag(self, page: bs4.BeautifulSoup, selector: str | None) -> bs4.Tag | None:
        if not selector:
            return None
        tag = page.select_one(selector)
        if not tag:
            return None
        return tag

    def _get_selector_content(self, page: bs4.BeautifulSoup, selector: str) -> str | None:
        tag = self._get_selector_tag(page, selector)
        if not tag:
            return None
        return tag.get_text().strip()

    def _get_selector_link(self, page: bs4.BeautifulSoup, selector: str) -> str | None:
        def absolute_url(url: str) -> str:
            if url.startswith('/'):
                return urljoin(self.chapter_url, url)
            return url

        tag = self._get_selector_tag(page, selector)
        if not tag:
            return None
        if tag.name != "a":
            return None
        result = tag['href']
        if isinstance(result, str):
            return absolute_url(result)
        return absolute_url(result[0])

    def _get_chapter_number(self, page: bs4.BeautifulSoup) -> float | None:
        number_str = self._get_selector_content(page, self.chapter_number_selector)
        if not number_str:
            return None
        try:
            return float(number_str)
        except ValueError:
            ...
        if not self.chapter_number_regex:
            return None
        found = re.findall(self.chapter_number_regex, number_str)
        if not found:
            return None
        return float(found[0])

    def update_chapter(self):
        browser = self.open_chapter()
        page = self._get_page(browser)
        self.chapter_number = self._get_chapter_number(page)
        self.next_chapter_url = self._get_selector_link(page, self.next_chapter_url_selector)

    def update_bookmark_url(self):
        browser = self.open_chapter()
        page = self._get_page(browser)
        self.url = self._get_selector_link(page, self.url_selector)

    def update_main_page(self):
        browser = self.open_main_page()
        if browser is None:
            return
        page = self._get_page(browser)
        self.title = self._get_selector_content(page, self.title_selector) or ''
        self.description = self._get_selector_content(page, self.description_selector) or ''

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
