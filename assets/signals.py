from django.apps import AppConfig
from authentication.models import User
from django.db.models.signals import post_save 
from django.dispatch import receiver
from.seeders import seed_asset_statuses
from authentication.models import SeedFlag
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def trigger_seed_on_first_superuser(sender,instance,created,**kwargs):
        if created and instance.is_superuser:
            
            if not SeedFlag.objects.exists():  # Only seed once
                seed_asset_statuses()
