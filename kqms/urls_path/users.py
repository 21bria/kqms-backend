from django.urls import path
from ..views.auth.users import *
from ..views.auth.group import *
# Permission page

urlpatterns = [
    path('users/', users_page, name='user-page'),
    path('users/list', user_List.as_view(), name='user-list'),
    path('users/add/', user_create, name='user_create'),
    path('users/<int:pk>/edit/', user_edit, name='user_edit'),
    path('users/delete/', delete_users, name='delete-users'),
    path('groups/', group_page, name='group-page'),
    path('groups/list/', group_List.as_view(), name='groups-list'),
    path('groups/add/', group_create, name='group_create'),
    path('groups/<int:pk>/edit/', group_edit, name='group_edit'),
    path('groups/delete/', delete_group, name='delete-group'),

]