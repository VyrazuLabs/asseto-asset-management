from django.shortcuts import render,redirect,get_object_or_404
from .models import Audit
from assets.models import AssetImage
from .forms import AuditForm
from django.core.paginator import Paginator
from assets.models import AssignAsset,Asset
from authentication.models import User
from audit.utils import next_audit_due
from datetime import datetime,timedelta,timezone 
from django.http import JsonResponse

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
        # image_form = AssetImageForm(request.POST, request.FILES)
        if form.is_valid():
            print(form.data)
            image_instance=None
            audit = form.save(commit=False)
            audit.asset=get_asset
            audit.organization = request.user.organization
            audit.audited_by = request.user  # save current user as auditor
            audit.notes = notes
            files=request.FILES.getlist('image')
            print("files'''''''",files)
            if not files:
                file = request.FILES.get("image")
                print("file",file)
                if file:
                    files = [file]
            for f in files:
                image_instance = AssetImage.objects.create(asset=audit.asset, image=f)

            audit.image = image_instance  # Link the last uploaded image to the audit
            # condition is handled by form field, no manual overwrite needed unless required
            audit.save()
            form.save_m2m()
            return redirect('audit:completed_audits')

    if request.method == 'GET':
        user_list = [assign for assign in User.undeleted_objects.all() if assign is not None]
        print(user_list)
        context = {'get_audit': get_audit, 'assigned_users': user_list}
        return render(request, 'audit/add_audit.html', context)

    # else:
    #     form = AuditForm(organization=request.user.organization)
    #     context = {'get_audit': get_audit, 'form': form}
    #     return render(request, 'assets/add_audit.html', context)

def get_audits_by_id(request, id):
    get_asset = get_object_or_404(Asset, id=id)
    get_assigned_user = AssignAsset.objects.filter(asset__id=id).first()
    print("get_assigned_user",get_assigned_user)
    if request.method == 'POST':
        comments = request.POST.get('comments', None)
        condition = request.POST.get('condition', None)
        print("condition",condition)
        files=request.FILES.getlist('image')
        print("files'''''''",files)
        if not files:
            file = request.FILES.get("image")
            print("file",file)
            if file:
                files = [file]
        image_instance=None
        for f in files:
                image_instance=AssetImage.objects.create(asset=get_asset, image=f)
        get_img_instance=AssetImage.objects.filter(asset=get_asset).first()
        Audit.objects.create(
            asset=get_asset,
            condition= condition,
            notes= comments,
            audited_by=request.user if request.user.is_authenticated else None,
            created_at= datetime.now(),
            image=get_img_instance
        )
        return redirect('audit:completed_audits')

    elif request.method == 'GET':
        if get_assigned_user is None:
            print("No USER")
            user_list = list(User.undeleted_objects.all())
            context = {'get_asset': get_asset, 'assigned_users': user_list}
        else:
            print(get_asset, get_assigned_user.user.full_name)
            context = {'get_asset': get_asset, 'asset_assigned_users': get_assigned_user.user.full_name}
        print("context",context)
        return render(request, 'audit/add_audit.html', context)

def audit_list(request):
    audits = Audit.objects.all()
    return render(request, 'audit/audit_list.html',context={
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
    return render(request, 'audit/asset-audit-history.html', context=context)

def completed_audits(request):
    thirty_days_ago = datetime.now() - timedelta(days=30)
    audits = Audit.objects.filter(
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')
    return render(request, 'audit/audit_list.html', {
        'audits': audits
    })

# def pending_audits(request):
#     get_audits=Audit.objects.all()
#     get_due_audits=[]
#     audits={}
#     for audit in get_audits:
#         time_diff=next_audit_due(audit)
#         print("time diff",time_diff)
#         if time_diff<=0:
#             audits['name']=audit.asset
#             audits['expected_date']=audit.created_at+timedelta(days=abs(time_diff))
#             get_due_audits.append(audits)
#     audit = Audit.objects.all().values('asset')
#     print(audit)
#     for it in audit:
#         print(it['asset'])
#     get_remaining_assets = Asset.objects.exclude(id__in=audit.values('asset'))
#     print(get_remaining_assets)
#     # pending = [a for a in audits if is_pending_audit(a)]
#     # print(pending)
#     print("due audits",get_due_audits)
#     return render(request, 'assets/pending_audits.html',context={
#         'audits': get_remaining_assets,
#         'due_audits': get_due_audits
#     })

def pending_audits(request):
    all_audits = Audit.objects.select_related("asset", "asset__product")
    due_audits = []
    
    # Get overdue audits
    for audit in all_audits:
        days_remaining, is_pending = next_audit_due(audit)

        if days_remaining is not None and days_remaining < 0:
            due_audits.append({
                "asset": audit.asset,
                "expected_date": is_pending,
                "days_overdue": abs(days_remaining),
            })

    #Find assets that have NEVER been audited
    audited_asset_ids = all_audits.values_list("asset_id", flat=True)
    remaining_assets = Asset.objects.exclude(id__in=audited_asset_ids)

    return render(request, 'audit/pending_audits.html', {
        "due_audits": due_audits,
        "audits": remaining_assets
    })
def get_assigned_user(request, tag=None):
    if not tag:
        return JsonResponse({"error": "No tag provided"}, status=400)

    asset = Asset.objects.filter(tag=tag).first()

    if not asset:
        return JsonResponse({"exists": False, "assigned_user": None}, status=200)

    assign_record = AssignAsset.objects.filter(asset=asset).order_by("-assigned_date").first()

    return JsonResponse({
        "exists": True,
        "assigned_user": assign_record.user.full_name if assign_record else None,
        "assigned_user_id": assign_record.user.id if assign_record else None
    })