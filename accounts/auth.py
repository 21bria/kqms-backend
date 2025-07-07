from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .auth_serializers import EmailTokenObtainPairSerializer

from django.contrib.auth import logout
from django.shortcuts import redirect


def oidc_redirect(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseRedirect("http://localhost:3000/auth?error=unauthenticated")

    refresh  = RefreshToken.for_user(user)
    token    = str(refresh.access_token)
    username = user.username
    email    = user.email

    # return HttpResponseRedirect(f"http://localhost:3000/auth?token={token}&user={username}")
    return HttpResponseRedirect(f"http://localhost:3000/auth?token={token}&user={email}")

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        print("✅ EmailTokenObtainPairView CALLED")
        print("📩 Data masuk:", request.data)
        return super().post(request, *args, **kwargs)

def logout_view(request):
    logout(request)
    response = HttpResponseRedirect("http://localhost:3000/auth")
    response.delete_cookie('sessionid')
    return response