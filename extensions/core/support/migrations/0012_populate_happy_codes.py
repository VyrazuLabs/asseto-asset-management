from django.db import migrations
import random
import string

def gen_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def populate_happy_codes(apps, schema_editor):
    SupportTicket = apps.get_model('support', 'SupportTicket')
    # Generate for all tickets that don't have a happy code
    for ticket in SupportTicket.objects.filter(happy_code__isnull=True):
        ticket.happy_code = gen_code()
        ticket.save(update_fields=['happy_code'])

class Migration(migrations.Migration):

    dependencies = [
        ('support', '0011_remove_historicalsupportticket_created_by_contact_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_happy_codes, reverse_code=migrations.RunPython.noop),
    ]
