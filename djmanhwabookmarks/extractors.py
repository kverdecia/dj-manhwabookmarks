from typing import cast, Protocol
import re
from urllib.parse import urljoin
from dataclasses import dataclass

import bs4
import mechanicalsoup
import soupsieve

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


class Extractor(Protocol):
    def __init__(self, params: ExtractorParams):
        ...

    def __call__(self) -> ExtractorResult:
        ...

    def validate_params(self) -> None:
        ...


class ValidatorsMixin:
    @staticmethod
    def validate_selector_syntax(value: str):
        try:
            soupsieve.compile(value)
        except soupsieve.util.SelectorSyntaxError:
            raise ValidationError(_("Invalid css selector syntax."))

    @staticmethod
    def validate_regex_syntax(value: str):
        try:
            re.compile(value)
        except re.error:
            raise ValidationError(_("Invalid regular expression syntax."))


class MechanicalSoupExtractor(ValidatorsMixin):
    params: ExtractorParams

    def __init__(self, params: ExtractorParams):
        self.params = params

    def open_main_page(self, url: str | None) -> mechanicalsoup.StatefulBrowser | None:
        if not url:
            return None
        browser = mechanicalsoup.StatefulBrowser()
        browser.open(url)
        return browser

    def open_chapter(self) -> mechanicalsoup.StatefulBrowser:
        browser = mechanicalsoup.StatefulBrowser()
        browser.open(self.params.chapter_url)
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
                return urljoin(self.params.chapter_url, url)
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
        number_str = self._get_selector_content(page, self.params.chapter_number_selector)
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
        browser = self.open_chapter()
        page = self._get_page(browser)
        result.chapter_number = self._get_chapter_number(page)
        result.next_chapter_url = self._get_selector_link(page, self.params.next_chapter_url_selector)

    def update_bookmark_url(self, result: ExtractorResult):
        browser = self.open_chapter()
        page = self._get_page(browser)
        result.url = self._get_selector_link(page, self.params.url_selector)

    def update_main_page(self, result: ExtractorResult):
        browser = self.open_main_page(result.url)
        if browser is None:
            return
        page = self._get_page(browser)
        result.title = self._get_selector_content(page, self.params.title_selector) or ''
        result.description = self._get_selector_content(page, self.params.description_selector) or ''

    def validate_params(self) -> None:
        errors = {}
        try:
            self.validate_selector_syntax(self.params.chapter_number_selector)
        except ValidationError as e:
            errors['chapter_number_selector'] = e
        try:
            self.validate_selector_syntax(self.params.next_chapter_url_selector)
        except ValidationError as e:
            errors['next_chapter_url_selector'] = e
        try:
            self.validate_selector_syntax(self.params.url_selector)
        except ValidationError as e:
            errors['url_selector'] = e
        try:
            self.validate_selector_syntax(self.params.title_selector)
        except ValidationError as e:
            errors['title_selector'] = e
        try:
            self.validate_selector_syntax(self.params.description_selector)
        except ValidationError as e:
            errors['description_selector'] = e
        try:
            self.validate_regex_syntax(self.params.chapter_number_regex)
        except ValidationError as e:
            errors['chapter_number_regex'] = e
        if errors:
            raise ValidationError(errors)

    def __call__(self) -> ExtractorResult:
        result = ExtractorResult()
        self.update_chapter(result)
        self.update_bookmark_url(result)
        self.update_main_page(result)
        return result
