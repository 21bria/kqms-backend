from .google_drive import get_drive_service

def share_google_file(cloud_id, emails, role='writer'):
    service = get_drive_service()

    for email in emails:
        service.permissions().create(
            fileId=cloud_id,
            body={
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
        ).execute()
