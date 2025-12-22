from django.utils import timezone
from datetime import timedelta
from file_manager.models.file_lock import FileLock
from file_manager.services.audit import log_action

LOCK_DURATION = timedelta(minutes=30)

def is_locked(file):
    if not hasattr(file, 'lock'):
        return False

    lock = file.lock
    if not lock.is_active:
        return False

    if lock.expires_at and lock.expires_at < timezone.now():
        lock.is_active = False
        lock.save()
        return False

    return True


def lock_file(file, user, request=None):
    if is_locked(file):
        return False

    FileLock.objects.create(
        file=file,
        locked_by=user,
        expires_at=timezone.now() + LOCK_DURATION
    )

    if request:
        log_action(request, file, 'lock')

    return True


def unlock_file(file, user=None, force=False, request=None):
    if not hasattr(file, 'lock'):
        return

    lock = file.lock
    if force or lock.locked_by == user:
        lock.is_active = False
        lock.save()

        if request:
            log_action(request, file, 'unlock')
