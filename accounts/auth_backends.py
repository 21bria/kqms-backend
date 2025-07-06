from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class MyOIDCBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super().create_user(claims)
        user.is_active = True
        user.email = claims.get("email", "")
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.save()
        return user

    def update_user(self, user, claims):
        user.email = claims.get("email", "")
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.save()
        return user

    def get_username(self, claims):
        return claims.get("preferred_username") or claims.get("email")

class BaseOIDCBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super().create_user(claims)
        user.is_active = True
        user.email = claims.get("email", "")
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.save()
        return user

    def update_user(self, user, claims):
        user.email = claims.get("email", "")
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.save()
        return user

    def get_username(self, claims):
        return claims.get("preferred_username") or claims.get("email")
    
class GoogleOIDCBackend(BaseOIDCBackend):
    def get_settings_prefix(self):
        return 'GOOGLE_OIDC_'

class MicrosoftOIDCBackend(BaseOIDCBackend):
    def get_settings_prefix(self):
        return 'MICROSOFT_OIDC_'


