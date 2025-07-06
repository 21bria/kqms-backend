import uuid
import random
from django.contrib.gis.geos import Polygon
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.http import JsonResponse
from ..models.ore_productions import OreProductions
from kqms.models import SourceMinesDome,SourceMinesDumping,SourceMines,SourceMinesLoading
from kqms.models import SellingProductions
from kqms.models import SellingPlan
from kqms.models import mineProductions
from kqms.models import planProductions


def random_date(start, end):
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)

def generate_dummy_ore(request):
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2025, 6, 29)

    shifts = ['day', 'night']
    batch_status_choices = ['Complete', 'Incomplete']
    status_dome_choices = ['Close', 'Continue']
    categories = ['Mining', 'Project']
    materials = [7, 10]

    current_date = start_date
    bulk_data = []

    while current_date <= end_date:
        category = random.choice(categories)
        mat_id = random.choice(materials)

        ore_class = (
            random.choice(['LGLO', 'MGLO', 'HGLO']) if mat_id == 7
            else random.choice(['LGSO', 'MGSO', 'HGSO'])
        )

        data = OreProductions(
            id=uuid.uuid4(),
            tgl_production=current_date.date(),
            shift=random.choice(shifts),
            id_prospect_area=random.randint(1, 5),
            id_block=random.randint(1000, 9999),
            from_rl='RL1',
            to_rl='RL2',
            id_material=mat_id,
            grade_expect=round(random.uniform(1.0, 2.5), 2),
            grade_control='G1',
            unit_truck='DT30',
            id_stockpile=random.randint(1, 10),
            id_pile=random.randint(1, 20),
            batch_code=f'BATCH-{random.randint(1, 30)}',
            increment=random.randint(7, 15),
            batch_status=random.choice(batch_status_choices),
            ritase=random.randint(1, 8),
            tonnage=round(random.uniform(50.0, 200.0), 2),
            pile_status=random.choice(status_dome_choices),
            kode_batch=None,
            pile_original=None,
            stockpile_ori=None,
            left_date=current_date.day,
            no_production=None,
            truck_factor='DT30',
            ore_class=ore_class,
            batch_status_set=None,
            dome_compositing=None,
            stock_compositing=None,
            status_dome=random.choice(status_dome_choices),
            sale_adjust=None,
            remarks=None,
            id_user=1,
            status_approval='approved',
            category=category,
        )
        bulk_data.append(data)

        if len(bulk_data) >= 1000:
            OreProductions.objects.bulk_create(bulk_data)
            bulk_data = []

        current_date += timedelta(days=1)

    if bulk_data:
        OreProductions.objects.bulk_create(bulk_data)

    return JsonResponse({"status": "success", "message": "✅ Data dummy 5 tahun berhasil dibuat dengan ore_class dan category random sesuai material"})

def generate_dummy_dome(request):
    pile_ids = [f'PILE-{i}' for i in range(1, 21)]  # PILE-1 s/d PILE-20

    categories = ['Mining', 'Project']
    compositing_choices = ['Yes', 'No']
    status_dome_choices = ['Close', 'Continue']

    domes = []
    for pile in pile_ids:
        dome = SourceMinesDome(
            pile_id=pile,
            remarks='Dummy dome',
            category=random.choice(categories),
            compositing=random.choice(compositing_choices),
            dome_finish=None,
            status_dome=random.choice(status_dome_choices),
            plan_ni_min=round(random.uniform(1.0, 1.4), 2),
            plan_ni_max=round(random.uniform(1.5, 2.2), 2),
            status=1,
            direct_sale=random.choice(['Yes', 'No']),
            id_dumping=random.randint(100, 200),
            latitude=round(random.uniform(-1.0, 1.0), 10),
            longitude=round(random.uniform(120.0, 125.0), 10)
        )
        domes.append(dome)

    SourceMinesDome.objects.bulk_create(domes)
    return JsonResponse({"status": "success", "message": "✅ Dummy data dome berhasil dibuat!"})

def generate_dummy_stockpile(request):
    stockpile_ids = [f'STOCKPILE-{i}' for i in range(1, 11)]  # STOCKPILE-1 to STOCKPILE-10
    categories = ['Mining', 'Project']
    compositing_choices = ['Yes', 'No']

    stockpiles = []
    for name in stockpile_ids:
        stockpile = SourceMinesDumping(
            dumping_point=name,
            remarks='Dummy stockpile',
            category=random.choice(categories),
            compositing=random.choice(compositing_choices),
            status=1,
            latitude=round(random.uniform(-1.0, 1.0), 10),
            longitude=round(random.uniform(120.0, 125.0), 10)
        )
        stockpiles.append(stockpile)

    SourceMinesDumping.objects.bulk_create(stockpiles)
    return JsonResponse({"status": "success", "message": "✅ Dummy data stockpile berhasil dibuat!"})

def generate_dummy_loading(request):
    loading_names = [f'PIT-{i}' for i in range(1, 6)]
    categories = ['Mining', 'Project']

    dummy_source = SourceMines.objects.first()
    if not dummy_source:
        return JsonResponse({
            "status": "error",
            "message": "⚠️ Tidak ada data SourceMines (prospect_area), buat dulu!"
        })

    loadings = []
    for i, name in enumerate(loading_names):
        base_lng = 128.480 + i * 0.002
        base_lat = -0.430 - i * 0.002

        # Buat 5 titik polygon valid (harus kembali ke titik awal)
        ring = [
            (base_lng, base_lat),
            (base_lng + 0.001, base_lat),
            (base_lng + 0.001, base_lat - 0.001),
            (base_lng, base_lat - 0.001),
            (base_lng, base_lat)  # titik awal lagi
        ]

        polygon = Polygon([ring])  # harus nested list!

        loading = SourceMinesLoading(
            loading_point=name,
            remarks='Dummy loading point',
            category=random.choice(categories),
            id_sources=dummy_source,
            status=1,
            latitude=base_lat,
            longitude=base_lng,
            geometry=polygon
        )
        loadings.append(loading)

    SourceMinesLoading.objects.bulk_create(loadings)
    return JsonResponse({
        "status": "success",
        "message": "Dummy loading point berhasil dibuat!"
    })

# Selling
def generate_dummy_selling(request, total=4000):
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2025, 6, 29)

    type_selling_choices = ['HPAL', 'RKEF']
    shifts = ['Day', 'Night']
    bulk_data = []

    for _ in range(total):
        tgl = random_date(start_date, end_date).date()
        jam = random.randint(0, 23)
        menit = random.randint(0, 59)
        time_hauling = time(hour=jam, minute=menit)

        empty_w = round(random.uniform(12.0, 16.0), 2)
        fill_w = empty_w + round(random.uniform(8.0, 15.0), 2)
        netto_w = round(fill_w - empty_w, 2)

        data = SellingProductions(
            id=uuid.uuid4(),
            tgl_hauling=tgl,
            time_hauling=time_hauling,
            shift=random.choice(shifts),
            id_material=random.choice([7, 10]),
            id_stockpile=random.randint(1, 3),
            id_pile=random.randint(1, 6),
            unit_code=f"TRK-{random.randint(100, 999)}",
            empety_weigth=empty_w,
            fill_weigth=fill_w,
            netto_weigth=netto_w,
            qa_control=f"QA-{random.randint(1, 10)}",
            batch=f"BATCH-{random.randint(1000, 9999)}",
            delivery_order=f"DO-{random.randint(10000, 99999)}",
            nota=f"NOTA-{random.randint(1000, 9999)}",
            id_factory=random.randint(1, 5),
            type_selling=random.choice(type_selling_choices),
            empety_weigth_f=empty_w,
            fill_weigth_f=fill_w,
            netto_weigth_f=netto_w,
            ore_transport=f"OT-{random.randint(1, 10)}",
            id_stock_temp=random.randint(1, 5),
            id_dome_temp=random.randint(1, 5),
            no_input=f"IN-{random.randint(100, 999)}",
            remarks="Dummy generated for testing",
            batch_g=f"G-{random.randint(1000, 9999)}",
            kode_batch_g=f"KBG-{random.randint(10000, 99999)}",
            left_date=random.randint(0, 10),
            new_awk=f"AWK-{random.randint(1, 50)}",
            new_awk_sub=f"SUBAWK-{random.randint(100, 999)}",
            new_kode_batch_awk=f"AKB-{random.randint(1000, 9999)}",
            new_batch_awk_pulp=f"PULP-{random.randint(1000, 9999)}",
            awk_order=str(random.randint(1, 10)),
            load_code=f"LOAD-{random.randint(1, 10)}",
            haulage_code=f"HAUL-{random.randint(1, 10)}",
            date_wb=tgl,
            timbang_isi=datetime.combine(tgl, time_hauling),
            timbang_kosong=datetime.combine(tgl, time_hauling) - timedelta(minutes=5),
            id_user=random.randint(1, 10),
            sale_adjust=random.choice(['Y', 'N']),
            sale_dome=random.choice(['A', 'B', 'C']),
        )

        bulk_data.append(data)

    # Eksekusi bulk insert
    SellingProductions.objects.bulk_create(bulk_data)

    return JsonResponse({
        "status": "success",
        "message": f"✅ {total} dummy selling rows berhasil dibuat via bulk_create"
    })

def generate_dummy_selling_plan(request):
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2025, 6, 29)

    type_ores = ['LIM', 'SAP']  # Material 7 = limonite, 10 = saprolite (misal)
    type_sellings = ['HPAL', 'RKEF']

    current_date = start_date
    bulk_data = []

    while current_date <= end_date:
        type_selling = random.choice(type_sellings)
        type_ore = random.choice(type_ores)

        tonnage = round(random.uniform(1000, 5000), 2)
        ni_plan = round(random.uniform(1.2, 2.0), 2)
        ni_buyer = round(ni_plan + random.uniform(-0.1, 0.1), 2)
        ni_surveyor = round(ni_plan + random.uniform(-0.1, 0.1), 2)

        plan = SellingPlan(
            id=uuid.uuid4(),
            plan_date=current_date.date(),
            type_ore=type_ore,
            type_selling=type_selling,
            tonnage_plan=tonnage,
            ni_plan=ni_plan,
            ni_buyer=ni_buyer,
            ni_surveyor=ni_surveyor,
            check_duplicated=f"{type_selling}_{current_date.strftime('%Y%m%d')}",
            description="Dummy selling plan for simulation",
            left_date=current_date.day,
            id_user=random.randint(1, 5)
        )
        bulk_data.append(plan)

        # Insert per 1000
        if len(bulk_data) >= 1000:
            SellingPlan.objects.bulk_create(bulk_data)
            bulk_data = []

        current_date += timedelta(days=1)

    # Final bulk insert
    if bulk_data:
        SellingPlan.objects.bulk_create(bulk_data)

    return JsonResponse({
        "status": "success",
        "message": "✅ Dummy SellingPlan berhasil dibuat untuk seluruh rentang tanggal."
    })

# Mining
def generate_dummy_plan_productions(request):
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2025, 6, 29)

    vendors_list = ['PPA', 'NPM']
    categories = ['Mining', 'Project']
    sources = ['Pit A', 'Pit B', 'Pit C', 'Pit D']

    material_fields = [
        'topsoil', 'ob', 'lglo', 'mglo', 'hglo', 'waste', 'mws',
        'lgso', 'uglo', 'mgso', 'hgso', 'quarry', 'ballast', 'biomass'
    ]

    current_date = start_date
    bulk_data = []

    while current_date <= end_date:
        data = planProductions(
            id=uuid.uuid4(),
            date_plan=current_date.date(),
            category=random.choice(categories),
            sources=random.choice(sources),
            vendors=random.choice(vendors_list),
            ref_plan=f"PLAN-{current_date.strftime('%Y%m%d')}",
            id_user=random.randint(1, 5)
        )

        for field in material_fields:
            setattr(data, field, round(random.uniform(0, 200), 2))

        bulk_data.append(data)

        if len(bulk_data) >= 1000:
            planProductions.objects.bulk_create(bulk_data)
            bulk_data = []

        current_date += timedelta(days=1)

    if bulk_data:
        planProductions.objects.bulk_create(bulk_data)

    return JsonResponse({
        "status": "success",
        "message": "✅ Dummy planProductions berhasil dibuat selama periode tanggal yang ditentukan."
    })

def generate_dummy_mine_productions(request):
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2025, 6, 29)

    materials = [18, 27, 28, 29, 30, 31, 32, 33, 34, 35]
    vendors = ['Vendor A', 'Vendor B', 'Vendor C']
    hauler_classes = ['DT', 'ADT']
    categories = ['Mining', 'Project']
    shifts = ['Day', 'Night']

    current_date = start_date
    bulk_data = []

    while current_date <= end_date:
        # Ambil nilai planProductions untuk tanggal tersebut
        plan = planProductions.objects.filter(date_plan=current_date.date()).first()

        if plan:
            plan_total = sum([
                getattr(plan, field) or 0
                for field in [
                    'topsoil', 'ob', 'lglo', 'mglo', 'hglo', 'waste',
                    'mws', 'lgso', 'uglo', 'mgso', 'hgso', 'quarry',
                    'ballast', 'biomass'
                ]
            ])
        else:
            plan_total = random.uniform(100, 300)  # fallback jika tidak ada data plan

        target_actual_total = plan_total * random.uniform(0.9, 1.1)  # ±10%
        target_actual_total = round(target_actual_total, 2)

        # Bagi rata target tonase ke jumlah ritase per hari (misalnya 3)
        tonnage_per_ritase = target_actual_total / 3

        for _ in range(3):
            jam = random.randint(5, 22)
            menit = random.randint(0, 59)
            loading_time = time(hour=jam, minute=menit)
            dumping_time = time(hour=(jam + 1) % 24, minute=(menit + 10) % 60)

            ton = round(tonnage_per_ritase * random.uniform(0.9, 1.1), 2)
            bcm = round(ton / random.uniform(1.2, 1.8), 2)

            from_rl = random.randint(90, 120)
            to_rl = from_rl + random.randint(5, 15)

            data = mineProductions(
                id=uuid.uuid4(),
                date_production=current_date.date(),
                vendors=random.choice(vendors),
                shift=random.choice(shifts),
                loader=f"LD-{random.randint(1, 10)}",
                hauler=f"HL-{random.randint(100, 999)}",
                hauler_class=random.choice(hauler_classes),
                sources_area=1,
                loading_point=random.randint(1, 3),
                dumping_point=random.randint(1, 10),
                dome_id=random.randint(1, 20),
                distance=f"{round(random.uniform(0.5, 5.0), 2)} KM",
                category_mine=random.choice(categories),
                time_dumping=dumping_time.strftime("%H:%M"),
                time_loading=loading_time,
                left_loading=str(random.randint(0, 5)),
                block_id=f"BLK-{random.randint(1000, 9999)}",
                from_rl=str(from_rl),
                to_rl=str(to_rl),
                id_material=random.choice(materials),
                ritase=1,
                bcm=bcm,
                tonnage=ton,
                remarks="Generated dummy",
                hauler_type=random.choice(['Nissan', 'Scania', 'Volvo']),
                ref_materials=f"REF-{random.randint(1000, 9999)}",
                no_production=f"PROD-{random.randint(100000, 999999)}",
                left_date=current_date.day,
                id_user=1
            )
            bulk_data.append(data)

        if len(bulk_data) >= 1000:
            mineProductions.objects.bulk_create(bulk_data)
            bulk_data = []

        current_date += timedelta(days=1)

    if bulk_data:
        mineProductions.objects.bulk_create(bulk_data)

    return JsonResponse({
        "status": "success",
        "message": "✅ Data dummy produksi mining disesuaikan dengan plan berhasil dibuat."
    })