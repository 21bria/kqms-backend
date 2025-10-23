import os
import uuid
import pandas as pd
from celery import shared_task
from django.conf import settings
import re
# from ..models.selling_plan_barging import SellingPlanBarging
# from ..models.task_model import taskImports
from kqms.models import BargingPlan, taskImports  # pastikan import sesuai
from datetime import datetime
from datetime import datetime
from django.utils import timezone
from django.db import transaction

import pandas as pd
import re

def read_barging_header(file_path):
    # Baca 10 baris awal untuk deteksi
    preview = pd.read_excel(file_path, nrows=10, header=None, dtype=str)
    preview = preview.fillna("")

    header_row_index = None
    for i, row in preview.iterrows():
        joined = " ".join(row.astype(str)).upper()
        if "DATE" in joined and ("WMT" in joined or "TONNAGE" in joined):
            header_row_index = i
            break

    if header_row_index is None:
        raise ValueError("Tidak dapat menemukan baris header yang valid (tidak ada DATE / WMT).")

    # Sekarang baca ulang file dengan header di baris yang ditemukan
    df = pd.read_excel(file_path, header=header_row_index)
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]
    print("DETECTED HEADER ROW:", header_row_index)
    print("COLUMNS:", df.columns.tolist())
    return df

@shared_task(name='kqms.task.import_barging_plan.import_barging_plan')
def import_barging_plan(file_path, id_user, year=None, month=None):
    errors = []
    duplicates = []
    duplicate_rows = []
    list_objects = []
    successful_imports = 0
    duplicate_imports = 0

    try:
        # --- 1️⃣ Baca dulu dua baris pertama untuk header mentah
        # preview = pd.read_excel(file_path, nrows=2, header=None, dtype=str)
        # header_rows = preview.fillna("").values.tolist()
        df = read_barging_header(file_path)

        # Pastikan dua baris punya panjang sama
        # max_len = max(len(header_rows[0]), len(header_rows[1]))
        # row1 = (header_rows[0] + [""] * (max_len - len(header_rows[0])))[:max_len]
        # row2 = (header_rows[1] + [""] * (max_len - len(header_rows[1])))[:max_len]

        # # --- 2️⃣ Gabungkan dua baris header jadi satu baris yang rapi
        # combined_header = []
        # for a, b in zip(row1, row2):
        #     a = str(a).strip()
        #     b = str(b).strip()
        #     header = f"{a} {b}".strip()
        #     header = re.sub(r"\s+", " ", header)
        #     combined_header.append(header or "Unnamed")

        # # --- 3️⃣ Baca ulang file dengan header gabungan
        # df = pd.read_excel(file_path, skiprows=2, header=None)
        # df = df.iloc[:, :len(combined_header)]  # jaga agar jumlah kolom sesuai header
        # df.columns = combined_header

        print("HEADER COLUMNS:", df.columns.tolist())

        # --- 4️⃣ Pastikan ada kolom DATE
        date_col = next((c for c in df.columns if "DATE" in c.upper()), None)
        if not date_col:
            raise ValueError(f"Tidak menemukan kolom DATE. Kolom yang ada: {df.columns.tolist()}")

        # --- 5️⃣ Deteksi kolom tonase
        tonnage_cols = [c for c in df.columns if re.search(r"(TONNAGE|WMT)", c, re.IGNORECASE)]
        if not tonnage_cols:
            raise ValueError(f"Tidak menemukan kolom tonase. Kolom yang ada: {df.columns.tolist()}")

        year = int(year or datetime.today().year)
        month = int(month or datetime.today().month)

        # --- 6️⃣ Proses data
        with transaction.atomic():
            for _, row in df.iterrows():
                date_val = row[date_col]
                if pd.isna(date_val):
                    continue

                try:
                    plan_date = pd.to_datetime(str(date_val)).date()
                except Exception:
                    continue

                for col in tonnage_cols:
                    tonnage = row[col]
                    if pd.isna(tonnage) or tonnage == 0:
                        continue

                    # Ambil nama tug dan barge dari header kolom
                    header = col.split("Tonnage")[0].split("(wmt)")[0].strip()
                    tug_name, barge_name = None, None
                    if " - " in header:
                        parts = header.split(" - ", 1)
                        tug_name = parts[0].replace("TB.", "").strip()
                        barge_name = parts[1].replace("BG.", "").strip()

                    check_dup = f"{plan_date}_{tug_name}_{barge_name}"

                    if BargingPlan.objects.filter(check_duplicated=check_dup).exists():
                        duplicates.append(f"{plan_date} - {tug_name} - {barge_name}")
                        duplicate_rows.append(row.to_dict())
                        duplicate_imports += 1
                        continue

                    obj = BargingPlan(
                        plan_date=plan_date,
                        tugboat_name=tug_name,
                        barge_name=barge_name,
                        tonnage_plan=float(tonnage),
                        description=f"{tug_name} - {barge_name}",
                        check_duplicated=check_dup,
                        id_user=id_user,
                    )
                    list_objects.append(obj)
                    successful_imports += 1

            # --- Simpan bulk
            if list_objects:
                BargingPlan.objects.bulk_create(list_objects, batch_size=200)

            # --- Simpan duplikat ke file excel
            duplicate_file_path = None
            if duplicate_rows:
                dup_df = pd.DataFrame(duplicate_rows)
                filename = f"duplicates_{uuid.uuid4().hex}.xlsx"
                duplicate_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_duplicates')
                os.makedirs(duplicate_dir, exist_ok=True)
                duplicate_file_path = os.path.join(duplicate_dir, filename)
                dup_df.to_excel(duplicate_file_path, index=False)

        return {
            "message": "Import completed",
            "successful_imports": successful_imports,
            "failed_imports": len(errors),
            "duplicate_imports": duplicate_imports,
            "errors": errors,
            "duplicates": duplicates,
            "duplicate_file": duplicate_file_path,
        }

    except Exception as e:
        errors.append(f"Transaction failed: {str(e)}")
        return {
            "message": "Import failed",
            "successful_imports": successful_imports,
            "failed_imports": len(errors),
            "duplicate_imports": duplicate_imports,
            "errors": errors,
            "duplicates": duplicates,
            "duplicate_file": None,
        }
