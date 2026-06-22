import importlib

LANGUAGE_MAP = {
    0: "en",
    2: "fr",
    8: "hi",
    9: "bn",
}


class TranslationProxy:
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
    lang_code = LANGUAGE_MAP.get(int(lang_id or 0), "en")

    # Always load English as fallback
    try:
        from configurations.translations import en

        fallback_strings = getattr(en, "STRINGS", {})
    except ImportError:
        fallback_strings = {}

    if lang_code == "en":
        return TranslationProxy(fallback_strings, fallback_strings)

    try:
        module = importlib.import_module(f"configurations.translations.{lang_code}")
        target_strings = getattr(module, "STRINGS", {})
        return TranslationProxy(target_strings, fallback_strings)
    except (ImportError, AttributeError):
        # Always return a TranslationProxy (not a plain dict) so that
        # attribute-style access in templates (trans.some_key) never raises AttributeError.
        return TranslationProxy(fallback_strings, fallback_strings)
