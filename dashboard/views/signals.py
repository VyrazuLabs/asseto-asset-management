from django.apps import AppConfig
from authentication.models import User
from django.db.models.signals import post_save 
from django.dispatch import receiver
from.seeders import seed_parent_category
from authentication.models import SeedFlag

@receiver(post_save, sender=User)
def trigger_seed_on_first_superuser(sender,instance,created,**kwargs):
        if created and instance.is_superuser:
            
            if not SeedFlag.objects.exists():  # Only seed once
                seed_parent_category()