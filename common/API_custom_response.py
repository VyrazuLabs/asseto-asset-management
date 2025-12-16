import os
import sys
import traceback
from rest_framework.response import Response

def api_response(success=True,status=200,data=None,message=None,validation_errors=None,error_message=None,
    error_type=None,error_location=None,system_message=None,trace_back=None):

    response = {
        "success": success,
        "status": status,
        "data": data,
        "message": message,
        "validation_errors": validation_errors,
        "error_type": error_type,
        "error_location": error_location,
        "error_message": error_message,
        "system_message": system_message,
        "trace_back": trace_back,
    }

    if status != 200:
        response["success"] = False

    if status == 500:
        response["error_message"] = "Something went wrong. Please try again later."

    response = {k: v for k, v in response.items() if v is not None}
    return Response(response, status=status)

def format_validation_errors(errors, model_cls=None):
    formatted = {}

    for field, error_list in errors.items():
        formatted[field] = {
            "errors": error_list,
            "field_type": (
                "model_field"
                if model_cls and hasattr(model_cls, field)
                else "custom_field"
            ),
        }

    return formatted

def get_detailed_errors_info(exception):
    exc_type, exc_value, exc_tb = sys.exc_info()
    frames = traceback.extract_tb(exc_tb)

    location = {
        "layer": "unknown",
        "file": None,
        "line": None,
        "function": None,
        "code": None,
    }

    # Walk from deepest frame
    for frame in reversed(frames):
        filename = os.path.basename(frame.filename)

        if "serializers" in filename:
            location["layer"] = "serializer"
        elif "models" in filename:
            location["layer"] = "model"
        elif "views" in filename or "api_views" in filename:
            location["layer"] = "api_view"
        else:
            continue

        location.update({
            "file": filename,
            "line": frame.lineno,
            "function": frame.name,
            "code": frame.line,
        })
        break

    return {
        "message": str(exception),
        "type": exc_type.__name__,
        "location": location,
        "traceback": traceback.format_exc(),
    }

def log_error_to_terminal(error_info):
    print("\n" + "=" * 60)
    print("ERROR OCCURRED")
    print(f"Type      : {error_info['type']}")
    print(f"Message   : {error_info['message']}")

    loc = error_info["location"]
    print("\n LOCATION")
    print(f"Layer     : {loc['layer']}")
    print(f"File      : {loc['file']}")
    print(f"Function  : {loc['function']}")
    print(f"Line      : {loc['line']}")
    print(f"Code      : {loc['code']}")

    print("\TRACEBACK")
    print(error_info["traceback"])
    print("=" * 60 + "\n")

