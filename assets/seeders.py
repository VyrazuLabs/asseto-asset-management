from assets.models import AssetStatus
from dashboard.models import ProductType
from authentication.models import SeedFlag

def seed_asset_statuses(organization=None):
    default_statuses = ['Broken ', ' Ready To Deploy ', 'Assigned', 'Lost/Stolen','Repair Required','Out for Repair','Available']
    default_types=['Consumeables','Accesories']
    for status in default_statuses:
            AssetStatus.objects.get_or_create(
            name=status.strip(),
            organization=organization,
            defaults={'can_modify': False}
        )
    for type in default_types:
            ProductType.objects.get_or_create(
                name=type.strip(),
                organization=organization,
                defaults={'can_modify': False}
            )

    SeedFlag.objects.create(seeded=True)





def seed_asset_statuses(asset=None, product=None, organization=None):
    default_statuses = ['Broken ', ' Ready To Deploy ', 'Assigned', 'Lost/Stolen','Repair Required','Out for Repair','Available']
    default_types=['Consumeables','Accesories']
    if asset:
        for status in default_statuses:
                AssetStatus.objects.get_or_create(
                name=status.strip(),
                organization=organization,
                defaults={'can_modify': False}
        )

    if product:
        for type in default_types:
                ProductType.objects.get_or_create(
                    name=type.strip(),
                    organization=organization,
                    defaults={'can_modify': False}
                )

    SeedFlag.objects.create(seeded=True)
    return True