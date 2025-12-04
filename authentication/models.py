import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Permission
from django.contrib.contenttypes.models import ContentType
from dashboard.models import Organization, Location, Address, Department, TimeStampModel, SoftDeleteModel
from django.conf import settings
from roles.models import Role
import os
from uuid import uuid4
from django_resized import ResizedImageField
from simple_history.models import HistoricalRecords
from configurations.models import LocalizationConfiguration
from configurations.constants import NAME_FORMATS


def path_and_rename(instance, filename):
    upload_to = 'profile/'
    ext = filename.split('.')[-1]
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        filename = '{}.{}'.format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)

class UserManager(BaseUserManager):

    def create_user(self, email, full_name, username, phone, password, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address.')
        user = self.model(email=self.normalize_email(email), full_name=full_name,username=username, phone=phone, **extra_fields)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user

    def create_superuser(self, email, full_name, username, phone, password, **extra_fields):
        user = self.create_user(email, full_name, username, phone, password, is_active = True, access_level=True, **extra_fields)
        
        # Create or get the Superuser default
        organization = Organization.objects.filter(name='DjangoSuperUserOrganization').first()
        if not organization:
            organization = Organization.objects.create(name='DjangoSuperUserOrganization')
        

        role = Role.objects.filter(related_name='Superuser', organization=organization).first()
        if not role:
            role = Role.objects.create(
                name = "all_permissions",
                related_name='Superuser',
                organization=organization
            )

        if role.permissions.count() == 0:
            all_permisisons = Permission.objects.all()
            for permission in all_permisisons:
                role.permissions.add(permission)
        role.save()


        user.role = role
        user.save(using=self._db)

        return user

BOOL_CHOICES = ((False, 'Only Assigned'), (True, 'All'))

class User(AbstractBaseUser, PermissionsMixin, TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=255 , blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    profile_pic = ResizedImageField(upload_to=path_and_rename, blank=True, null=True)
    employee_id = models.CharField(max_length=45, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    address = models.ForeignKey(Address, models.DO_NOTHING, blank=True, null=True)
    location = models.ForeignKey(Location, models.DO_NOTHING, blank=True, null=True)
    department = models.ForeignKey(Department, models.DO_NOTHING, blank=True, null=True)
    access_level = models.BooleanField(choices=BOOL_CHOICES,default=False)
    role = models.ForeignKey(Role, models.DO_NOTHING, related_name='role', blank=True, null=True)
    objects = UserManager()
    history = HistoricalRecords()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone', 'username']  

    def dynamic_display_name(self, fullname):
        # Normalize fullname
        fullname = (fullname or "").strip()
        if not fullname:
            return ""

        # Get organization's configured format key (safe)
        format_key_value = None
        try:
            config = LocalizationConfiguration.objects.filter(
                organization=self.organization
            ).values_list("name_display_format", flat=True).first()
            format_key_value = config
        except Exception:
            format_key_value = None

        # coerce to int safely, fallback to 0
        try:
            format_key = int(format_key_value) if format_key_value is not None else 0
        except (ValueError, TypeError):
            format_key = 0

        # Convert NAME_FORMATS list to dict for lookup
        formats_map = dict(NAME_FORMATS)

        # prepare name parts
        parts = fullname.split()
        first = parts[0] if parts else ""
        last = parts[-1] if len(parts) > 1 else ""
        first_initial = (first[0].upper() if first else "")

        context = {
            "first": first,
            "last": last,
            "first_initial": first_initial,
        }

        fmt = formats_map.get(format_key, formats_map.get(0, "{first} {last}"))
        try:
            result = fmt.format(**context).strip()
        except Exception:
            # final fallback to "First Last" or fullname if that's all we have
            if first and last:
                result = f"{first} {last}"
            else:
                result = first or last or fullname    
        return result

    def __str__(self):
        return self.full_name or f'Role {self.role}' or " "
    
    @property
    def reverse_full_name(self):
        if self.full_name:
            return self.dynamic_display_name(self.full_name)
        return ""

class SeedFlag(models.Model):
    seeded=models.BooleanField(default=False)

    def __str__(self):
        return "Seed already done" if self.seeded else "Seed not done yet"