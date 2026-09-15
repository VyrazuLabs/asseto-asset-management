from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Consumable


@receiver(post_save, sender=Consumable)
def consumable_post_save(sender, instance, created, **kwargs):
    pass


@receiver(post_delete, sender=Consumable)
def consumable_post_delete(sender, instance, **kwargs):
    pass
