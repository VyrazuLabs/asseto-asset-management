from dashboard.models import ProductCategory
from authentication.models import SeedFlag

def seed_parent_category(organization=None):
    default_parent_category = ['Root']
    for category in default_parent_category:
            ProductCategory.objects.get_or_create(
            name=category.strip(),
            organization=organization,
        )

    SeedFlag.objects.create(seeded=True)




def seed_parent_category(category=None, organization=None):
    default_parent_category = ['Root']
    if category:
        for category in  default_parent_category:
               ProductCategory.objects.get_or_create(
                name=category.strip(),
                organization=organization,
        )



    SeedFlag.objects.create(seeded=True)
    return True