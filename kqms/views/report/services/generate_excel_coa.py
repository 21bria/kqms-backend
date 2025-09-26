# reports/views.py
from io import BytesIO
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from datetime import date
import xlsxwriter
from .get_compare_coa import (
    fetch_official_split,
    fetch_official_split_year,
)

def excel_unified_coa(request):
    mode       = request.GET.get("mode") or "range"   # default: range
    date_start = request.GET.get("date_start") or str(date.today().replace(day=1))
    date_end   = request.GET.get("date_end")   or str(date.today())
    year       = request.GET.get("year")       # untuk mode=year
    material   = request.GET.get("material") 

    # Ambil data
    if mode == "range":
        data_coa = fetch_official_split(date_start, date_end, material)
    elif mode == "year" and year:
        try:
            year = int(year)
        except ValueError:
            return HttpResponseBadRequest("Invalid year parameter")
        data_coa = fetch_official_split_year(year, material)
    else:
        return HttpResponseBadRequest("Invalid mode or missing parameters")


    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})

    # Styles
    fmt_title = workbook.add_format({'bold': True, 'font_size': 14})
    fmt_th    = workbook.add_format({'bold': True, 'bg_color': '#F3F4F6', 'border': 1})
    fmt_td    = workbook.add_format({'border': 1})
    fmt_num   = workbook.add_format({'border': 1, 'num_format': '#,##0'})
    fmt_dec2  = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
    fmt_small = workbook.add_format({'font_size': 9, 'italic': True, 'font_color': '#6B7280'})

    # === Sheet Data_COA
    ws_coa = workbook.add_worksheet("Official_vs_Split")

    headers = [
        "Date In","Code Lot","Barge Code","Barge Name","Tonnage Split","Ni Split","Fe Split","MgO Split","SiO₂ Split",
        "Tonnage Official","Ni Official","Fe Official","MgO Official","SiO₂ Official",
        "Tonnage Diff","Ni Diff %","Fe Diff %","MgO Diff %","SiO₂ Diff %"
    ]

    # Header di baris 0
    ws_coa.write_row(0, 0, headers, fmt_th)

    # bikin format tanggal
    fmt_date = workbook.add_format({'num_format': 'yyyy-mm-dd', 'border': 1})

    # Data mulai baris 1
    for row_idx, r in enumerate(data_coa["rows"], start=1):
        # tanggal (kolom A / index 0)
        date_val = r.get("date_barge_in")
        if date_val:
            try:
                ws_coa.write_datetime(row_idx, 0, date_val, fmt_date)
            except Exception:
                # fallback kalau date_val masih string
                from datetime import datetime
                try:
                    parsed = datetime.strptime(str(date_val), "%Y-%m-%d")
                    ws_coa.write_datetime(row_idx, 0, parsed, fmt_date)
                except:
                    ws_coa.write(row_idx, 0, str(date_val))
        else:
            ws_coa.write(row_idx, 0, "")

        # sisanya tetap sama
        ws_coa.write(row_idx, 1, r.get("code_lot"))
        ws_coa.write(row_idx, 2, r.get("barge_code"))
        ws_coa.write(row_idx, 3, r.get("barge_name"))
        ws_coa.write_number(row_idx, 4, r.get("tonnage_split") or 0)
        ws_coa.write_number(row_idx, 5, r.get("ni_split") or 0)
        ws_coa.write_number(row_idx, 6, r.get("fe_split") or 0)
        ws_coa.write_number(row_idx, 7, r.get("mgo_split") or 0)
        ws_coa.write_number(row_idx, 8, r.get("sio2_split") or 0)
        ws_coa.write_number(row_idx, 9, r.get("tonnage_official") or 0)
        ws_coa.write_number(row_idx, 10, r.get("ni_official") or 0)
        ws_coa.write_number(row_idx, 11, r.get("fe_official") or 0)
        ws_coa.write_number(row_idx, 12, r.get("mgo_official") or 0)
        ws_coa.write_number(row_idx, 13, r.get("sio2_official") or 0)
        ws_coa.write_number(row_idx, 14, r.get("tonnage_diff") or 0)
        ws_coa.write_number(row_idx, 15, r.get("ni_diff") or 0)
        ws_coa.write_number(row_idx, 16, r.get("fe_diff") or 0)
        ws_coa.write_number(row_idx, 17, r.get("mgo_diff") or 0)
        ws_coa.write_number(row_idx, 18, r.get("sio2_diff") or 0)

    # atur lebar kolom
    ws_coa.set_column('A:A', 15)   # tanggal
    ws_coa.set_column('B:B', 15)   # code lot
    ws_coa.set_column('C:D', 20)   # barge_code + barge_name
    ws_coa.set_column('E:S', 14)   # angka

    # tambahkan blok summary :

    # === Sheet Summary Official vs Split ===
    ws_sum_coa = workbook.add_worksheet('Chart')
    ws_sum_coa.hide_gridlines(2)   # 2 = hide both screen & print
    ws_sum_coa.write('A1', 'Official vs Split COA', fmt_title)
    ws_sum_coa.write('A2', f'Range: {date_start} → {date_end}', fmt_small)

    # ws_sum_coa.write_row('A4', ['Metric','Split','Official','Diff %'], fmt_th)

    # Hitung summary total
    total_split_ni  = sum(r["ni_split"]  or 0 for r in data_coa["rows"])
    total_split_fe  = sum(r["fe_split"]  or 0 for r in data_coa["rows"])
    total_split_mgo = sum(r["mgo_split"] or 0 for r in data_coa["rows"])
    total_split_sio2= sum(r["sio2_split"]or 0 for r in data_coa["rows"])

    total_off_ni  = sum(r["ni_official"]  or 0 for r in data_coa["rows"])
    total_off_fe  = sum(r["fe_official"]  or 0 for r in data_coa["rows"])
    total_off_mgo = sum(r["mgo_official"] or 0 for r in data_coa["rows"])
    total_off_sio2= sum(r["sio2_official"]or 0 for r in data_coa["rows"])

    # Selisih %
    ni_diff  = ((total_split_ni - total_off_ni) / total_off_ni * 100) if total_off_ni else 0
    fe_diff  = ((total_split_fe - total_off_fe) / total_off_fe * 100) if total_off_fe else 0
    mgo_diff = ((total_split_mgo - total_off_mgo) / total_off_mgo * 100) if total_off_mgo else 0
    sio2_diff= ((total_split_sio2 - total_off_sio2) / total_off_sio2 * 100) if total_off_sio2 else 0

    rows_summary = [
        ("Ni", total_split_ni, total_off_ni, ni_diff),
        ("Fe", total_split_fe, total_off_fe, fe_diff),
        ("MgO", total_split_mgo, total_off_mgo, mgo_diff),
        ("SiO₂", total_split_sio2, total_off_sio2, sio2_diff),
    ]

    # for idx, (metric, split_val, off_val, diff_val) in enumerate(rows_summary, start=5):
    #     ws_sum_coa.write(f"A{idx}", metric, fmt_td)
    #     ws_sum_coa.write_number(f"B{idx}", split_val, fmt_dec2)
    #     ws_sum_coa.write_number(f"C{idx}", off_val, fmt_dec2)
    #     ws_sum_coa.write_number(f"D{idx}", diff_val, fmt_dec2)

    # ws_sum_coa.set_column('A:D', 18)

    # === Chart Ni Internal vs Official ===
    chart_ni = workbook.add_chart({'type': 'column'})
    chart_ni.set_title({'name': 'Internal vs Official (Ni%)'})
    chart_ni.set_legend({'position': 'bottom'})

    chart_ni.add_series({
        'name': 'Ni Internal',
        'categories': f"=Official_vs_Split!$C$2:$C${len(data_coa['rows'])+1}",
        'values':     f"=Official_vs_Split!$F$2:$F${len(data_coa['rows'])+1}",
        'fill': {'color': '#3b82f6'}  # biru
    })
    chart_ni.add_series({
        'name': 'Ni Official',
        'categories': f"=Official_vs_Split!$C$2:$C${len(data_coa['rows'])+1}",
        'values':     f"=Official_vs_Split!$K$2:$K${len(data_coa['rows'])+1}",
        'fill': {'color': '#f59e0b'}  # oranye
    })

    # Insert ke Summary
    ws_sum_coa.insert_chart('B5', chart_ni, {'x_scale': 1.7, 'y_scale': 1.2})


    # === Chart Fe Internal vs Official ===
    chart_fe = workbook.add_chart({'type': 'column'})
    chart_fe.set_title({'name': 'Internal vs Official (Fe%)'})
    chart_fe.set_legend({'position': 'bottom'})

    chart_fe.add_series({
        'name': 'Fe Internal',
        'categories': f"=Official_vs_Split!$C$2:$C${len(data_coa['rows'])+1}",
        'values':     f"=Official_vs_Split!$G$2:$G${len(data_coa['rows'])+1}",
        'fill': {'color': '#3b82f6'}
    })
    chart_fe.add_series({
        'name': 'Fe Official',
        'categories': f"=Official_vs_Split!$C$2:$C${len(data_coa['rows'])+1}",
        'values':     f"=Official_vs_Split!$L$2:$L${len(data_coa['rows'])+1}",
        'fill': {'color': '#f59e0b'}
    })

    # Insert ke Summary (letakkan agak bawah)
    ws_sum_coa.insert_chart('P5', chart_fe, {'x_scale': 1.7, 'y_scale': 1.2})

    # === Chart MgO Internal vs Official ===
    chart_mgo = workbook.add_chart({'type': 'column'})
    chart_mgo.set_title({'name': 'Internal vs Official (MgO%)'})
    chart_mgo.set_legend({'position': 'bottom'})

    chart_mgo.add_series({
        'name': 'MgO Internal',
        'categories': f"=Official_vs_Split!$C$2:$C${len(data_coa['rows'])+1}",
        'values':     f"=Official_vs_Split!$H$2:$H${len(data_coa['rows'])+1}",
        'fill': {'color': '#3b82f6'}
    })
    chart_mgo.add_series({
        'name': 'MgO Official',
        'categories': f"=Official_vs_Split!$C$2:$C${len(data_coa['rows'])+1}",
        'values':     f"=Official_vs_Split!$M$2:$M${len(data_coa['rows'])+1}",
        'fill': {'color': '#f59e0b'}
    })

    # Insert ke Summary (letakkan agak bawah)
    ws_sum_coa.insert_chart('B25', chart_mgo, {'x_scale': 1.7, 'y_scale': 1.2})

     # === Chart SiO2 Internal vs Official ===
    chart_sio2 = workbook.add_chart({'type': 'column'})
    chart_sio2.set_title({'name': 'Internal vs Official (SiO2%)'})
    chart_sio2.set_legend({'position': 'bottom'})

    chart_sio2.add_series({
        'name': 'SiO2 Internal',
        'categories': f"=Official_vs_Split!$C$2:$C${len(data_coa['rows'])+1}",
        'values':     f"=Official_vs_Split!$I$2:$I${len(data_coa['rows'])+1}",
        'fill': {'color': '#3b82f6'}
    })
    chart_sio2.add_series({
        'name': 'SiO2 Official',
        'categories': f"=Official_vs_Split!$C$2:$C${len(data_coa['rows'])+1}",
        'values':     f"=Official_vs_Split!$N$2:$N${len(data_coa['rows'])+1}",
        'fill': {'color': '#f59e0b'}
    })

    # Insert ke Summary (letakkan agak bawah)
    ws_sum_coa.insert_chart('P25', chart_sio2, {'x_scale': 1.7, 'y_scale': 1.2})


    # Close workbook
    workbook.close()
    output.seek(0)

    filename = f"KQMS-summary_COA_{date_start}_to_{date_end}.xlsx"
    resp = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp
