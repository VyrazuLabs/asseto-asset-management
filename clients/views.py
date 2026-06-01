from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse

from .models import Client, ClientContact, STATUS_CHOICES
from .forms import ClientForm
from assets.models import Asset, AssetImage, AssignAsset
from audit.models import Audit
from collections import defaultdict

PAGE_SIZE = 10
ORPHANS = 1


def _base_qs(request):
    return Client.undeleted_objects.filter(
        organization=request.user.organization
    ).annotate(
        asset_count=Count('assets', filter=Q(assets__is_deleted=False))
    ).order_by('-created_at')


def _stats(request):
    qs = _base_qs(request)
    # Sum the annotated asset_count (calculated based on actual related Asset records)
    total_active_rentals = qs.aggregate(total=models.Sum('asset_count'))['total'] or 0
    return {
        'total_client_count':    qs.count(),
        'active_client_count':   qs.filter(status='1').count(),
        'review_client_count':   qs.filter(status='2').count(),
        'dormant_client_count':  qs.filter(status='3').count(),
        'inactive_client_count': qs.filter(status='0').count(),
        'active_rentals_count':  total_active_rentals,
        'deleted_client_count':  Client.deleted_objects.filter(organization=request.user.organization).count(),
    }


@login_required
def client_list(request):
    qs = _base_qs(request)
    
    # Filtering & Search
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status')
    
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(client_id__icontains=search))
    if status and status != 'All Statuses':
        qs = qs.filter(status=status)
        
    page_num = request.GET.get('page', 1)
    paginator = Paginator(qs, PAGE_SIZE, orphans=ORPHANS)
    page_object = paginator.get_page(page_num)

    context = {
        'sidebar': 'clients',
        'title': 'Client Directory | Asseto',
        'page_object': page_object,
        'status_choices': [s for s in STATUS_CHOICES if s[0] in ('1', '0')],
        'search_query': search,
        'selected_status': status,
        **_stats(request),
    }
    return render(request, 'clients/list.html', context)


@login_required
def add_client(request):
    from roles.models import Role
    
    form = ClientForm(organization=request.user.organization)
    roles = Role.objects.filter(organization=request.user.organization).order_by('name')
    
    if request.method == 'POST':
        form = ClientForm(request.POST, organization=request.user.organization)
        if form.is_valid():
            client = form.save(commit=False)
            client.organization = request.user.organization
            client.created_by = request.user.id
            client.save()
            
            contact_names = request.POST.getlist('contact_name[]')
            contact_emails = request.POST.getlist('contact_email[]')
            contact_phones = request.POST.getlist('contact_phone[]')
            contact_roles = request.POST.getlist('contact_role[]')
            contact_notes = request.POST.getlist('contact_notes[]')
            
            for i, name in enumerate(contact_names):
                name = name.strip()
                if name:
                    ClientContact.objects.create(
                        client=client,
                        name=name,
                        email=contact_emails[i].strip() if i < len(contact_emails) else '',
                        phone=contact_phones[i].strip() if i < len(contact_phones) else '',
                        role_id=contact_roles[i] if i < len(contact_roles) and contact_roles[i] else None,
                        notes=contact_notes[i].strip() if i < len(contact_notes) else ''
                    )
            
            messages.success(request, 'Client registered successfully.')
            return redirect('clients:list')

    context = {
        'sidebar': 'clients',
        'title': 'Register Client | Asseto',
        'form': form,
        'roles': roles,
    }
    return render(request, 'clients/add.html', context)


@login_required
def update_client(request, id):
    client = get_object_or_404(Client.undeleted_objects, pk=id,
                               organization=request.user.organization)
    form = ClientForm(instance=client, organization=request.user.organization)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client, organization=request.user.organization)
        if form.is_valid():
            client = form.save(commit=False)
            client.updated_by = request.user.id
            client.save()
            
            contact_names = request.POST.getlist('contact_name[]')
            contact_emails = request.POST.getlist('contact_email[]')
            contact_phones = request.POST.getlist('contact_phone[]')
            contact_roles = request.POST.getlist('contact_role[]')
            contact_notes = request.POST.getlist('contact_notes[]')
            
            client.contacts.all().delete()
            for i, name in enumerate(contact_names):
                name = name.strip()
                if name:
                    ClientContact.objects.create(
                        client=client,
                        name=name,
                        email=contact_emails[i].strip() if i < len(contact_emails) else '',
                        phone=contact_phones[i].strip() if i < len(contact_phones) else '',
                        role_id=contact_roles[i] if i < len(contact_roles) and contact_roles[i] else None,
                        notes=contact_notes[i].strip() if i < len(contact_notes) else ''
                    )
            
            messages.success(request, 'Client updated successfully.')
            return redirect('clients:list')

    from roles.models import Role
    roles = Role.objects.filter(organization=request.user.organization).order_by('related_name')
    
    context = {
        'sidebar': 'clients',
        'title': f'Edit {client.name} | Asseto',
        'form': form,
        'client': client,
        'roles': roles,
    }
    return render(request, 'clients/edit.html', context)


@login_required
def client_detail(request, id):
    client = get_object_or_404(Client.undeleted_objects, pk=id,
                               organization=request.user.organization)
    
    # Fetch related assets with pagination
    assets_qs = client.assets.filter(is_deleted=False).select_related('product__product_type', 'product__product_sub_category', 'location').prefetch_related('images').order_by('-created_at')

    asset_search = request.GET.get('asset_search', '').strip()
    if asset_search:
        assets_qs = assets_qs.filter(
            Q(tag__icontains=asset_search) | Q(name__icontains=asset_search)
        )

    assets_paginator = Paginator(assets_qs, 10, orphans=1)
    assets_page_number = request.GET.get('asset_page')
    assets_page_object = assets_paginator.get_page(assets_page_number)
    
    asset_ids = [a.id for a in assets_page_object]
    
    # Asset Images
    asset_images = {}
    for img in AssetImage.objects.filter(asset__organization=request.user.organization, asset_id__in=asset_ids).order_by('-uploaded_at'):
        if img.asset_id not in asset_images:
            asset_images[img.asset_id] = img

    # Asset User Map
    asset_user_map = {}
    for assign in AssignAsset.objects.select_related('user').filter(asset_id__in=asset_ids).order_by('-assigned_date'):
        if assign.asset_id not in asset_user_map:
            asset_user_map[assign.asset_id] = None
        if assign.user:
            asset_user_map[assign.asset_id] = {"full_name": assign.user.full_name, "image": assign.user.profile_pic}

    # Asset Conditions Map
    asset_conditions_map = defaultdict(list)
    for audit in Audit.objects.filter(asset_id__in=asset_ids):
        asset_conditions_map[audit.asset_id].append(audit.condition)

    # Calculate total asset value in Millions
    total_val = assets_qs.aggregate(total=models.Sum('price'))['total'] or 0
    total_asset_value = total_val / 1_000_000
    
    # Fetch History
    client_history = client.history.all()[:10]
    asset_history = Asset.history.filter(client=client)[:10]
    
    # Combine and sort history
    activities = []
    for h in client_history:
        h_type = h.get_history_type_display()
        if h_type == 'Created':
            action = 'Registration'
            notes = 'Initial registration of the client record.'
        elif h_type == 'Changed':
            action = 'Updated'
            notes = 'Client profile information was updated.'
        else:
            action = h_type
            notes = f'Client record {h_type.lower()}.'

        activities.append({
            'date': h.history_date,
            'user': h.history_user,
            'type': 'Client',
            'action': action,
            'notes': notes,
            'history_type': h.history_type,
        })

    for h in asset_history:
        h_type = h.get_history_type_display()
        action = 'Updated' if h_type == 'Changed' else h_type
        activities.append({
            'date': h.history_date,
            'user': h.history_user,
            'type': 'Asset',
            'action': action,
            'notes': f'Asset {h.tag} was {h_type.lower()}.',
            'history_type': h.history_type,
        })
    
    activities.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'sidebar': 'clients',
        'title': f'{client.name} | Asseto',
        'client': client,
        'assets_page_object': assets_page_object,
        'asset_images': asset_images,
        'asset_user_map': asset_user_map,
        'asset_conditions_map': asset_conditions_map,
        'asset_search': asset_search,
        'total_asset_value': total_asset_value,
        'activities': activities[:15],
    }
    return render(request, 'clients/detail.html', context)


@login_required
def delete_client(request, id):
    if request.method == 'POST':
        client = get_object_or_404(Client.undeleted_objects, pk=id,
                                   organization=request.user.organization)
        client.soft_delete()
        messages.success(request, 'Client deleted successfully.')
    return redirect('clients:list')


@login_required
def toggle_status(request, id):
    if request.method == 'POST' and request.user.is_superuser:
        client = get_object_or_404(Client.undeleted_objects, pk=id,
                                   organization=request.user.organization)
        client.status = '0' if client.status == '1' else '1'
        client.save()
    return HttpResponse(status=204)


@login_required
def search_clients(request, page):
    search_text = request.GET.get('search_text', '').strip()
    qs = _base_qs(request)
    if search_text:
        qs = qs.filter(
            Q(name__icontains=search_text) |
            Q(client_id__icontains=search_text) |
            Q(contacts__name__icontains=search_text) |
            Q(contacts__email__icontains=search_text) |
            Q(rental_type__icontains=search_text)
        ).distinct()
    paginator = Paginator(qs, PAGE_SIZE, orphans=ORPHANS)
    page_object = paginator.get_page(page)

    context = {
        'sidebar': 'clients',
        'page_object': page_object,
    }
    return render(request, 'clients/clients-data.html', context)
@login_required
def export_clients(request):
    import csv
    qs = _base_qs(request)
    
    # Apply filters from request
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status')
    
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(client_id__icontains=search))
    if status and status != 'All Statuses':
        qs = qs.filter(status=status)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="clients_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Client ID', 'Name', 'Industry', 'Contact Person', 'Email', 'Phone', 'Active Rentals', 'Open Tickets', 'Status'])
    
    for client in qs:
        first_contact = client.contacts.first()
        writer.writerow([
            client.client_id,
            client.name,
            client.industry,
            first_contact.name if first_contact else '',
            first_contact.email if first_contact else '',
            first_contact.phone if first_contact else '',
            client.active_rentals,
            client.open_tickets,
            client.get_status_display()
        ])
        
    return response
