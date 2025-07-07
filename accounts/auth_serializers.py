from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        print("🔍 ATTRS:", attrs)

        email = attrs.get('email')
        password = attrs.get('password')

        if not email:
            print("🚨 Email kosong")
            raise serializers.ValidationError({"email": "This field is required."})

        if not password:
            print("🚨 Password kosong")
            raise serializers.ValidationError({"password": "This field is required."})

        try:
            user = User.objects.get(email=email)
            print("✅ User ditemukan:", user.username)
        except User.DoesNotExist:
            print("❌ Email tidak ditemukan di database")
            raise serializers.ValidationError({"email": "Email not registered."})

        # user = authenticate(username=user.username, password=password)
        user = authenticate(email=email, password=password)

        if user is None:
            print("❌ Auth gagal")
            raise serializers.ValidationError({"non_field_errors": ["Invalid credentials."]})

        if not user.is_active:
            print("⚠️ User tidak aktif")
            raise serializers.ValidationError({"non_field_errors": ["Inactive user."]})

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email  # Tambah email ke token
        token['name'] = user.get_full_name()
        return token