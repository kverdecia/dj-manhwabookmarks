import re

import soupsieve

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_selector_syntax(value):
    try:
        soupsieve.compile(value)
    except soupsieve.util.SelectorSyntaxError:
        raise ValidationError(_("Invalid css selector syntax."))


def validate_regex_syntax(value):
    try:
        re.compile(value)
    except re.error:
        raise ValidationError(_("Invalid regular expression syntax."))
