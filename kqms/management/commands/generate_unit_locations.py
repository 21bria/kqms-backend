
from django.core.management.base import BaseCommand
from kqms.models import UnitLocation, SourceMinesLoading, SourceMinesDumping

class Command(BaseCommand):
    help = 'Setup UnitLocation and generate data'

    def handle(self, *args, **options):
        # === Insert / update UnitLocation dari SourceMinesLoading ===
        loading_points = SourceMinesLoading.objects.all()
        for lp in loading_points:
            obj, created = UnitLocation.objects.update_or_create(
                code=lp.loading_point.upper().replace(" ", "_"),  # bisa jadi kode unik
                defaults={
                    "name": lp.loading_point
                }
            )
            action = "Created" if created else "Updated"
            print(f"{action} UnitLocation from Loading: {obj.code} - {obj.name}")

        # === Insert / update UnitLocation dari SourceMinesDumping ===
        dumping_points = SourceMinesDumping.objects.all()
        for dp in dumping_points:
            obj, created = UnitLocation.objects.update_or_create(
                code=dp.dumping_point.upper().replace(" ", "_"),
                defaults={
                    "name": dp.dumping_point
                }
            )
            action = "Created" if created else "Updated"
            print(f"{action} UnitLocation from Dumping: {obj.code} - {obj.name}")

