from django.core.files.base import ContentFile
import uuid
import base64

def convert_image(image):
    format,image_string=image.split(";base64,")
    extract=format.split("/")[-1]
    file_name=f"{uuid.uuid4()}.{extract}"
    image_data=ContentFile(base64.b64decode(image_string),name=file_name)

    return image_data