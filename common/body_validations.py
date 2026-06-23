def validate_body(fields, arguments):
    errors = {}
    for key, value in fields.items():
        if value.get("required") and not arguments.get(key):
            errors[key] = "This field is required"
            continue
    return errors
