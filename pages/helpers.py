from urllib.parse import unquote

from django.template.defaultfilters import urlencode


class Slugify:
    @classmethod
    def encode(cls, value):
        return urlencode(urlencode(value, ''), '')

    @classmethod
    def decode(cls, value):
        return unquote(unquote(value))
