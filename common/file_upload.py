import os
import uuid

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage

from constants import MAX_DOCUMENT_FILE_SIZE, MAX_IMAGE_FILE_SIZE, MAX_VIDEO_FILE_SIZE


class CreateName:
    @staticmethod
    def unique_name(file_name):
        return f"{uuid.uuid4()}_{file_name}"


class CreatePath:
    @staticmethod
    def create_folder_path(folder_path):
        folder_path = os.path.join(settings.MEDIA_ROOT, folder_path)
        os.makedirs(folder_path, exist_ok=True)

        return folder_path


class CreateStorage:
    @staticmethod
    def create_file_storage(folder_path, unique_name, file_obj):
        fs = FileSystemStorage(location=folder_path)
        fs.save(unique_name, file_obj)


class CheckSize:
    @staticmethod
    def image_size(request, file_size):
        if file_size > MAX_IMAGE_FILE_SIZE:
            messages.error(request, "Image size is more than 5 MB")
            return False
        
        return True

    @staticmethod
    def video_size(request, file_size):
        if file_size > MAX_VIDEO_FILE_SIZE:
            messages.error(request, "Video size is more than 10 MB")
            return False
        return True

    @staticmethod
    def document_size(request, file_size):
        if file_size > MAX_DOCUMENT_FILE_SIZE:
            messages.error(request, "Document size is more than 5 MB")
            return False
        return True
class Upload:
    @staticmethod
    def image_upload(request, file_object, folder_name):

        if not file_object:
            return None

        image_extentions = {".jpg", ".jpeg", ".svg", ".png", ".webp", ".avif"}
        ext = os.path.splitext(file_object.name)[1].lower()
        if ext not in image_extentions:
            messages.error(request, f" {ext} file type not allowed")
            return None
        
        if not CheckSize.image_size(request, file_object.size):
            return None

        unique_name = CreateName.unique_name(file_object.name)
        folder_path = CreatePath.create_folder_path(folder_name)
        CreateStorage.create_file_storage(folder_path, unique_name, file_object)
        return unique_name

    @staticmethod
    def video_upload(request, file_object, folder_name):

        if not file_object:
            return None

        video_extentions = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}
        ext = os.path.splitext(file_object.name)[1].lower()

        if ext not in video_extentions:
            messages.error(request, f" {ext} file type not resloveallowed")
            return None

        if not CheckSize.video_size(request, file_object.size):
            return None

        unique_name = CreateName.unique_name(file_object.name)
        folder_path = CreatePath.create_folder_path(folder_name)
        CreateStorage.create_file_storage(folder_path, unique_name, file_object)

        return unique_name

    @staticmethod
    def document_upload(request, file_object, folder_name):

        if not file_object:
            return None

        document_extentions = {".pdf", ".txt", ".csv", ".docx"}
        ext = os.path.splitext(file_object.name)[1].lower()

        if ext not in document_extentions:
            messages.error(request, f" {ext} file type not allowed")
            return None

        if not CheckSize.document_size(request, file_object.size):
            return None

        unique_name = CreateName.unique_name(file_object.name)
        folder_path = CreatePath.create_folder_path(folder_name)
        CreateStorage.create_file_storage(folder_path, unique_name, file_object)

        return unique_name
