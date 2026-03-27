from django.template.loader import get_template
from django.http import HttpResponse
import csv
from io import BytesIO
from xhtml2pdf import pisa
from assets.models import Asset,AssignAsset
from django.db.models import Q
from vendors.models import Vendor
from django.core.paginator import Paginator
from dashboard.models import Address
from django.shortcuts import get_object_or_404
from dashboard.models import CustomField
from datetime import date

PAGE_SIZE = 10
ORPHANS = 1


def export_vendors_pdf_utils(request):
    today = date.today()
    vendors = Vendor.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    context = {'vendors': vendors}
    pdf = render_to_pdf('vendors/vendors-pdf.html', context_dict=context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="export-vendors-{today}.pdf"'
    return response
def export_vendor_csv_utils(request):
    today = date.today()
    header_list = ['Vendor Name', 'Vendor Email', 'Phone', 'Contact Person Name', 'Designation', 'GSTIN Number',
                   'Address Line One', 'Address Line Two', 'City', 'Pin Code', 'State', 'Country', 'Description']
    vendors_list = Vendor.undeleted_objects.filter(organization=request.user.organization).order_by('-created_at').values_list('name', 'email', 'phone', 'contact_person', 'designation',
    'gstin_number', 'address__address_line_one', 'address__address_line_two', 'address__city', 'address__pin_code', 'address__state', 'address__country', 'description')
    context = {'header_list': header_list, 'rows': vendors_list}
    response = render_to_csv(context_dict=context)
    response['Content-Disposition'] = f'attachment; filename="export-vendors-{today}.csv"'
    return response

def search_utils(request,page):
    search_text = (request.GET.get('search_text') or "").strip()

    if search_text:
        vendors_list = searched_data(request,search_text)
        page_object = vendors_list
    else:
        vendors_list = Vendor.undeleted_objects.filter(
            organization=request.user.organization
        ).order_by("-created_at")

        paginator = Paginator(vendors_list, PAGE_SIZE, orphans=ORPHANS)
        page_number = page
        page_object = paginator.get_page(page_number)

    count_array = []
    for it in page_object:
        get_count = get_count_of_assets(request, it.id)
        count_array.append(get_count)

    deleted_vendor_count = Vendor.deleted_objects.count()
    return page_object,count_array,deleted_vendor_count

def get_vendor_details(request, id):
    vendor = get_object_or_404(
        Vendor.undeleted_objects, pk=id, organization=request.user.organization)
    address = Address.objects.get(id=vendor.address.id) if vendor.address else None
    assets=Asset.undeleted_objects.filter(vendor=vendor)
    assets_paginator=Paginator(assets,10,orphans=1)
    assets_page_number=request.GET.get('asset_page')
    assets_page_object=assets_paginator.get_page(assets_page_number)


    history_list = vendor.history.all()
    paginator = Paginator(history_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    get_custom_data=[]
    get_data=CustomField.objects.filter(object_id=vendor.id)
    for it in get_data:
        obj={}
        obj['field_name']=it.field_name
        obj['field_value']=it.field_value
        get_custom_data.append(obj)
    context = {'sidebar': 'vendors', 'vendor': vendor, 'page_object': page_object,
    'address': address, 'title': f'Details-{vendor.name}','assets_page_object':assets_page_object,'get_custom_data':get_custom_data}

def vendor_list_util(request):
    vendors_list = Vendor.undeleted_objects.filter(Q(organization=None) |  
        Q(organization=request.user.organization)).order_by('-created_at')
    deleted_vendor_count=Vendor.deleted_objects.count()
    paginator = Paginator(vendors_list, PAGE_SIZE, orphans=ORPHANS)
    count_array = []
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    for vendor in page_object:
        count_array.append(
            get_count_of_assets(request, vendor.id)
        )
    context = {'sidebar': 'vendors','count_array': count_array,
               'page_object': page_object, 'deleted_vendor_count':deleted_vendor_count,'title': 'Vendors',
               }
    return context

def render_to_csv(context_dict={}):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(context_dict['header_list'])
    for row in context_dict['rows']:
        writer.writerow(row)
    return response


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def get_count_of_assets(request,vendor_id):
    """
    Returns the count of assets for the given organization.
    """
    get_count=Asset.objects.filter(organization=request.user.organization,vendor=vendor_id, is_deleted=False).count()
    return get_count

def convert_to_list(queryset,request):
    venodr_list=[]
    for vendor in queryset:
        vendor_dict={
            'id':vendor.id,
            'vendor_name':vendor.name,
            'contact_person':vendor.contact_person,
            'email':vendor.email,
            'phone':vendor.phone,
            'gstin_number':vendor.gstin_number,
            'status':vendor.status
        }
        asset_count=Asset.undeleted_objects.filter(vendor=vendor.id).count()
        vendor_dict['asset_count']=asset_count
        venodr_list.append(vendor_dict)
    return venodr_list

def vendor_details(get_vendor,request):
    vendor_details_dict={
        'id':get_vendor.id,
        'name':get_vendor.name ,
        'email':get_vendor.email if get_vendor.email else None,
        'phone':get_vendor.phone if get_vendor.phone else None,
        'designation':get_vendor.designation if get_vendor.designation else None,
        'status':get_vendor.status,
        'contact_person':get_vendor.contact_person if get_vendor.contact_person else None,
        'gstin_number':get_vendor.gstin_number if get_vendor.gstin_number else None,
        'address':get_vendor.address.address_line_one if get_vendor.address and get_vendor.address.address_line_one else None,
        'description':get_vendor.description if get_vendor.description else None
    }
    get_assets=Asset.undeleted_objects.filter(vendor=get_vendor.id)
    get_assets_count=Asset.undeleted_objects.filter(vendor=get_vendor.id).count()
    vendor_details_dict['assets_count']=get_assets_count
    get_asset_list=[]
    vendor_details_dict['assets']=get_asset_list
    if get_assets:
        for asset in get_assets:
            get_asset_dict={
                'id':asset.id,
                'asset_tag':asset.tag,
                'asset_name':asset.name
            }
            get_asset_list.append(get_asset_dict)
        vendor_details_dict['assets']=get_asset_list

    return vendor_details_dict


def searched_data(request,search_text):
    vendor_list=Vendor.undeleted_objects.filter(
        Q(organization=request.user.organization) &
        (
            Q(name__icontains=search_text) |
            Q(email__icontains=search_text) |
            Q(phone__icontains=search_text) |
            Q(designation__icontains=search_text) |
            Q(gstin_number__icontains=search_text) |
            Q(contact_person__icontains=search_text)
        )
    ).order_by("-created_at")[:10]
    return vendor_list


def vendor_list_for_form(vendors):
    list=[]
    for vendor in vendors:
        vendor_dict={
            'id':vendor.id,
            'name':vendor.name
        }
        list.append(vendor_dict)
    return list

def get_assigned_asset_by_vendor(id):
    get_assets=Asset.undeleted_objects.filter(vendor_id=id)
    print("Asset Lists",get_assets)
    return get_assets
