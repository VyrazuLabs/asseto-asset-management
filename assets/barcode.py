from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from assets.api_utils import get_asset_id
from assets.models import Asset
from barcode import Code128
from barcode.writer import SVGWriter
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView

class Scan_barcode(View):
    def get(self,request,**kwargs):
        tag_id=self.kwargs.get('tag_id')
        respones_data = get_asset_id(tag_id)
        return JsonResponse(respones_data=respones_data, status=404)
        
def generate_barcode(tag_id):
    barcode_svg = Code128(tag_id, writer=SVGWriter())
    svg_content = barcode_svg.render(writer_options={'write_text': False,'module_width': 0.8,'module_height': 25,},text=f'Asset-{tag_id}').decode('utf-8')
    return svg_content
