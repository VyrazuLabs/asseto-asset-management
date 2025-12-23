import os
import sys
import traceback
from rest_framework.response import Response
from django.conf import settings
import traceback
import structlog
import sys

def get_traceback(show_locals=True) -> list[dict[str]]:
    """Returns relevant traceback information in JSON Format.

    This function can also be used to debug wherever necessary, 
    you only need to make sure that an exception gets called first.
    
    Reference: https://gitlab.com/-/snippets/2284049
    """

    exc_info = sys.exc_info()

    trace = structlog.tracebacks.extract(
            *exc_info, 
            show_locals=(settings.TRACEBACK_SHOW_LOCALS and show_locals),
            locals_max_string=settings.TRACEBACK_LOCALS_MAX_LENGTH
        )

    for stack in trace.stacks:
        if len(stack.frames) <= 50:
            continue

        half = 50 // 2
        fake_frame = structlog.tracebacks.Frame(
            filename="",
            lineno=-1,
            name=f"Skipped frames: {len(stack.frames) - (2 * half)}",
        )
        stack.frames[:] = [*stack.frames[:half], fake_frame, *stack.frames[-half:]]

    stack_dicts = [
        {
            'exc_type': stack.exc_type,
            'exc_value': stack.exc_value,
            'syntax_error': stack.syntax_error,
            'is_cause': stack.is_cause,
            'frames': [
                {
                    'filename': frame.filename,
                    'lineno': frame.lineno,
                    'name': frame.name,
                    'locals': frame.locals,
                }

                for frame in stack.frames
            ],
        }

        for stack in trace.stacks
    ]

    return stack_dicts

def api_response(success=True,status=200,data=None,message=None,validation_errors=None,error_message=None,
    error_type=None,error_location=None,system_message=None,trace_back=None,include_traceback=True):
 
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
    if (
        include_traceback
        and trace_back is None
        and status >= 500):
        try:
            trace_back = get_traceback()
        except Exception:
            trace_back = None 
 
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
