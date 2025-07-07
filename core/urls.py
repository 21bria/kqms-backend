from django.contrib import admin
from django.urls import path, include
import accounts
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView,
)
from django.conf import settings
from django.conf.urls.static import static
# from accounts.views import GoogleLoginView, MicrosoftLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oidc/', include('mozilla_django_oidc.urls')),
    
    path('api/accounts/', include('accounts.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token

    #  Login Google / Microsoft
    # path('oidc/google/', GoogleLoginView.as_view(), name='google_login'),
    # path('oidc/microsoft/', MicrosoftLoginView.as_view(), name='microsoft_login'),
     path("kqms/", include("kqms.urls")),
]

# Menyajikan file statis dan media selama pengembangan
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)