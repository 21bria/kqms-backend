from .models.menu_model import Menu
from django.db.models import Q

def sidebar_menu(request):
    user = request.user

    if not user.is_authenticated:
        return {"menu_items": []}
    
    user_groups = user.groups.all()
    user_permissions = user.get_all_permissions()

    menu_queryset = Menu.objects.filter(
        Q(groups__in=user_groups) | Q(groups__isnull=True)
    ).distinct().order_by("order")

    def build_menu():
        menu_items = []

        root_menus = menu_queryset.filter(parent=None)

        for menu in root_menus:
            # Cek permission jika diset
            if menu.permission and menu.permission.codename not in [p.split('.')[-1] for p in user_permissions]:
                continue

            if menu.section_title:
                menu_items.append({"section_title": menu.section_title})
                continue

            children_qs = menu.children.all().order_by("order")
            children = []

            for child in children_qs:
                if child.permission and child.permission.codename not in [p.split('.')[-1] for p in user_permissions]:
                    continue

                subchildren_qs = child.children.all().order_by("order")
                if subchildren_qs.exists():
                    submenu = []
                    for sub in subchildren_qs:
                        if sub.permission and sub.permission.codename not in [p.split('.')[-1] for p in user_permissions]:
                            continue
                        submenu.append({"label": sub.label, "url": sub.url})
                    if submenu:
                        children.append({"label": child.label, "url": child.url, "submenu": submenu})
                else:
                    children.append({"label": child.label, "url": child.url})

            menu_items.append({
                "label": menu.label,
                "icon": menu.icon.name if hasattr(menu.icon, 'name') else menu.icon,
                "key": menu.key,
                "url": menu.url,
                "dropdown": bool(children),
                "children": children
            })
        

        return menu_items

    return {"menu_items": build_menu()}

# Tidak pakai permission
# def sidebar_menu(request):
#     user = request.user

#     if not user.is_authenticated:
#         return {"menu_items": []}

#     user_groups = user.groups.all()

#     def build_menu():
#         menu_items = []

#         # Ambil semua menu induk (parent=None) yang cocok group
#         root_menus = Menu.objects.filter(
#             Q(parent__isnull=True) & (Q(groups__in=user_groups) | Q(groups__isnull=True))
#         ).distinct().order_by('order')

#         for menu in root_menus:
#             if menu.section_title:
#                 menu_items.append({
#                     "section_title": menu.section_title
#                 })
#                 continue

#             # Ambil anak (child) dari menu ini
#             children = menu.children.filter(
#                 Q(groups__in=user_groups) | Q(groups__isnull=True)
#             ).distinct().order_by("order")

#             item = {
#                 "label": menu.label,
#                 "icon": menu.icon.name if menu.icon else "",  # jika pakai relasi FontAwesomeIcon
#                 "key": menu.key,
#                 "url": menu.url,
#                 "dropdown": children.exists(),
#             }

#             if children.exists():
#                 item["children"] = []
#                 for child in children:
#                     subchildren = child.children.filter(
#                         Q(groups__in=user_groups) | Q(groups__isnull=True)
#                     ).distinct().order_by("order")

#                     if subchildren.exists():
#                         item["children"].append({
#                             "label": child.label,
#                             "url": child.url,
#                             "submenu": [
#                                 {"label": sub.label, "url": sub.url} for sub in subchildren
#                             ]
#                         })
#                     else:
#                         item["children"].append({
#                             "label": child.label,
#                             "url": child.url
#                         })

#             menu_items.append(item)

#         return menu_items

#     return {"menu_items": build_menu()}
