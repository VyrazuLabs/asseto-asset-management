from django.template.loader import get_template
from django.http import HttpResponse
import csv
from io import BytesIO
from xhtml2pdf import pisa


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
