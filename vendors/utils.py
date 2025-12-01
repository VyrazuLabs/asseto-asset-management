from django.template.loader import get_template
from django.http import HttpResponse
import csv
from io import BytesIO
from xhtml2pdf import pisa
from assets.models import Asset
from django.db.models import Q
from vendors.models import Vendor

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
            'GSITN_no.':vendor.gstin_number,
            'status':vendor.status
        }
        asset_count=Asset.objects.filter(vendor=vendor.id).count()
        vendor_dict['asset_count']=asset_count
        venodr_list.append(vendor_dict)
    return venodr_list

def vendor_details(get_vendor,request):
    vendor_details_dict={
        'name':get_vendor.name ,
        'email':get_vendor.email if get_vendor.email else None,
        'phone':get_vendor.phone if get_vendor.phone else None,
        'designation':get_vendor.designation if get_vendor.designation else None,
        'status':get_vendor.status,
        'contact_person':get_vendor.contact_person if get_vendor.contact_person else None,
        'GSTIN Number':get_vendor.gstin_number if get_vendor.gstin_number else None,
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