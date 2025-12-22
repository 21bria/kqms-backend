from django.contrib import admin
from django.urls import path, include
from .notifications import *


urlpatterns = [
    path("test-push/", test_push_notif, name="test-push"),
]
