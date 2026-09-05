from django.db import migrations

# Gate Pass, Audit and Configurations were open to any logged-in user before
# this migration (zero or partial @permission_required gating). Without
# grandfathering, every existing non-superuser role would lose access the
# instant the new decorators ship — see the RBAC overhaul plan's Phase 4
# lockout mitigation.
GRANDFATHER_PERMISSIONS = {
    ("gate_pass", "gatepass"): [
        "view_gate_pass",
        "add_gate_pass",
        "edit_gate_pass",
        "delete_gate_pass",
        "authorise_gate_pass",
        "checkout_gate_pass",
    ],
    ("audit", "audit"): [
        "view_audit",
        "add_audit",
        "edit_audit",
        "delete_audit",
    ],
    ("configurations", "configurationpermission"): [
        "view_configuration",
        "add_configuration",
        "edit_configuration",
        "delete_configuration",
    ],
}


def grandfather_existing_roles(apps, schema_editor):
    """Grant every existing Role full access to the newly-gated modules.

    Args:
        apps: Historical app registry supplied by the migration framework.
        schema_editor: Unused; required by RunPython's signature.
    """
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    Role = apps.get_model("roles", "Role")

    permissions = []
    for (app_label, model_name), codenames in GRANDFATHER_PERMISSIONS.items():
        # get_or_create, not get: on a fresh database the contenttypes
        # post_migrate signal only creates rows for an app's models after
        # ALL migrations finish, so a mid-migration lookup here can run
        # before it exists yet.
        content_type, _ = ContentType.objects.get_or_create(app_label=app_label, model=model_name)
        for codename in codenames:
            permission, _ = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={"name": f"Can {codename.replace('_', ' ')}"},
            )
            permissions.append(permission)

    for role in Role.objects.all():
        role.permissions.add(*permissions)


def noop_reverse(apps, schema_editor):
    """Deliberately not reversible.

    Stripping grandfathered permissions on rollback could remove access a
    role legitimately still needs by then; revert manually via the Role
    editor instead.
    """


class Migration(migrations.Migration):

    dependencies = [
        ("roles", "0004_alter_role_created_at_alter_role_status_and_more"),
        ("gate_pass", "0003_alter_gatepass_status"),
        ("audit", "0001_initial"),
        ("configurations", "0010_configurationpermission"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(grandfather_existing_roles, noop_reverse),
    ]
