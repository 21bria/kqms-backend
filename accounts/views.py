from django.shortcuts import render

# accounts/views.py
from mozilla_django_oidc.views import OIDCAuthenticationRequestView

class GoogleLoginView(OIDCAuthenticationRequestView):
    def get_settings_prefix(self):
        return 'GOOGLE_OIDC_'

class MicrosoftLoginView(OIDCAuthenticationRequestView):
    def get_settings_prefix(self):
        return 'MICROSOFT_OIDC_'