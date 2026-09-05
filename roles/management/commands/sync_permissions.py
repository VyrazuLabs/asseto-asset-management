from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand

from common.permissions import PERMISSION_MODULES, get_content_type_for_module


class Command(BaseCommand):
    """Ensure every codename in ``PERMISSION_MODULES`` exists as a real
    ``Permission`` row on its correct ContentType.

    Idempotent — safe to re-run on every deploy, analogous to Django's own
    ``create_permissions`` post_migrate signal. This is the only intended
    writer of ``Permission`` rows going forward; ``roles/views.py`` looks
    them up rather than creating them.
    """

    help = "Create/update Permission rows for every module in common.permissions.PERMISSION_MODULES."

    def handle(self, *args, **options):
        """Walk the registry and ``get_or_create`` each declared permission.

        Args:
            *args: Unused.
            **options: Unused management-command options.
        """
        created_count = 0
        existing_count = 0

        for module in PERMISSION_MODULES:
            content_type = get_content_type_for_module(module)

            for action in module.actions:
                _, created = Permission.objects.get_or_create(
                    codename=action.codename,
                    content_type=content_type,
                    defaults={"name": f"Can {action.label.lower()} {module.label.lower()}"},
                )
                if created:
                    created_count += 1
                else:
                    existing_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"sync_permissions: {created_count} created, {existing_count} already present.")
        )
