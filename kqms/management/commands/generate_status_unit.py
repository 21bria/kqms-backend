
from django.core.management.base import BaseCommand
from kqms.models import UnitStatus, UnitActivity

class Command(BaseCommand):
    help = 'Setup UnitStatus, UnitActivity, UnitLocation, and generate data'

    def handle(self, *args, **options):
        # === Insert UnitStatus ===
        status_data = [
            ("EWH", "WORKING"),
            ("STB", "STANDBY"),
            ("BD", "BREAKDOWN"),
            # ("PM", "MAINTENANCE"),
            # ("SUPPORT", "Support"),
            # ("OFF", "Off / Non Shift"),
            # ("WX", "Weather"), 
            # ("SLP", "Slippery"),
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
            ("EWH", "D_EWH", "Default"),

            # STANDBY
            ("STB", "D_STB", "Default"),
       
            # PM / Maintenance
            ("BD", "USC", "Unshceduled"),
            # ("PM", "PM250", "PM 250 HM"),
            
            # SUPPORT / OFF
            # ("SUPPORT", "SUP", "Support Work"),
            # ("OFF", "OFF", "Off / Non Shift"),
            
            # Weather / condition
            # ("WX", "RAIN", "Raining"),
            # ("SLP", "SLIP", "Slippery"),
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
