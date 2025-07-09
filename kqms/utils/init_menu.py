from kqms.models import Menu
from django.db import transaction

@transaction.atomic
def create_menu_from_structure(menu_items, parent=None):
    for item in menu_items:
        is_category = item.get('category') is not None and parent is None and not item.get('url')
        
        menu = Menu.objects.create(
            title=item['title'],
            icon=item.get('icon', ''),
            url=item.get('url', ''),
            parent=parent,
            order=item.get('order', 0),
            is_active=True,
            allowed_group_names=item.get('groups', []),
            is_category=is_category,
            category_title=item.get('category') if is_category else None
        )

        # Rekursif jika ada anak
        children = item.get('children')
        if children:
            create_menu_from_structure(children, parent=menu)
