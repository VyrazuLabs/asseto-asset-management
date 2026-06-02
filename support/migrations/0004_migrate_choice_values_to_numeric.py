# Converts legacy word-based choice values to the numeric-string keys now
# used by the SupportTicket model. Safe to run multiple times (idempotent).

from django.db import migrations


PRIORITY_MAP = {
    'emergency': '3',
    'high':      '2',
    'medium':    '1',
    'low':       '0',
}

STATUS_MAP = {
    'open':        '0',
    'in_progress': '1',
    'in_testing':  '2',
    'resolved':    '3',
    'closed':      '4',
}

IMPACT_MAP = {
    'critical': '3',
    'high':     '2',
    'medium':   '1',
    'low':      '0',
}


def migrate_forward(apps, schema_editor):
    SupportTicket = apps.get_model('support', 'SupportTicket')
    for ticket in SupportTicket.objects.all():
        changed = False
        new_priority = PRIORITY_MAP.get(ticket.priority)
        if new_priority:
            ticket.priority = new_priority
            changed = True
        new_status = STATUS_MAP.get(ticket.status)
        if new_status:
            ticket.status = new_status
            changed = True
        new_impact = IMPACT_MAP.get(ticket.impact_level)
        if new_impact:
            ticket.impact_level = new_impact
            changed = True
        if changed:
            ticket.save(update_fields=['priority', 'status', 'impact_level'])


def migrate_backward(apps, schema_editor):
    """Reverse: numeric → word-based. Provided for completeness."""
    PRIORITY_REVERSE = {v: k for k, v in PRIORITY_MAP.items()}
    STATUS_REVERSE   = {v: k for k, v in STATUS_MAP.items()}
    IMPACT_REVERSE   = {v: k for k, v in IMPACT_MAP.items()}

    SupportTicket = apps.get_model('support', 'SupportTicket')
    for ticket in SupportTicket.objects.all():
        changed = False
        new_priority = PRIORITY_REVERSE.get(ticket.priority)
        if new_priority:
            ticket.priority = new_priority
            changed = True
        new_status = STATUS_REVERSE.get(ticket.status)
        if new_status:
            ticket.status = new_status
            changed = True
        new_impact = IMPACT_REVERSE.get(ticket.impact_level)
        if new_impact:
            ticket.impact_level = new_impact
            changed = True
        if changed:
            ticket.save(update_fields=['priority', 'status', 'impact_level'])


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0003_delete_support'),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
