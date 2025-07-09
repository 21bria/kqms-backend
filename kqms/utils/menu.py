from collections import defaultdict
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from kqms.models import Menu

def get_menu_context(request):
    """
    Function untuk mendapatkan menu berdasarkan user group
    """
    user_groups = request.user.groups.values_list('name', flat=True)
    
    # Ambil semua menu yang aktif dan urutkan berdasarkan order
    menus = Menu.objects.filter(is_active=True).order_by('order')
    
    # Filter menu berdasarkan group user
    filtered_menus = []
    for menu in menus:
        # Jika menu tidak ada batasan group atau user memiliki akses
        if not menu.allowed_group_names or any(group in menu.allowed_group_names for group in user_groups):
            filtered_menus.append(menu)
    
    # Bangun struktur menu hierarkis
    menu_tree = build_menu_tree(filtered_menus)
    
    return menu_tree

def build_menu_tree(menus):
    """
    Membangun struktur menu hierarkis
    """
    menu_dict = {}
    root_menus = []
    
    # Buat dictionary untuk akses cepat
    for menu in menus:
        menu_dict[menu.id] = {
            'menu': menu,
            'children': []
        }
    
    # Bangun hierarki
    for menu in menus:
        if menu.parent_id:
            if menu.parent_id in menu_dict:
                menu_dict[menu.parent_id]['children'].append(menu_dict[menu.id])
        else:
            root_menus.append(menu_dict[menu.id])
    
    return root_menus


# def get_user_menu_tree(user):
#     group_names = list(user.groups.values_list('name', flat=True))
    
#     # Jika superuser, ambil semua menu aktif
#     if user.is_superuser or user.groups.filter(name='superadmin').exists():
#         menus = Menu.objects.filter(is_active=True).order_by('order')
#     else:
#         menus = Menu.objects.filter(
#             is_active=True,
#         ).filter(
#             allowed_group_names__overlap=group_names
#         ).order_by('order')

#     # Strukturkan menu ke dalam kategori
#     category_map = defaultdict(list)
#     menu_map = {}

#     for menu in menus:
#         if menu.parent is None:
#             menu_data = {
#                 "title": menu.title,
#                 "icon": menu.icon,
#                 "url": menu.url,
#                 "children": [],
#             }
#             menu_map[menu.id] = menu_data
#             if menu.category_title:
#                 category_map[menu.category_title].append(menu_data)

#     # Hubungkan anak ke parent
#     for menu in menus:
#         if menu.parent_id and menu.parent_id in menu_map:
#             menu_map[menu.parent_id]["children"].append({
#                 "title": menu.title,
#                 "url": menu.url
#             })

#     return dict(category_map)
