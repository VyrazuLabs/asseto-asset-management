from .models import CustomFieldDefinition, CustomFieldValue

def get_definitions_for_module(organization, module):
    """Returns active field definitions for the given org + module."""
    if not organization:
        return CustomFieldDefinition.objects.none()
    return CustomFieldDefinition.objects.filter(
        organization=organization,
        module=module,
        is_active=True,
        is_deleted=False,
    ).order_by("field_label")


def get_values_for_entity(entity_uuid, definitions):
    """
    Returns dict of {field_key: value_text} for an entity.
    Call after get_definitions_for_module().
    """
    if not entity_uuid or not definitions:
        return {}
    defn_ids = [d.id for d in definitions]
    values_qs = CustomFieldValue.objects.filter(
        definition_id__in=defn_ids,
        entity_uuid=entity_uuid,
    ).select_related("definition")
    return {v.definition.field_key: v.value_text for v in values_qs}


def _validate_field_value(definition, raw_value):
    """
    Server-side type validation (second layer after HTML5 frontend validation).
    Returns (is_valid: bool, error_message: str|None).
    """
    if not raw_value:
        return True, None
    ftype = definition.field_type
    try:
        if ftype == "integer":
            int(raw_value)
        elif ftype == "decimal":
            float(raw_value)
        elif ftype == "date":
            from datetime import datetime
            datetime.strptime(raw_value, "%Y-%m-%d")
        elif ftype == "boolean":
            if str(raw_value).lower() not in ("true", "false", "1", "0", "on", "off"):
                raise ValueError
        elif ftype == "email":
            from django.core.validators import validate_email
            validate_email(raw_value)
    except Exception:
        return False, f"'{raw_value}' is not a valid {definition.field_type} for field '{definition.field_label}'."
    return True, None


def validate_cf_values(request, module):
    """
    Validates submitted custom field values for a module (without saving).
    Returns list of error strings (empty list = all values valid).
    """
    org = request.user.organization
    definitions = get_definitions_for_module(org, module)
    errors = []
    for defn in definitions:
        raw_value = request.POST.get(f"cf_{defn.field_key}", "").strip()
        # Required check
        if defn.is_required and not raw_value:
            errors.append(f"'{defn.field_label}' is required.")
            continue
        # Type check (server-side)
        if raw_value:
            valid, err = _validate_field_value(defn, raw_value)
            if not valid:
                errors.append(err)
    return errors


def validate_cf_values_dict(organization, module, values):
    """
    Dict-based counterpart to ``validate_cf_values`` for JSON API bodies.

    ``values`` is a plain ``{field_key: raw_value}`` dict (e.g. a parsed
    request body) rather than ``request.POST`` — lets DRF serializers pass
    parsed JSON straight through without a form/POST round-trip.
    Returns list of error strings (empty list = all values valid).
    """
    definitions = get_definitions_for_module(organization, module)
    errors = []
    for defn in definitions:
        raw_value = str(values.get(defn.field_key, "") or "").strip()
        if defn.is_required and not raw_value:
            errors.append(f"'{defn.field_label}' is required.")
            continue
        if raw_value:
            valid, err = _validate_field_value(defn, raw_value)
            if not valid:
                errors.append(err)
    return errors


def save_values_for_entity_dict(organization, entity_uuid, module, values):
    """
    Dict-based counterpart to ``save_values_for_entity`` for JSON API bodies.

    ``values`` is a plain ``{field_key: raw_value}`` dict. Validates first
    (via ``validate_cf_values_dict``); upserts/deletes ``CustomFieldValue``
    rows only when validation passes. Returns list of error strings (empty
    list = all good, values saved).
    """
    errors = validate_cf_values_dict(organization, module, values)
    if errors:
        return errors
    definitions = get_definitions_for_module(organization, module)
    for defn in definitions:
        raw_value = str(values.get(defn.field_key, "") or "").strip()
        if raw_value:
            CustomFieldValue.objects.update_or_create(
                definition=defn,
                entity_uuid=entity_uuid,
                defaults={"value_text": raw_value},
            )
        else:
            CustomFieldValue.objects.filter(
                definition=defn,
                entity_uuid=entity_uuid,
            ).delete()
    return errors


def save_values_for_entity(request, entity_uuid, module):
    """
    Reads POST data with keys `cf_<field_key>`.
    Layer 1 (HTML5 type attr) runs in browser.
    Layer 2 (this function) validates server-side before saving.
    Upserts CustomFieldValue rows.
    Returns list of error strings (empty list = all good).
    """
    errors = validate_cf_values(request, module)
    if errors:
        return errors
    org = request.user.organization
    definitions = get_definitions_for_module(org, module)
    for defn in definitions:
        raw_value = request.POST.get(f"cf_{defn.field_key}", "").strip()
        if raw_value:
            CustomFieldValue.objects.update_or_create(
                definition=defn,
                entity_uuid=entity_uuid,
                defaults={"value_text": raw_value},
            )
        else:
            CustomFieldValue.objects.filter(
                definition=defn,
                entity_uuid=entity_uuid,
            ).delete()
    return errors
