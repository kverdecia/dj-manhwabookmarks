from typing import cast, Protocol, Iterator
import time
import re
from urllib.parse import urljoin
from dataclasses import dataclass
from lxml import etree, html
from contextlib import contextmanager
from playwright.sync_api import Page, sync_playwright, Locator

import bs4
import mechanicalsoup
import soupsieve
import requests

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


@dataclass
class ExtractorParams:
    chapter_url: str
    chapter_number_selector: str
    chapter_number_regex: str

    next_chapter_url_selector: str

    url_selector: str
    title_selector: str
    description_selector: str


@dataclass
class ExtractorResult:
    url: str | None = None
    title: str = ''
    description: str = ''
    chapter_number: float | None = None
    next_chapter_url: str | None = None


class ExtractorBackend(Protocol):
    @staticmethod
    def validate_selector_syntax(value: str):
        ...

    def open(self, url: str) -> None:
        ...

    def get_text_content(self, selector: str) -> str | None:
        ...

    def get_attribute(self, selector: str, attribute: str, required_tag: str | None = None) -> str | None:
        ...

    @contextmanager
    def context(self) -> Iterator['ExtractorBackend']:
        ...


class Extractor(Protocol):
    def __init__(self, backend: ExtractorBackend, params: ExtractorParams):
        ...

    def __call__(self) -> ExtractorResult:
        ...

    def validate_params(self) -> None:
        ...


# class ValidatorsMixin:
#     @staticmethod
#     def validate_selector_syntax(value: str):
#         try:
#             soupsieve.compile(value)
#         except soupsieve.util.SelectorSyntaxError:
#             raise ValidationError(_("Invalid css selector syntax."))

#     @staticmethod
#     def validate_regex_syntax(value: str):
#         try:
#             re.compile(value)
#         except re.error:
#             raise ValidationError(_("Invalid regular expression syntax."))


class MechanicalSoupExtractorBackend:
    browser: mechanicalsoup.StatefulBrowser
    page: bs4.BeautifulSoup | None

    def __init__(self):
        self.browser = mechanicalsoup.StatefulBrowser()
        self.page = None

    def open(self, url: str) -> None:
        self.browser.open(url)
        self.page = cast(bs4.BeautifulSoup, self.browser.page)

    def _get_selector_tag(self, selector: str | None) -> bs4.Tag | None:
        if not selector or not self.page:
            return None
        tag = self.page.select_one(selector)
        if not tag:
            return None
        return tag

    def get_text_content(self, selector: str) -> str | None:
        tag = self._get_selector_tag(selector)
        if tag is None:
            return None
        return tag.get_text().strip()

    def get_attribute(self, selector: str, attribute: str, required_tag: str | None = None) -> str | None:
        tag = self._get_selector_tag(selector)
        if tag is None:
            return None
        if required_tag and tag.name != required_tag:
            return None
        result = tag.get(attribute, None)
        if result is None:
            return None
        if isinstance(result, str):
            return result
        return result[0]

    @staticmethod
    def validate_selector_syntax(value: str):
        try:
            soupsieve.compile(value)
        except soupsieve.util.SelectorSyntaxError:
            raise ValidationError(_("Invalid css selector syntax."))

    @contextmanager
    def context(self) -> Iterator['ExtractorBackend']:
        yield self


class PlayWrightExtractorBackend:
    page: Page | None

    def __init__(self):
        self.page = None

    def open(self, url: str) -> None:
        if self.page is None:
            return None
        self.page.goto(url)
        time.sleep(2)

    def _get_selector_tag(self, selector: str | None) -> Locator | None:
        "Returns the first tag from the locator obtained from the selector parameter. If locator is empty returns None."
        if not selector or not self.page:
            return None
        locator = self.page.locator(selector)
        if locator.count() == 0:
            return None
        return locator.first

    def get_text_content(self, selector: str) -> str | None:
        tag = self._get_selector_tag(selector)
        if tag is None:
            return None
        return (tag.text_content() or '').strip()

    def get_attribute(self, selector: str, attribute: str, required_tag: str | None = None) -> str | None:
        locator = self._get_selector_tag(selector)
        if locator is None:
            return None
        if required_tag:
            tag_name = locator.evaluate("element => element.tagName")
            if not tag_name or tag_name.lower() != required_tag.lower():
                return None
        return locator.get_attribute(attribute)

    @staticmethod
    def validate_selector_syntax(value: str):
        ...

    @contextmanager
    def context(self) -> Iterator['ExtractorBackend']:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            self.page = browser.new_page()
            yield self


class LXmlXpathExtractorBackend:
    page_content: str | None
    xml: etree._Element | None

    def __init__(self):
        self.page = None

    def open(self, url: str) -> None:
        response = requests.get(url)
        response.raise_for_status()
        self.page_content = response.text
        self.xml = html.parse(self.page_content)

    def _get_selector_tag(self, selector: str | None) -> bs4.Tag | None:
        if not selector or not self.page:
            return None
        tag = self.page.select_one(selector)
        if not tag:
            return None
        return tag

    def get_text_content(self, selector: str) -> str | None:
        tag = self._get_selector_tag(selector)
        if tag is None:
            return None
        return tag.get_text().strip()

    def get_attribute(self, selector: str, attribute: str, required_tag: str | None = None) -> str | None:
        tag = self._get_selector_tag(selector)
        if tag is None:
            return None
        if required_tag and tag.name != required_tag:
            return None
        result = tag.get(attribute, None)
        if result is None:
            return None
        if isinstance(result, str):
            return result
        return result[0]

    @staticmethod
    def validate_selector_syntax(value: str):
        try:
            soupsieve.compile(value)
        except soupsieve.util.SelectorSyntaxError:
            raise ValidationError(_("Invalid css selector syntax."))


class SimpleExtractor:
    params: ExtractorParams
    backend: ExtractorBackend

    def __init__(self, backend: ExtractorBackend, params: ExtractorParams):
        self.params = params
        self.backend = backend

    @staticmethod
    def validate_regex_syntax(value: str):
        try:
            re.compile(value)
        except re.error:
            raise ValidationError(_("Invalid regular expression syntax."))

    def validate_params(self) -> None:
        errors = {}
        try:
            self.backend.validate_selector_syntax(self.params.chapter_number_selector)
        except ValidationError as e:
            errors['chapter_number_selector'] = e
        try:
            self.backend.validate_selector_syntax(self.params.next_chapter_url_selector)
        except ValidationError as e:
            errors['next_chapter_url_selector'] = e
        try:
            self.backend.validate_selector_syntax(self.params.url_selector)
        except ValidationError as e:
            errors['url_selector'] = e
        try:
            self.backend.validate_selector_syntax(self.params.title_selector)
        except ValidationError as e:
            errors['title_selector'] = e
        try:
            self.backend.validate_selector_syntax(self.params.description_selector)
        except ValidationError as e:
            errors['description_selector'] = e
        try:
            self.validate_regex_syntax(self.params.chapter_number_regex)
        except ValidationError as e:
            errors['chapter_number_regex'] = e
        if errors:
            raise ValidationError(errors)

    def _get_selector_content(self, selector: str) -> str | None:
        return self.backend.get_text_content(selector)

    def _get_selector_link(self, selector: str) -> str | None:
        def absolute_url(url: str) -> str:
            if url.startswith('/'):
                return urljoin(self.params.chapter_url, url)
            return url
        result = self.backend.get_attribute(selector, 'href', required_tag='a')
        if result is None:
            return None
        return absolute_url(result)

    def _get_chapter_number(self) -> float | None:
        number_str = self.backend.get_text_content(self.params.chapter_number_selector)
        if not number_str:
            return None
        try:
            return float(number_str)
        except ValueError:
            ...
        if not self.params.chapter_number_regex:
            return None
        found = re.findall(self.params.chapter_number_regex, number_str)
        if not found:
            return None
        return float(found[0])

    def update_chapter(self, result: ExtractorResult) -> None:
        self.backend.open(self.params.chapter_url)
        result.chapter_number = self._get_chapter_number()
        result.next_chapter_url = self._get_selector_link(self.params.next_chapter_url_selector)

    def update_bookmark_url(self, result: ExtractorResult) -> None:
        # self.backend.open(self.params.chapter_url)
        result.url = self._get_selector_link(self.params.url_selector)

    def update_main_page(self, result: ExtractorResult) -> None:
        if result.url is None:
            return
        self.backend.open(result.url)
        result.title = self._get_selector_content(self.params.title_selector) or ''
        result.description = self._get_selector_content(self.params.description_selector) or ''

    def __call__(self) -> ExtractorResult:
        with self.backend.context():
            result = ExtractorResult()
            self.update_chapter(result)
            self.update_bookmark_url(result)
            self.update_main_page(result)
            return result
