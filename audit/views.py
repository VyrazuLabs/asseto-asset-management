from django.shortcuts import render,redirect,get_object_or_404
from .models import Audit,AuditImage
from .forms import AuditForm,AuditImageForm
from django.core.paginator import Paginator
from assets.models import AssignAsset,Asset
from authentication.models import User
from audit.utils import is_pending_audit,is_upcoming_audit
from datetime import datetime,timedelta,timezone

PAGE_SIZE = 10
ORPHANS = 1

# Create your views here.
# def add_audit(request):
#     id=request.GET.get('id',None)
#     tag_id=request.GET.get('tag',None)
#     image_id=request.GET.get('image',None)
#     condition_choice=request.GET.get('condition',None) #get the condition integer
#     assigned_to=request.GET.get('assigned-to',None)
#     comments=request.GET.get('comments',None)

#     get_asset=Asset.objects.filter(id=tag_id).first()
#     if request.method == 'POST':
#         Audit.objects.create(asset=get_asset,organization=request.user.organization,condition=condition_choice,notes=comments,assigned_to=assigned_to)
#         return redirect('assets:list')
#     elif request.method == 'GET':
#         user_list = [assign.user for assign in AssignAsset.objects.all() if assign.user is not None]
#         form = AuditForm()
#         get_audit=None
#         if id is not None:
#             get_audit=Audit.objects.filter(id=id).first()
#         context={'get_audit':get_audit,'assigned_users': user_list}
#         return render(request, 'assets/add_audit.html',context=context)
def add_audit(request):
    id = request.GET.get('id', None)
    get_audit = Audit.objects.filter(id=id).first() if id else None
    notes=request.POST.get('comments',None)
    tag=request.POST.get('tag',None)
    get_asset=Asset.objects.filter(tag=tag).first()
    
    if request.method == 'POST':
        form = AuditForm(request.POST, request.FILES, organization=request.user.organization)
        if form.is_valid():
            print(form.data)
            audit = form.save(commit=False)
            audit.asset=get_asset
            audit.organization = request.user.organization
            audit.audited_by = request.user  # save current user as auditor
            audit.notes = notes
            # condition is handled by form field, no manual overwrite needed unless required
            audit.save()
            form.save_m2m()

            for f in request.FILES.getlist('image'):
                AuditImage.objects.create(audit=audit, image=f)

            return redirect('assets:list')

    if request.method == 'GET':
        user_list = [assign for assign in User.undeleted_objects.all() if assign is not None]
        print(user_list)
        context = {'get_audit': get_audit, 'assigned_users': user_list}
        return render(request, 'assets/add_audit.html', context)

    # else:
    #     form = AuditForm(organization=request.user.organization)
    #     context = {'get_audit': get_audit, 'form': form}
    #     return render(request, 'assets/add_audit.html', context)

def get_audits_by_id(request, id):
    get_asset = get_object_or_404(Asset, id=id)
    get_assigned_user = AssignAsset.objects.filter(asset__id=id).first()

    if request.method == 'POST':
        comments = request.POST.get('comments', None)
        condition = request.POST.get('condition', None)

        audit, created = Audit.objects.update_or_create(
            asset=get_asset,
            defaults={
                'condition': condition,
                'notes': comments,
                'audited_by': request.user if request.user.is_authenticated else None,
                'created_at': datetime.now(),
            }
        )
        print("Audit created" if created else "Audit updated", audit.id)

        return render(request, 'assets/add_audit.html', {'get_asset': get_asset, 'message': 'Audit saved successfully!'})

    elif request.method == 'GET':
        if get_assigned_user is None:
            user_list = list(User.undeleted_objects.all())
            context = {'get_asset': get_asset, 'assigned_users': user_list}
        else:
            context = {'get_asset': get_asset, 'asset_assigned_users': get_assigned_user.user.full_name}

        return render(request, 'assets/add_audit.html', context)

def audit_list(request):
    audits = Audit.objects.all()
    return render(request, 'assets/audit_list.html',context={
        'audits': audits
    })


# def upcoming_audits(request):
#     audits = Audit.objects.all()
#     upcoming = [a for a in audits if is_upcoming_audit(a)]
#     print(upcoming)
#     return render(request, 'assets/audit_list.html',context={
#         'audits': upcoming
#     })

def asset_audit_history(request,id):
    audit_list = Audit.objects.filter(asset__id=id).order_by('-created_at')
    paginator = Paginator(audit_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'assets',
        'submenu': 'assigned-assets',
        'page_object': page_object,
        'title': 'Assigned Assets'
    }
    return render(request, 'assets/asset-audit-history.html', context=context)

def completed_audits(request):
    thirty_days_ago = datetime.now() - timedelta(days=30)
    audits = Audit.objects.filter(
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')
    return render(request, 'assets/audit_list.html', {
        'audits': audits
    })

def pending_audits(request):
    audit = Audit.objects.all().values('asset')
    print(audit)
    for it in audit:
        print(it['asset'])
    get_remaining_assets = Asset.objects.exclude(id__in=audit.values('asset'))
    print(get_remaining_assets)
    # pending = [a for a in audits if is_pending_audit(a)]
    # print(pending)
    return render(request, 'assets/pending_audits.html',context={
        'audits': get_remaining_assets
    })