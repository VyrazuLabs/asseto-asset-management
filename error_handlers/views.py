from django.shortcuts import render


def handle_403(request, exception):
    return render(request, 'error_handlers/error-403.html')

def handle_404(request, exception):
    return render(request, 'error_handlers/error-404.html')

def handle_500(request):
    return render(request, 'error_handlers/error-500.html')