from io import BytesIO
from googleapiclient.http import MediaIoBaseUpload
from .google_drive import get_drive_service

EXCEL_MIME = [
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
]

WORD_MIME = [
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
]

def upload_and_convert(file_version):
    service = get_drive_service()

    media = MediaIoBaseUpload(
        BytesIO(file_version.file_blob.read()),
        mimetype=file_version.mime_type,
        resumable=True
    )

    if file_version.mime_type in EXCEL_MIME:
        google_mime = 'application/vnd.google-apps.spreadsheet'
    elif file_version.mime_type in WORD_MIME:
        google_mime = 'application/vnd.google-apps.document'
    else:
        raise ValueError('Unsupported file type')

    metadata = {
        'name': file_version.file.original_name,
        'mimeType': google_mime
    }

    created = service.files().create(
        body=metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    return created['id'], created['webViewLink']
