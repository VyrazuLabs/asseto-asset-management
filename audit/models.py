from django.db import models
from assets.models import Asset
from authentication.models import Organization, User
from assets.models import AssetImage

class Audit(models.Model):
    CONDITION_CHOICES = [
        (0, 'Excellent'),
        (1, 'Good'),
        (2, 'Fair'),
        (3, 'Bad'),
        (4, 'Retired')
    ]
    image=models.ForeignKey(AssetImage, null=True, blank=True, on_delete=models.CASCADE)
    assigned_to = models.CharField(max_length=150,blank=True, null=True)
    asset = models.ForeignKey(Asset, null=True, blank=True, related_name='audits', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, null=True, on_delete=models.CASCADE)
    condition = models.IntegerField(choices=CONDITION_CHOICES, default=0)
    notes = models.TextField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    audited_by=models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    def condition_label(self):
        print("yo",dict(self.CONDITION_CHOICES).get(self.condition))
        return dict(self.CONDITION_CHOICES).get(self.condition)