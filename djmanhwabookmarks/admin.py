# -*- coding: utf-8 -*-
from django.urls import path
from django.utils.translation import gettext_lazy as _, gettext
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.template.loader import render_to_string

from django_htmx.http import trigger_client_event

from . import models
from . import forms


@admin.register(models.ManhwaBookmark)
class ManhwaBookmarkAdmin(admin.ModelAdmin):
    class Media:
        js = [
            'https://unpkg.com/htmx.org@1.9.5',
            'js/djmanhwabookmarks.js',
        ]

    actions = ('update_bookmark',)
    list_display = ('get_name', 'get_url', 'get_chapter_number', 'get_next_chapter')
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
    form = forms.BookmarkForm

    @admin.display(description=_('Name'))
    def get_name(self, obj: models.ManhwaBookmark) -> str:
        return str(obj)

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
        context = {'bookmark': obj}
        return render_to_string('djmanhwabookmarks/bookmark_actions.html', context)

    @admin.action(description=_('Update bookmark'))
    def update_bookmark(self, request, queryset):
        for bookmark in queryset:
            bookmark.update_bookmark()
        self.message_user(request, gettext('Bookmarks updated'))

    def get_urls(self):
        url = super().get_urls()
        custom_urls = [
            path(
                '<int:bookmark_id>/bookmark-actions/',
                self.admin_site.admin_view(self.bookmark_actions),
                name='bookmark-actions'
            ),
            path(
                '<int:bookmark_id>/view-next-chapter/',
                self.admin_site.admin_view(self.view_next_chapter),
                name='view-bookmark-next-chapter'
            ),
            path(
                '<int:bookmark_id>/change-to-next-chapter/',
                self.admin_site.admin_view(self.change_to_next_chapter),
                name='change-bookmark-to-next-chapter'
            ),
        ]
        return custom_urls + url

    def render_bookmark_actions_response(self, request, bookmark: models.ManhwaBookmark) -> HttpResponse:
        context = {'bookmark': bookmark}
        return render(request, 'djmanhwabookmarks/bookmark_actions_response.html', context)

    def bookmark_actions(self, request, bookmark_id, *args, **kwargs):
        bookmark = get_object_or_404(models.ManhwaBookmark, pk=bookmark_id)
        return self.render_bookmark_actions_response(request, bookmark)

    def view_next_chapter(self, request, bookmark_id, *args, **kwargs):
        bookmark = get_object_or_404(models.ManhwaBookmark, pk=bookmark_id)
        bookmark.mark_next_chapter_opened()
        response = self.render_bookmark_actions_response(request, bookmark)
        trigger_client_event(
            response,
            'openNextChapterUrl',
            {'next_chapter_url': bookmark.next_chapter_url},
            after='swap')
        return response

    def change_to_next_chapter(self, request, bookmark_id, *args, **kwargs):
        bookmark = get_object_or_404(models.ManhwaBookmark, pk=bookmark_id)
        bookmark.change_to_next_chapter()
        return self.render_bookmark_actions_response(request, bookmark)
