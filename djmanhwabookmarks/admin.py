# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _, gettext
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from . import models


@admin.register(models.ManhwaBookmark)
class ManhwaBookmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_url', 'get_chapter_number', 'get_next_chapter')
    readonly_fields = ('url', 'title', 'description', 'chapter_number', 'next_chapter_url')
    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        (_('Main info'), {
            'fields': ('url', 'url_selector', 'title', 'title_selector', 'description', 'description_selector')
        }),
        (_('Chapter'), {
            'fields': ('chapter_url', 'chapter_number', 'chapter_number_selector', 'chapter_number_regex')
        }),
        (_('Next chapter'), {
            'fields': ('next_chapter_url', 'next_chapter_url_selector', 'next_chapter_opened')
        }),
    )

    @admin.display(description=_('Url'))
    def get_url(self, obj: models.ManhwaBookmark) -> str | None:
        if not obj.url:
            return None
        return mark_safe(f'<a href="{obj.url}" target="__blank">{obj.url}</a>')

    @admin.display(description=_('Chapter'))
    def get_chapter_number(self, obj: models.ManhwaBookmark) -> str | None:
        if not obj.chapter_number:
            return None
        id = f'bookmark-{obj.pk}-chapter-number'
        return format_html(
            '<a id="{}" href="{}" target="__blank">{}</a>',
            id, obj.chapter_url, obj.chapter_number
        )

    @admin.display(description=_('Next chapter'))
    def get_next_chapter(self, obj: models.ManhwaBookmark) -> str | None:
        if not obj.next_chapter_url:
            return None
        msg = gettext('Next chapter')
        return format_html('<a href="{}" target="__blank">{}</a>', obj.next_chapter_url, msg)
