from rest_framework.decorators import action
from rest_framework.response import Response   # ✅ WAJIB
from django.shortcuts import redirect

from file_manager.services.google_convert import upload_and_convert
from file_manager.services.permissions import can_edit
from file_manager.models import FileCloudLink
from file_manager.services.file_lock import lock_file, is_locked
from file_manager.services.file_lock import unlock_file
from file_manager.services.audit import log_action

@action(detail=True, methods=['get'])
def open_google(self, request, pk=None):
    file = self.get_object()

    if not can_edit(request.user, file):
        return Response(status=403)

    if is_locked(file) and file.lock.locked_by != request.user:
        return Response(
            {"detail": "File is currently being edited"},
            status=423
        )

    lock_file(file, request.user)

    # ✅ audit open
    log_action(request, file, 'open', {
        'mode': 'edit'
    })

    if hasattr(file, 'cloud'):
        return redirect(file.cloud.cloud_url)

    latest_version = file.versions.first()
    cloud_id, cloud_url = upload_and_convert(latest_version)

    FileCloudLink.objects.create(
        file=file,
        provider='google',
        cloud_id=cloud_id,
        cloud_url=cloud_url
    )

    # ✅ audit sync
    log_action(request, file, 'sync', {
        'provider': 'google',
        'cloud_id': cloud_id
    })

    return redirect(cloud_url)


@action(detail=True, methods=['post'])
def check_in(self, request, pk=None):
    file = self.get_object()

    if not can_edit(request.user, file):
        return Response(status=403)

    unlock_file(file, request.user)

    # ✅ audit unlock
    log_action(request, file, 'unlock')

    return Response({"detail": "File unlocked"})
