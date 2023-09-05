# -*- coding: utf-8 -*-
from typing import cast
import re
from urllib.parse import urljoin

from django.utils.translation import gettext_lazy as _
from django.db import models

import bs4
import mechanicalsoup

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

    def _get_chapter_number(self, page: bs4.BeautifulSoup) -> int | None:
        number_str = self._get_selector_content(page, self.chapter_number_selector)
        if not number_str:
            return None
        try:
            return int(number_str)
        except ValueError:
            ...
        if not self.chapter_number_regex:
            return None
        found = re.findall(self.chapter_number_regex, number_str)
        if not found:
            return None
        return int(found[0])

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
