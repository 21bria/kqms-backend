from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from kqms.models import MineUnits, HmUnit

# python manage.py append_hm_unit
class Command(BaseCommand):
    help = "Append HM Unit 'Date?' (Day & Night, hm=0)"

    def handle(self, *args, **options):
        # SET MANUAL DI SINI
        START_DATE = date(2026, 1, 1)
        END_DATE   = date(2026, 1, 31)
        SHIFTS     = ['Day', 'Night']
        # ===============================

        units = MineUnits.objects.filter(status=1)
        created = 0
        skipped = 0

        with transaction.atomic():
            current = START_DATE
            while current <= END_DATE:
                for shift in SHIFTS:
                    for unit in units:
                        _, is_created = HmUnit.objects.get_or_create(
                            unit=unit,
                            date=current,
                            shift=shift,
                            defaults={
                                'hm_start': 0,
                                'hm_end': 0,
                                'status': 'DRAFT'
                            }
                        )
                        if is_created:
                            created += 1
                        else:
                            skipped += 1

                current += timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Selesai ✔ {created} dibuat, {skipped} dilewati"
            )
        )
