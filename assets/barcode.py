from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from assets.models import Asset
from barcode import Code128
from barcode.writer import SVGWriter
from django.contrib.auth.decorators import login_required

class scan_barcode(View):
    def get(self,request,**kwargs):
        tag_id=self.kwargs.get('tag_id')
        get_tag=Asset.objects.filter(tag=tag_id).exists()
        if get_tag:
            asset_id=Asset.objects.filter(tag=tag_id).first()
            respones_data={
                'id':asset_id.id,
                "status": "success"
            }
            return JsonResponse(respones_data)
        else:
            respones_data={
                'status':False,
                'message':"asset with this tag does not exists!"
            }
            return JsonResponse(respones_data, status=404)
        
def generate_barcode(tag_id,user_organization):
    barcode_svg = Code128(tag_id, writer=SVGWriter())
    svg_content = barcode_svg.render(writer_options={'write_text': False,'module_width': 0.8,'module_height': 25,},text=f'Asset-{tag_id}').decode('utf-8')
    return svg_content