from django.urls import path
from django.urls import re_path
from .consumers.batch_consumer import DuplicateNotificationConsumer
from .consumers.upload_mine_consumer import UploadMineConsumer

websocket_urlpatterns = [
    # path("ws/duplicates/", DuplicateNotificationConsumer.as_view()),
    re_path(r"ws/duplicates/$", DuplicateNotificationConsumer.as_view()),
    re_path(r"ws/upload/$", UploadMineConsumer.as_view()),
]
