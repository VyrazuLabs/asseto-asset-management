from django.utils import timezone
from .models import Audit

def perform_auditing():
    print(f"[{timezone.now()}] Running scheduled cleanup...")
    
