from django.http import HttpResponse


def index(request):
    """Proves the extension's URLs are wired and reachable after a reload."""
    return HttpResponse("sample_extension: pong")
