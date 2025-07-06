
from django.urls import path
from . import auth

urlpatterns = [
    path('oidc/redirect/', auth.oidc_redirect, name='oidc_redirect'),
    path('token/email/', auth.EmailTokenObtainPairView.as_view(), name='token_obtain_pair_email'),
    path('logout/', auth.logout_view, name='logout'),
]
