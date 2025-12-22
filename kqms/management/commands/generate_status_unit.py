
from django.core.management.base import BaseCommand
from kqms.models import UnitStatus, UnitActivity

class Command(BaseCommand):
    help = 'Setup UnitStatus, UnitActivity, UnitLocation, and generate data'

    def handle(self, *args, **options):
        # === Insert UnitStatus ===
        status_data = [
            ("OPR", "OPERATING"),
            ("STB", "STANDBY"),
            ("BD", "BREAKDOWN"),
            ("PM", "MAINTENANCE"),
            ("SUPPORT", "Support"),
            ("OFF", "Off / Non Shift"),
            ("WX", "Weather"),       # tambahan untuk cuaca / kondisi
            ("SLP", "Slippery"),
        ]

        status_objects = {}
        for code, cat in status_data:
            obj, _ = UnitStatus.objects.get_or_create(
                code=code,
                defaults={
                    "name": cat.title(),
                    "category": cat
                }
            )
            status_objects[code] = obj
            self.stdout.write(f"Status created: {obj.code} - {obj.category}")

        # === Insert UnitActivity linked to UnitStatus ===
        activity_data = [
            # OPERATING
            ("OPR", "P2H", "Pre-Start Check"),
            ("OPR", "LOAD", "Loading Ore"),
            ("OPR", "HAUL", "Hauling Ore"),
            ("OPR", "DUMP", "Dumping Ore"),
            ("OPR", "DOZ", "Dozing"),
            ("OPR", "GRD", "Grader"),
            ("OPR", "CMP", "Compactor"),
            ("OPR", "WTR", "Water Truck"),
            
            # STANDBY
            ("STB", "WAIT", "Waiting"),
            ("STB", "IDLE", "Idle"),
            
            # PM / Maintenance
            ("PM", "PM250", "PM 250 HM"),
            ("BD", "HYD", "Hydraulic Problem"),
            
            # SUPPORT / OFF
            ("SUPPORT", "SUP", "Support Work"),
            ("OFF", "OFF", "Off / Non Shift"),
            
            # Weather / condition
            ("WX", "RAIN", "Raining"),
            ("SLP", "SLIP", "Slippery"),
        ]

        for st, code, name in activity_data:
            obj, _ = UnitActivity.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "status": status_objects[st]
                }
            )
            self.stdout.write(f"Activity created: {obj.code} - {obj.name}")
