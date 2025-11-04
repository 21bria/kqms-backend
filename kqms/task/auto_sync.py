# tasks.py
# kqms/task/auto_sync.py
from celery import shared_task
from kqms.models import SellingBarging, OreProductions, SourceMinesDome
import logging
logger = logging.getLogger(__name__)

@shared_task
def auto_sync_dome_status_task():

    # Ambil semua id_pile yang punya status Finished (case-insensitive)
    finished_piles = list(
        SellingBarging.objects.filter(sale_dome__iexact='Finished')
        .values_list('id_pile', flat=True)
        .distinct()
    )

    if not finished_piles:
        return "No finished piles found"

    # Ubah semua Continue jadi Finished untuk id_pile yang sama
    updated_count = SellingBarging.objects.filter(
        id_pile__in=finished_piles,
        sale_dome__iexact='Continue'
    ).update(sale_dome='Finished')

    # Sinkron ke tabel lain
    OreProductions.objects.filter(
        id_pile__in=finished_piles,
        status_dome__iexact='Continue'
    ).update(status_dome='Finished')

    SourceMinesDome.objects.filter(
        id__in=finished_piles,
        dome_finish__iexact='Continue'
    ).update(dome_finish='Finished')

    logger.info(f"Auto sync dome: updated {updated_count} records")
    return f"Updated {updated_count} SellingBarging records and synced others."
