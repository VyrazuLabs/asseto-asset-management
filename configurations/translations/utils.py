import importlib


class TranslationProxy:
    """
    Provides attribute-style and dict-style access to translation strings.
    Falls back to the English (fallback) string when a key is missing in the
    target language, and returns a bracketed key name when it can't be found
    in either dictionary – so templates never render an empty string silently.
    """

    def __init__(self, target_strings, fallback_strings):
        self.target = target_strings
        self.fallback = fallback_strings

    def __getitem__(self, key):
        return self.target.get(key, self.fallback.get(key, f"[{key}]"))

    def __getattr__(self, key):
        return self.target.get(key, self.fallback.get(key, f"[{key}]"))

    def get(self, key, default=None):
        return self.target.get(key, self.fallback.get(key, default))


def get_translations(lang_id):
    """
    Load and return a TranslationProxy for the given language ID.

    Always loads English as the fallback so that missing keys still render a
    readable string.  Silently falls back to English if the requested language
    module cannot be imported.
    """
    from configurations.constants import LANGUAGE_MAP

    lang_code = LANGUAGE_MAP.get(int(lang_id or 0), 'en')

    # Always load English as fallback
    try:
        from configurations.translations import en
        fallback_strings = getattr(en, 'STRINGS', {})
    except ImportError:
        fallback_strings = {}

    if lang_code == 'en':
        return TranslationProxy(fallback_strings, fallback_strings)

    try:
        module = importlib.import_module(f'configurations.translations.{lang_code}')
        target_strings = getattr(module, 'STRINGS', {})
        return TranslationProxy(target_strings, fallback_strings)
    except (ImportError, AttributeError):
        # Always return a TranslationProxy (not a plain dict) so that
        # attribute-style access in templates (trans.some_key) never raises AttributeError.
        return TranslationProxy(fallback_strings, fallback_strings)
