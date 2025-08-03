# python manage.py generate_selling
import uuid
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from kqms.models import SellingBarging

import uuid
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from kqms.models import SellingBarging

class Command(BaseCommand):
    help = 'Generate dummy data for SellingBarging'

    def handle(self, *args, **options):
        start_date = datetime(2025, 7, 1)
        end_date = datetime(2025, 7, 31)
        date_range = (end_date - start_date).days

        shifts = ['Day', 'Night']
        bulk_data = []

        type_selling_map = {
            7 : 'HPAL',  # LIM
            10: 'RKEF',  # SAP
        }

        pile_material_map = {
            1: 'SAP',
            2: 'SAP',
            3: 'SAP',
            4: 'LIM',
            5: 'LIM',
            6: 'SAP',
        }

        pile_to_stockpile_map = {
            1: 2,
            2: 2,
            3: 2,
            4: 2,
            5: 2,
            6: 3,
        }

        for i in range(600):  # generate 600 data dummy
            material_id = random.choice([7, 10])
            ore_type = 'LIM' if material_id == 7 else 'SAP'
            type_selling = type_selling_map[material_id]

            # ambil pile dan stockpile sesuai jenis material
            valid_piles = [pid for pid, mat in pile_material_map.items() if mat == ore_type]
            id_pile = random.choice(valid_piles)
            id_stockpile = pile_to_stockpile_map.get(id_pile, 1)

            ritase = random.randint(5, 16)
            tonnage = round(ritase * 20, 2)
            ton_barge_load = tonnage
            ton_barge_unload = round(ton_barge_load - random.uniform(0, 5), 2)
            base_date = start_date + timedelta(days=random.randint(0, date_range))

            barging = SellingBarging(
                id=uuid.uuid4(),
                date_barge_in=base_date,
                date_barge_out=base_date + timedelta(days=random.randint(1, 3)),
                barge_code=random.randint(1, 2),
                barging_load_loc=random.choice(['Jetty Kawi']),
                barging_unload_loc=random.choice(['Factory A', 'Factory B']),
                date_hauling=base_date - timedelta(days=random.randint(1, 2)),
                shift=random.choice(shifts),
                id_material=material_id,
                id_stockpile=id_stockpile,
                id_pile=id_pile,
                unit_code=f"TRK-{random.randint(100, 999)}",
                ritase=ritase,
                tonnage=tonnage,
                ton_barge_load=ton_barge_load,
                ton_barge_unload=ton_barge_unload,
                fill_adjust=round(random.uniform(-2, 2), 2),
                batch=f"BATCH-{random.randint(1, 100)}",
                nota=f"NOTA-{random.randint(1000, 9999)}",
                id_factory=random.randint(1, 3),
                type_selling=type_selling,
                sale_adjust=type_selling,  # ✅ isinya HPAL atau RKEF
                code_inc=f"INC-{random.randint(1000, 9999)}",
                code_sub=f"SUB-{random.randint(1000, 9999)}",
                code_batch=f"CB-{random.randint(1000, 9999)}",
                code_batch_pulp=f"PULP-{random.randint(1000, 9999)}",
                surv_order=f"SURV-{random.randint(1000, 9999)}",
                code_fix_batch=f"FIX-{random.randint(1000, 9999)}",
                code_barging=f"BARGING-{random.randint(1000, 9999)}",
                haulage_code=f"HAUL-{random.randint(1000, 9999)}",
                date_barging=base_date + timedelta(days=random.randint(1, 5)),
                id_user=random.randint(1, 10),
                sale_dome=random.choice(['Yes']),
                remarks='Generated dummy data selling'
            )
            bulk_data.append(barging)

        SellingBarging.objects.bulk_create(bulk_data, batch_size=100)
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(bulk_data)} SellingBarging records.'))
