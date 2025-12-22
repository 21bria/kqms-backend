from file_manager.models import FilePermission

def has_permission(user, permission, folder=None, file=None):
    if user.is_superuser:
        return True

    return FilePermission.objects.filter(
        user=user,
        permission=permission,
        folder=folder if folder else None,
        file=file if file else None
    ).exists()

def can_edit(user, file):
    if not user.is_authenticated:
        return False

    # Manager bisa edit semua
    if user.groups.filter(name='Manager').exists():
        return True

    # uploader boleh edit
    if file.uploaded_by == user:
        return True

    return False

def can_view(user, file):
    return can_edit(user, file) or file.folder.is_public
