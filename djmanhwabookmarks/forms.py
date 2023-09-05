from django import forms

from . import models


class BookmarkForm(forms.ModelForm):
    class Meta:
        model = models.ManhwaBookmark
        fields = (
            'name', 'url_selector', 'title_selector', 'description_selector',
            'chapter_url', 'chapter_number_selector', 'chapter_number_regex',
            'next_chapter_url_selector', 'next_chapter_opened',
        )

    def save(self, commit=True) -> models.ManhwaBookmark:
        bookmark = super().save(commit=commit)
        bookmark.copy_template_fields_if_empty()
        bookmark.update_bookmark(save=commit)
        return bookmark
