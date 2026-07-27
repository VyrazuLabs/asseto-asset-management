from django.core.management.base import BaseCommand, CommandError
from authentication.models import User
from dashboard.models import Organization


class Command(BaseCommand):
    help = "Register a new user"

    def add_arguments(self, parser):
        parser.add_argument('--fullname', required=True, help="Full name of the user")
        parser.add_argument('--email', required=True, help="Email address")
        parser.add_argument('--username', required=True, help="Username")
        parser.add_argument('--phone', required=True, help="Phone number")
        parser.add_argument('--password', required=True, help="Password")
        parser.add_argument('--company_name', required=True, help="Company/Organization name")
        parser.add_argument('--company_website', required=True, help="Company website")

    def handle(self, *args, **options):
        if User.objects.filter(username=options['username']).exists():
            raise CommandError(f"User with username '{options['username']}' already exists.")

        if User.objects.filter(email=options['email']).exists():
            raise CommandError(f"User with email '{options['email']}' already exists.")

        organization, _ = Organization.objects.get_or_create(
            name=options['company_name'],
            defaults={'website': options['company_website']}
        )

        user = User.objects.create_user(
            email=options["email"],
            full_name=options["fullname"],
            username=options["username"],
            phone=options["phone"],
            password=options["password"],
        )

        user.organization = organization
        user.is_active = True
        user.is_superuser = True
        user.access_level = True
        user.save()

        self.stdout.write(self.style.SUCCESS('User created successfully'))
