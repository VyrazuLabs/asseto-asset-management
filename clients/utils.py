from django.template.loader import get_template
from django.http import HttpResponse
from django.db.models import Count
from django.db.models import Q
import csv
from io import BytesIO
from xhtml2pdf import pisa
from datetime import date

from .models import Client


def export_clients_csv_utils(request):
    today = date.today()
    qs = Client.undeleted_objects.filter(
        organization=request.user.organization
    ).annotate(
        asset_count=Count('assets', filter=Q(assets__is_deleted=False))
    ).order_by('-created_at')

    search = request.GET.get('search', '').strip()
    status = request.GET.get('status')
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(client_id__icontains=search))
    if status and status != 'All Statuses':
        qs = qs.filter(status=status)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="export-clients-{today}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Client ID', 'Name', 'Industry', 'Contact Person', 'Email', 'Phone', 'Total Assets', 'Open Tickets', 'Status'])

    for client in qs:
        first_contact = client.contacts.first()
        writer.writerow([
            client.client_id,
            client.name,
            client.industry_name,
            first_contact.name if first_contact else '',
            first_contact.email if first_contact else '',
            first_contact.phone if first_contact else '',
            client.asset_count,
            client.open_tickets,
            client.get_status_display()
        ])

    return response


def export_clients_pdf_utils(request):
    today = date.today()
    clients = Client.undeleted_objects.filter(
        organization=request.user.organization
    ).annotate(
        asset_count=Count('assets', filter=Q(assets__is_deleted=False))
    ).order_by('-created_at')

    search = request.GET.get('search', '').strip()
    status = request.GET.get('status')
    if search:
        clients = clients.filter(Q(name__icontains=search) | Q(client_id__icontains=search))
    if status and status != 'All Statuses':
        clients = clients.filter(status=status)

    context = {'clients': clients}
    template = get_template('clients/clients-pdf.html')
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="export-clients-{today}.pdf"'
        return response
    return HttpResponse(status=500)
