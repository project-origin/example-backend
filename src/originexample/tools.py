# -*- coding: utf-8 -*-

import re
import time
import random
import hashlib

# from .settings import SECRET


def salted_hash(*args):
    hasher = hashlib.md5()
    hasher.update(SECRET.encode('utf8'))
    for arg in args:
        hasher.update(str(arg).encode('utf8'))
    return hasher.hexdigest()


def randomized_hash(*args):
    return salted_hash(random.randint(0, 9999999), time.time(), *args)


password_hash = salted_hash


# -- Creating URL slugs ------------------------------------------------------


_slugify_special_chars = {
    u'æ': 'ae',
    u'ø': 'oe',
    u'å': 'aa',
    u'á': 'a',
    u'à': 'a',
    u'ä': 'a',
    u'ü': 'u',
}

_slugify_patterns = (
    (re.compile(r'([^a-zA-Z0-9])'), '-'),   # Non alphabetic chars
    (re.compile(r'(-)+'), '-'),             # Multiple dashes
    (re.compile(r'^(-*)'), ''),             # Leading dashes
    (re.compile(r'(-*)$'), ''),             # Trailing dashes
)


def slugify(*args):
    """
    Convert a string to an URL-friendly slug
    """
    s = '-'.join(map(str, args)).lower()
    for char, replace in _slugify_special_chars.items():
        s = s.replace(char, replace)
    for pattern, replace in _slugify_patterns:
        s = pattern.sub(replace, s)
    return s
