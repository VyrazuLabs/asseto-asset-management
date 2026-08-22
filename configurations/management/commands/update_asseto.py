"""`python manage.py update_asseto`

Full core update: git pull, dependency install, migrate, collectstatic,
graceful reload. See docs/extension-architecture.md §8.
"""

from django.core.management.base import BaseCommand, CommandError

from configurations.extensions.core_updater import run_core_update_steps


class Command(BaseCommand):
    help = "Update Asseto core: git pull, install dependencies, migrate, collectstatic, reload."

    def handle(self, *args, **options):
        try:
            run_core_update_steps()
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Core update complete."))
