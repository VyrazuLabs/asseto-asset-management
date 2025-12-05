from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from assets.api_utils import get_asset_id
from assets.models import Asset
from barcode import Code128
from barcode.writer import SVGWriter
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from barcode.writer import ImageWriter
import io
import base64
from assets.api_utils import convert_svg_mm_to_px

class Scan_barcode(View):
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
        
def generate_barcode(tag_id):
    barcode_svg = Code128(tag_id, writer=SVGWriter())
    svg_content = barcode_svg.render(writer_options={'write_text': False,'module_width': 0.8,'module_height': 25,},text=f'Asset-{tag_id}').decode('utf-8')
    return svg_content

def generate_barcode_px(tag_id):
    writer = SVGWriter()
    writer_options = {
        "write_text": False,
        "module_height": 25,   # still internal mm
        "module_width": 0.8,   # still internal mm
    }

    raw_svg = Code128(str(tag_id), writer=writer).render(writer_options).decode()

    # convert everything to px
    svg_px = convert_svg_mm_to_px(raw_svg)

    return svg_px