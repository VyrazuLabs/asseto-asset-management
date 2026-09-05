from django.db import models


class RecycleBinPermission(models.Model):
    """Unmanaged anchor model for Recycle Bin permissions.

    Recycle Bin is a cross-cutting view over several soft-deleted models
    (vendors, products, assets, users, locations, departments, ...) with no
    single real model of its own. This model exists purely so
    ``ContentType.objects.get_for_model()`` has a stable, real target for
    the "view_recycle_bin" / "restore_recycle_bin" / "delete_recycle_bin"
    permissions — it has no database table and is never queried.
    See ``common/permissions.py`` for the module registry.
    """

    class Meta:
        managed = False
        default_permissions = ()
