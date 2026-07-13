# configurations/translations/__init__.py
#
# This package provides runtime translation support.
#
# Public API (re-exported for backward-compatible imports):
#   from configurations.translations import get_translations
#   from configurations.translations import TranslationProxy
#
# Implementation lives in:
#   configurations/translations/utils.py      ← TranslationProxy, get_translations
#
# Language ID → language code mapping lives in:
#   configurations/constants.py               ← LANGUAGE_MAP
#
# Per-language string dictionaries live in:
#   configurations/translations/{en,hi,fr,bn}/__init__.py  (STRINGS dict)

from configurations.translations.utils import TranslationProxy, get_translations

__all__ = ['TranslationProxy', 'get_translations']
