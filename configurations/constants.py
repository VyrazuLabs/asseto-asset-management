# configurations/constants.py

# Maps the integer language ID (stored in LocalizationConfiguration.default_language)
# to the language-code subdirectory under configurations/translations/.
# Add new languages here; the translations package and ACTIVE_LANGUAGES list
# will pick them up automatically.
LANGUAGE_MAP = {
    0: 'en',
    2: 'fr',
    8: 'hi',
    9: 'bn',
}

# Example dropdown values
COUNTRY_CHOICES = [
    (0, 'India'),
    (1, 'Saudi Arabia'),
    (2, 'Kuwait'),
    (3, 'Qatar'),
    (4, 'Oman'),
    (5, 'United Arab Emirates'),
    (6, 'United Kingdom'),
    (7, 'United States of America'),
    (8, 'Germany'),
    (9, 'France'),
    (10, 'Japan'),
]

DEFAULT_LANGUAGE=[
    (0, 'English'),
    (1, 'Espaniol'),
    (2, 'French'),
    (3, 'German'),
    (4, 'Italian'),
    (5, 'Portuguese'),
    (6, 'Russian'),
    (7, 'Chinese'),
    (8, 'Hindi'),
    (9, 'Bengali'),]

# Derived from LANGUAGE_MAP above so there is a single source of truth.
# To add or remove a supported language, update LANGUAGE_MAP above —
# this list will follow automatically.
def _build_active_languages():
    _label_map = dict(DEFAULT_LANGUAGE)
    return [(lang_id, _label_map.get(lang_id, lang_code.upper()))
            for lang_id, lang_code in LANGUAGE_MAP.items()]

ACTIVE_LANGUAGES = _build_active_languages()

ASSET_STATUS_CHOICES = [
    ('ready', 'Ready to Deploy'),
    ('broken', 'Broken'),
    ('deployed', 'Deployed'),
    ('retired', 'Retired'),
]

PURCHASE_TYPE_CHOICES = [
    ('capex', 'Capital Expenditure'),
    ('opex', 'Operational Expenditure'),
]
CURRENCY_CHOICES = [
    (0, 'USD'),
    (1, 'EUR'),
    (2, 'GBP'),
    (3, 'AED'),
    (4, 'SAR'),
    (5, 'KWD'),
    (6, 'INR'),
    (7, 'JPY'),
]

INTEGRATION_CHOICES = [
    (0, ['Slack','Install the slack to get real time updates about any addition or updation in your asset application']),
    (1,['API',''])
]

DATETIME_CHOICES=[
    (0, 'YYYY-MM-DD'),
    (1, 'Day Month DD, Year'),
    (2, 'Month DD, YYYY'),
    (3, 'DD/MM/YYYY'),
    (4, 'MM/DD/YYYY'),
]
DEFAULT_COUNTRY='India'
DEFAULT_CURRENCY = 'USD'
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
PAGE_SIZE = 10
ORPHANS = 1
NAME_FORMATS = [
    (0, '{first} {last}'),
    (1, '{last} {first}'),
    (2, '{first_initial}. {last}'),
    (3, '{last}, {first}'),
]