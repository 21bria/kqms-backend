from django.http import JsonResponse
from notifications.utils import batch_notifications

def test_push_notif(request):
    duplicates, duplicate_count= batch_notifications.push_double_notifications()

    return JsonResponse({
        "status"    : "ok",
        "message"   : "Notification sent!",
        "type_sample": "PDS",
        "duplicates": list(duplicates)
    })