from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from kqms.models import Menu
from kqms.utils.init_menu import create_menu_from_structure
from kqms.utils.menu_structure import menu_structure


@require_http_methods(["GET"])  # atau ["GET", "POST"] jika mau fleksibel
@login_required
def init_menu_view(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # Optional: Hapus menu lama sebelum insert ulang
    Menu.objects.all().delete()

    # Buat ulang struktur menu
    create_menu_from_structure(menu_structure)

    return JsonResponse({'status': 'Menu berhasil diinisialisasi'})
