from django.shortcuts import render

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from kqms.models.samples_data_view import SamplesView
from django.db.models import Count

def push_double_notifications():
    duplicates = (
        SamplesView.objects
        .filter(type_sample='PDS')  # ← filter tipe PDS
        .values('kode_batch')
        .annotate(total=Count('kode_batch'))
        .filter(total__gt=1)
    )

    duplicate_count = duplicates.count()

    if duplicate_count > 0:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "duplicates",
            {
                "type"          : "send_duplicate",  # wajib
                "message"       : f"Ada {duplicate_count} batch PDS duplikat!",
                "count"         : duplicate_count,
                "duplicates"    : list(duplicates),
                "sample_type"   : "PDS"
            }
        )


    return list(duplicates), duplicate_count