from django.template.loader import get_template
from django.http import HttpResponse
import csv
from io import BytesIO
from xhtml2pdf import pisa
import os
from django.shortcuts import redirect
import pandas as pd
from django.contrib import messages
import os
from datetime import date
from .models import File
today = date.today()


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


def csv_file_upload(request, file):
    if file is not None:
        file_name = file.name
        split_tup = os.path.splitext(file_name)
        file_extension = split_tup[1]

        if file_name.endswith('.csv'):
            obj = File.objects.create(file=file)
            df = pd.read_csv(obj.file, delimiter=',')
            list_of_csv = [list(row) for row in df.values]
            length_of_csv = len(list_of_csv)
            if length_of_csv <= 100:
                return obj.file.path
            else:
                messages.error(
                    request, f'Please upload less than 100 rows. Your list has {length_of_csv} rows.')
        else:
            messages.error(
                request, f'Please upload CSV file. You have uploaded {file_extension} file.')
    else:
        messages.error(request, 'Please choose a File.')

    return redirect(request.META.get('HTTP_REFERER'))
