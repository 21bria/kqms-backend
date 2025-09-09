from django.urls import path
from ..views.reconciliation.productions_view import *

urlpatterns = [
    # Task list
    # path('productions/page/', recon_mine_day, name='productions-page'),
    path('get/productions/data/', recon_mine_day, name='get-productions-daily'),
    
]
    