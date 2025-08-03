# python manage.py generate_selling_plan

import uuid
import random
from datetime import datetime
from collections import defaultdict

from django.core.management.base import BaseCommand
from kqms.models import SellingBarging, SellingPlan


class Command(BaseCommand):
    help = 'Generate dummy data for SellingPlan based on existing SellingBarging records'

    def handle(self, *args, **options):
        start_date = datetime(2025, 7, 1)
        end_date   = datetime(2025, 7, 31)

        self.stdout.write("Fetching SellingBarging data...")

        barging_data = SellingBarging.objects.filter(date_barging__range=(start_date, end_date))

        if not barging_data.exists():
            self.stdout.write(self.style.WARNING("No SellingBarging data found in range. Aborting."))
            return

        grouped = defaultdict(list)
        for record in barging_data:
            key = (record.date_barging, record.type_selling)
            grouped[key].append(record)

        bulk_plan = []

        for (plan_date, type_selling), records in grouped.items():
            total_ton = sum(r.tonnage or 0 for r in records)
            ni_values = [r.fill_adjust if r.fill_adjust is not None else 1.5 for r in records]

            tonnage_plan = round(total_ton * random.uniform(0.95, 1.05), 2)
            ni_plan = round(sum(ni_values) / len(ni_values) + random.uniform(-0.05, 0.05), 2)

            # Pastikan nilai minimum >= 1.2
            ni_plan = max(1.2, round(ni_plan, 2))
            ni_buyer = round(max(1.2, ni_plan + random.uniform(-0.02, 0.02)), 2)
            ni_surveyor = round(max(1.2, ni_plan + random.uniform(-0.03, 0.03)), 2)

            plan = SellingPlan(
                id=uuid.uuid4(),
                plan_date=plan_date,
                type_ore=random.choice(['LIM', 'SAP']),
                type_selling=type_selling,
                tonnage_plan=tonnage_plan,
                ni_plan=ni_plan,
                ni_buyer=ni_buyer,
                ni_surveyor=ni_surveyor,
                check_duplicated=f"{plan_date}_{type_selling}",
                description='Auto-generated dummy plan',
                left_date=random.randint(0, 5),
                id_user=random.randint(1, 5),
            )
            bulk_plan.append(plan)

        SellingPlan.objects.bulk_create(bulk_plan, batch_size=100)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(bulk_plan)} SellingPlan records."))
