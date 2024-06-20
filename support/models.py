from django.db import models

# Create your models here.

class Support(models.Model):
    question = models.CharField(max_length = 250, blank = False, null = False)
    answer = models.TextField(blank = False, null = False)
    
    
    class Meta:
        db_table = "support"
