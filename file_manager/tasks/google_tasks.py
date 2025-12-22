from celery import shared_task
from file_manager.models.file import FileVersion, FileCloudLink
from file_manager.services.google_convert import upload_and_convert

@shared_task
def upload_to_google_task(file_version_id):
    version = FileVersion.objects.get(id=file_version_id)
    cloud_id, cloud_url = upload_and_convert(version)

    FileCloudLink.objects.create(
        file=version.file,
        provider='google',
        cloud_id=cloud_id,
        cloud_url=cloud_url
    )
