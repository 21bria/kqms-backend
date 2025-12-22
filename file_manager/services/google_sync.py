from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload
from .google_drive import get_drive_service

def download_google_file(cloud_id):
    service = get_drive_service()

    request = service.files().export_media(
        fileId=cloud_id,
        mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    fh.seek(0)
    return fh
