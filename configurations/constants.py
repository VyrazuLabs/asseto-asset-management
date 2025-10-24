# configurations/constants.py

# Example dropdown values
COUNTRY_CHOICES = [
    (1, 'United Arab Emirates'),
    (2, 'Saudi Arabia'),
    (3, 'Kuwait'),
    (4, 'Qatar'),
    (5, 'Oman'),
    (6, 'United States of America'),
    (7, 'United Kingdom'),
    (8, 'India'),
    (9, 'Germany'),
    (10, 'France'),
    (11, 'Japan'),
]

DEFAULT_LANGUAGE=[
    (1, 'English'),
    (2, 'Espaniol'),
    (3, 'French'),
    (4, 'German'),
    (5, 'Italian'),
    (6, 'Portuguese'),
    (7, 'Russian'),
    (8, 'Chinese'),
    (9, 'Hindi'),
    (10, 'Bengali'),]

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
    (1, 'USD'),
    (2, 'EUR'),
    (3, 'GBP'),
    (4, 'AED'),
    (5, 'SAR'),
]

DATETIME_CHOICES=[
    (1, 'YYYY-MM-DD'),
    (2, 'Day Month DD, Year'),
    (3, 'Month DD, YYYY'),
    (4, 'DD/MM/YYYY'),
    (5, 'MM/DD/YYYY'),
]

DEFAULT_CURRENCY = 'USD'
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
PAGE_SIZE = 10
ORPHANS = 1
DEFAULT_NAME_DISPLAY_FORMAT = [(1, 'first_name  last_name'), (2, 'last_name  first_name')]  # e.g., John Doe