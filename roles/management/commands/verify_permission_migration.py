from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from authentication.models import User
from common.permissions import codename_to_app_label
from roles.models import Role


class Command(BaseCommand):
    """Verify no Role lost a permission during the ContentType repoint.

    Compares each Role's permission codename set against a snapshot taken
    before the migration ran (see ``--baseline``); with no baseline given,
    only checks that no non-user codename is still glued to the fake
    ``authentication.User`` ContentType. Exits non-zero on any discrepancy
    so it can gate a deploy in CI.
    """

    help = "Verify the ContentType-repoint migration preserved every Role's permissions."

    def add_arguments(self, parser):
        """Register command-line arguments.

        Args:
            parser: The argparse parser to add arguments to.
        """
        parser.add_argument(
            "--baseline",
            type=str,
            default=None,
            help="Path to a JSON file of {role_id: [codenames]} captured before migrating.",
        )

    def handle(self, *args, **options):
        """Run both checks and report/raise on failure.

        Args:
            *args: Unused.
            **options: Parsed command-line options (``baseline``).

        Raises:
            CommandError: If any orphaned permission or lost role
                permission is found.
        """
        errors = []
        errors.extend(self._check_no_orphaned_fake_permissions())

        baseline_path = options.get("baseline")
        if baseline_path:
            errors.extend(self._check_against_baseline(baseline_path))

        if errors:
            for error in errors:
                self.stderr.write(self.style.ERROR(error))
            raise CommandError(f"verify_permission_migration: {len(errors)} problem(s) found.")

        self.stdout.write(self.style.SUCCESS("verify_permission_migration: OK."))

    def _check_no_orphaned_fake_permissions(self) -> list:
        """Find non-user codenames still pinned to the fake User ContentType.

        Returns:
            list[str]: Human-readable error strings, empty if clean.
        """
        user_ct = ContentType.objects.get_for_model(User)
        real_user_codenames = set(get_module_codenames_for_app("authentication"))
        stray = (
            Permission.objects.filter(content_type=user_ct)
            .exclude(codename__in=real_user_codenames)
            .values_list("codename", flat=True)
        )
        return [f"Permission '{codename}' is still pinned to the fake authentication.User ContentType." for codename in stray]

    def _check_against_baseline(self, baseline_path: str) -> list:
        """Diff current Role permission codenames against a pre-migration snapshot.

        Args:
            baseline_path: Path to a JSON file mapping role id -> codename list.

        Returns:
            list[str]: Human-readable error strings, empty if nothing was lost.
        """
        import json

        with open(baseline_path) as handle:
            baseline = json.load(handle)

        errors = []
        for role_id, expected_codenames in baseline.items():
            try:
                role = Role.objects.get(pk=role_id)
            except Role.DoesNotExist:
                errors.append(f"Role {role_id} from baseline no longer exists.")
                continue

            current_codenames = set(role.permissions.values_list("codename", flat=True))
            missing = set(expected_codenames) - current_codenames
            if missing:
                errors.append(f"Role {role_id} ({role.related_name}) lost permissions: {sorted(missing)}")

        return errors


def get_module_codenames_for_app(app_label: str) -> list:
    """Codenames from ``PERMISSION_MODULES`` that legitimately belong to ``app_label``.

    Args:
        app_label: The app label to filter by, e.g. "authentication".

    Returns:
        list[str]: Codenames whose module is genuinely owned by that app.
    """
    mapping = codename_to_app_label()
    return [codename for codename, owner in mapping.items() if owner == app_label]
