# templatetags/menu_tags.py
from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.inclusion_tag('layout/menu/menu_item.html', takes_context=True)
def render_menu_item(context, menu_item):
    """
    Template tag untuk render menu item
    """
    request = context['request']
    
    # Cek apakah URL aktif
    is_active = False
    if menu_item['menu'].url:
        try:
            current_url = request.resolver_match.url_name
            if current_url == menu_item['menu'].url:
                is_active = True
        except:
            pass
    
    return {
        'menu_item': menu_item,
        'is_active': is_active,
        'request': request
    }

@register.filter
def has_children(menu_item):
    """
    Filter untuk cek apakah menu memiliki children
    """
    return len(menu_item['children']) > 0

@register.filter
def get_url(menu_item):
    """
    Filter untuk mendapatkan URL dari menu
    """
    if menu_item['menu'].url:
        try:
            return reverse(menu_item['menu'].url)
        except NoReverseMatch:
            return menu_item['menu'].url
    return "javascript:void(0);"
