from .utils.menu import get_menu_context

# def menu_context(request):
#     if request.user.is_authenticated:
#         menus = get_user_menu_tree(request.user)
#         print("DEBUG MENU STRUCTURE:")
#         import pprint
#         pprint.pprint(menus)  # akan tampil di terminal saat page dimuat
#         return {'user_menus': menus}
#     return {}

def menu_context(request):
    """
    Context processor untuk menu
    """
    if request.user.is_authenticated:
        return {'dynamic_menu': get_menu_context(request)}
    return {'dynamic_menu': []}
