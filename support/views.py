from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.http import HttpResponse, JsonResponse
import csv
from django.db.models import Q

from .models import *
from .forms import SupportTicketForm, TicketNoteForm
from assets.models import Asset, AssetImage
from authentication.models import User

def check_admin(user):
    return user.is_superuser



# Helper Functions
def _ticket_base_qs(request):
    """Base queryset filtered by org, excludes soft-deleted."""
    return SupportTicket.undeleted_objects.filter(
        organization=request.user.organization
    ).select_related('asset', 'assigned_to').order_by('-created_at')

def _ticket_stats(request):
    """Compute stat card values."""
    qs = _ticket_base_qs(request)
    return {
        'total_active': qs.exclude(status='4').count(),
        'pending_parts': qs.filter(status='0', ticket_type='hardware_repair').count(),
        'overdue_count': qs.filter(status='0', estimated_eta__lt=now()).count(),
        'critical_count': qs.filter(priority__in=['3', '2'], status='0').count(),
    }

@login_required
def ticket_list(request):
    qs = _ticket_base_qs(request)
    
    # Filtering & Search
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    ticket_type = request.GET.get('ticket_type')
    
    if search:
        qs = qs.filter(
            Q(ticket_id__icontains=search) |
            Q(subject__icontains=search) |
            Q(asset__name__icontains=search) |
            Q(assigned_to__full_name__icontains=search)
        )
    if status: qs = qs.filter(status=status)
    if priority: qs = qs.filter(priority=priority)
    if ticket_type: qs = qs.filter(ticket_type=ticket_type)
    
    qs = qs.order_by('-created_at')
    
    paginator = Paginator(qs, 10, orphans=1)
    page_object = paginator.get_page(request.GET.get('page', 1))
    
    asset_images = {}
    for ticket in page_object:
        if ticket.asset:
            asset_images[ticket.asset.id] = ticket.asset.images.first()
    
    context = {
        'sidebar': 'support',
        'title': 'Maintenance Tickets | Asseto',
        'page_object': page_object,
        'all_tickets': qs,  # For Kanban view
        'status_choices': STATUS_CHOICES,
        'priority_choices': PRIORITY_CHOICES,
        'ticket_type_choices': TICKET_TYPE_CHOICES,
        'asset_images': asset_images,
        **_ticket_stats(request),
    }
    return render(request, 'support/ticket_list.html', context)

@login_required
def add_ticket(request):
    form = SupportTicketForm(organization=request.user.organization)
    
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, request.FILES, organization=request.user.organization)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.organization = request.user.organization
            ticket.created_by = str(request.user.id)
            ticket.save()
            
            # Handle file uploads
            for f in request.FILES.getlist('attachments'):
                TicketAttachment.objects.create(
                    ticket=ticket, file=f,
                    file_name=f.name, file_size=f.size,
                    uploaded_by=request.user
                )
            
            # Create initial activity
            TicketActivity.objects.create(
                ticket=ticket, activity_type='created',
                description=f'Ticket initiated by {request.user.get_full_name()}.',
                performed_by=request.user
            )
            
            messages.success(request, 'Ticket created successfully.')
            return redirect('support:ticket_list')
    
    context = {
        'sidebar': 'support',
        'title': 'New Support Request | Asseto',
        'form': form,
    }
    return render(request, 'support/ticket_add.html', context)

@login_required
def ticket_detail(request, id):
    ticket = get_object_or_404(
        SupportTicket.undeleted_objects.select_related(
            'asset', 'assigned_to', 'department', 'location'
        ), pk=id, organization=request.user.organization
    )
    
    from django.core.paginator import Paginator
    history_qs = ticket.history.all().order_by('-history_date')
    paginator = Paginator(history_qs, 10, orphans=1)
    page_object = paginator.get_page(request.GET.get('page', 1))
    
    context = {
        'sidebar': 'support',
        'title': f'{ticket.subject} | Asseto',
        'ticket': ticket,
        'attachments': ticket.attachments.order_by('-created_at'),
        'page_object': page_object,
    }
    return render(request, 'support/ticket_detail.html', context)

@login_required
def update_ticket(request, id):
    ticket = get_object_or_404(SupportTicket.undeleted_objects, pk=id,
                               organization=request.user.organization)
    old_status = ticket.status
    old_assigned = ticket.assigned_to
    form = SupportTicketForm(instance=ticket, organization=request.user.organization)
    
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, instance=ticket, organization=request.user.organization)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.updated_by = str(request.user.id)
            ticket.save()
            
            # Log status change
            if old_status != ticket.status:
                TicketActivity.objects.create(
                    ticket=ticket, activity_type='status_changed',
                    description=f'Status changed from {old_status} to {ticket.status}.',
                    performed_by=request.user
                )
            
            # Log reassignment
            if old_assigned != ticket.assigned_to:
                desc = f'Ticket assigned to {ticket.assigned_to.get_full_name()}.' if ticket.assigned_to else 'Ticket unassigned.'
                TicketActivity.objects.create(
                    ticket=ticket, activity_type='reassigned',
                    description=desc,
                    performed_by=request.user
                )
            
            # Handle note/comment
            note_content = request.POST.get('note_content', '').strip()
            if note_content:
                is_internal = request.POST.get('is_internal') == 'on'
                TicketActivity.objects.create(
                    ticket=ticket,
                    activity_type='internal_note' if is_internal else 'comment',
                    description=note_content,
                    is_internal=is_internal,
                    performed_by=request.user
                )
            
            # Handle new file uploads
            for f in request.FILES.getlist('attachments'):
                TicketAttachment.objects.create(
                    ticket=ticket, file=f,
                    file_name=f.name, file_size=f.size,
                    uploaded_by=request.user
                )
            
            messages.success(request, 'Ticket updated successfully.')
            return redirect('support:ticket_list')
    
    context = {
        'sidebar': 'support',
        'title': f'Edit {ticket.subject} | Asseto',
        'form': form,
        'ticket': ticket,
        'activities': ticket.activities.order_by('-created_at')[:20],
    }
    return render(request, 'support/ticket_edit.html', context)

@login_required
def delete_ticket(request, id):
    ticket = get_object_or_404(SupportTicket.undeleted_objects, pk=id,
                               organization=request.user.organization)
    if request.method == 'POST':
        ticket.soft_delete()
        messages.success(request, 'Ticket deleted successfully.')
    return redirect('support:ticket_list')

@login_required
def search_tickets(request, page):
    qs = _ticket_base_qs(request)
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    ticket_type = request.GET.get('ticket_type')
    
    if search:
        qs = qs.filter(
            Q(ticket_id__icontains=search) |
            Q(subject__icontains=search) |
            Q(asset__name__icontains=search) |
            Q(assigned_to__full_name__icontains=search)
        )
    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    if ticket_type:
        qs = qs.filter(ticket_type=ticket_type)
    
    qs = qs.order_by('-created_at')
    
    paginator = Paginator(qs, 10, orphans=1)
    page_object = paginator.get_page(page)
    
    asset_images = {}
    for ticket in page_object:
        if ticket.asset:
            asset_images[ticket.asset.id] = ticket.asset.images.first()
    
    return render(request, 'support/tickets-data.html', {'page_object': page_object, 'asset_images': asset_images})

@login_required
def export_tickets(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tickets.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Ticket ID', 'Subject', 'Asset', 'Priority', 'Status', 'Assigned To', 'Created At'])
    
    for ticket in _ticket_base_qs(request):
        writer.writerow([
            ticket.ticket_id,
            ticket.subject,
            ticket.asset.name if ticket.asset else '',
            ticket.priority,
            ticket.status,
            ticket.assigned_to.get_full_name() if ticket.assigned_to else 'Unassigned',
            ticket.created_at
        ])
    
    return response
@login_required
def delete_ticket_attachment(request, id):
    attachment = get_object_or_404(TicketAttachment, id=id, ticket__organization=request.user.organization)
    ticket_id = attachment.ticket.id
    attachment.delete()
    messages.success(request, 'Attachment deleted successfully.')
    return redirect('support:ticket_update', id=ticket_id)

@login_required
def asset_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        assets = Asset.undeleted_objects.filter(organization=request.user.organization).order_by('-created_at')[:10]
    else:
        assets = Asset.undeleted_objects.filter(
            Q(organization=request.user.organization),
            Q(name__icontains=query) | Q(tag__icontains=query) | Q(serial_no__icontains=query)
        )[:10]
    
    results = []
    for asset in assets:
        results.append({
            'id': str(asset.id),
            'name': asset.name,
            'tag': asset.tag,
        })
    
    return JsonResponse({'results': results})

@login_required
def technician_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        users = User.objects.filter(organization=request.user.organization).order_by('full_name')[:10]
    else:
        users = User.objects.filter(
            Q(organization=request.user.organization),
            Q(full_name__icontains=query) | Q(email__icontains=query)
        )[:10]
    
    results = []
    for user in users:
        results.append({
            'id': str(user.id),
            'full_name': user.get_full_name(),
            'email': user.email,
        })
    
    return JsonResponse({'results': results})
