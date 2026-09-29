from django.core.management.base import BaseCommand
from django.db import transaction

from consumables.models import CONSUMABLE_ID_START, Consumable
from dashboard.models import Organization


class Command(BaseCommand):
    """Assign sequential consumable_id values (from 100000) to existing consumables.

    Ids are allocated per organization in created_at order, including
    soft-deleted rows. Rows that already have an id are left untouched, so the
    command is idempotent and safe to re-run.
    """

    help = "Backfill consumable_id for existing consumables, starting at 100000 per organization."

    def add_arguments(self, parser):
        """Register the --dry-run flag."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be assigned without writing.",
        )

    def handle(self, *args, **options):
        """Assign ids inside one transaction, org by org.

        Args:
            *args: Unused.
            **options: Parsed options; ``dry_run`` skips the writes.
        """
        dry_run = options["dry_run"]
        org_ids = list(
            Consumable.objects.filter(consumable_id__isnull=True)
            .values_list("organization_id", flat=True)
            .distinct()
        )
        updated = 0

        with transaction.atomic():
            for org_id in org_ids:
                if org_id:
                    Organization.objects.select_for_update().get(pk=org_id)
                pending = Consumable.objects.filter(
                    organization_id=org_id, consumable_id__isnull=True
                ).order_by("created_at", "pk")
                highest = (
                    Consumable.objects.filter(
                        organization_id=org_id, consumable_id__isnull=False
                    )
                    .order_by("-consumable_id")
                    .values_list("consumable_id", flat=True)
                    .first()
                )
                next_id = CONSUMABLE_ID_START if highest is None else highest + 1
                for consumable in pending:
                    if not dry_run:
                        Consumable.objects.filter(pk=consumable.pk).update(
                            consumable_id=next_id
                        )
                    updated += 1
                    next_id += 1
            if dry_run:
                transaction.set_rollback(True)

        verb = "Would assign" if dry_run else "Assigned"
        self.stdout.write(self.style.SUCCESS(f"{verb} consumable_id to {updated} consumable(s)."))
