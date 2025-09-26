# reports/views.py
from io import BytesIO
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from datetime import date
import xlsxwriter
from .compile_renge import (
    fetch_production_quality, 
    fetch_selling_quality,
    fetch_production_mining,
    fetch_inventory_balance,
    fetch_inventory_dome,
)
from .compile_year import (
    fetch_production_quality_year, 
    fetch_selling_quality_year,
    fetch_production_mining_year,
    fetch_inventory_balance_year,
    fetch_inventory_dome_year,
)

def excel_unified_summary(request):
    mode       = request.GET.get("mode") or "range"   # default: range
    date_start = request.GET.get("date_start") or str(date.today().replace(day=1))
    date_end   = request.GET.get("date_end")   or str(date.today())
    year       = request.GET.get("year")       # untuk mode=year

    # Ambil data
    if mode == "range":
        mining  = fetch_production_mining(date_start, date_end)
        prod    = fetch_production_quality(date_start, date_end)
        sell    = fetch_selling_quality(date_start, date_end)
        inv     = fetch_inventory_balance(date_start, date_end)
        invlist = fetch_inventory_dome(date_end)
    elif mode == "year" and year:
        try:
            year = int(year)
        except ValueError:
            return HttpResponseBadRequest("Invalid year parameter")
        mining  = fetch_production_mining_year(year)
        prod    = fetch_production_quality_year(year)
        sell    = fetch_selling_quality_year(year)
        inv     = fetch_inventory_balance_year(year)
        invlist = fetch_inventory_dome_year(year)
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

    # === Sheet Data_Mining
    ws_mining = workbook.add_worksheet('Data_Mining')
    ws_mining.write_row('A1', ['Date','LIM','SAP','Waste','Quarry','Topsoil','OB','Ballast','Biomass','Actual Total','Plan Total'], fmt_th)
    for i, r in enumerate(mining["rows"], start=2):
        ws_mining.write(f'A{i}', str(r['dt']), fmt_td)
        ws_mining.write_number(f'B{i}', r['lim'] or 0, fmt_num)
        ws_mining.write_number(f'C{i}', r['sap'] or 0, fmt_num)
        ws_mining.write_number(f'D{i}', r['waste'] or 0, fmt_num)
        ws_mining.write_number(f'E{i}', r['quarry'] or 0, fmt_num)
        ws_mining.write_number(f'F{i}', r['topsoil'] or 0, fmt_num)
        ws_mining.write_number(f'G{i}', r['ob'] or 0, fmt_num)
        ws_mining.write_number(f'H{i}', r['ballast'] or 0, fmt_num)
        ws_mining.write_number(f'I{i}', r['biomass'] or 0, fmt_num)
        ws_mining.write_number(f'J{i}', r['actual_total'] or 0, fmt_num)
        ws_mining.write_number(f'K{i}', r['plan_total'] or 0, fmt_num)
    ws_mining.set_column('A:A', 12)
    ws_mining.set_column('B:K', 12)


    # === Sheet Data_Quality
    ws_quality = workbook.add_worksheet('Data_Quality')
    ws_quality.write_row('A1', ['Date', 'Total', 'LIM', 'SAP'], fmt_th)
    for i, r in enumerate(prod["rows"], start=2):
        ws_quality.write(f'A{i}', str(r['dt']), fmt_td)
        ws_quality.write_number(f'B{i}', r['prod_total'] or 0, fmt_num)
        ws_quality.write_number(f'C{i}', r.get('prod_lim', 0) or 0, fmt_num)
        ws_quality.write_number(f'D{i}', r.get('prod_sap', 0) or 0, fmt_num)
    ws_quality.set_column('A:A', 12)
    ws_quality.set_column('B:D', 12)

    # === Sheet Data_Selling
    ws_sell = workbook.add_worksheet('Data_Selling')
    ws_sell.write_row(
        'A1',
        ['Date', 'Actual LIM', 'Actual SAP', 'Actual Total', 'Plan LIM', 'Plan SAP', 'Plan Total'],
        fmt_th
    )

    for i, r in enumerate(sell["rows"], start=2):
        ws_sell.write(f'A{i}', str(r['dt']), fmt_td)
        ws_sell.write_number(f'B{i}', r.get('actual_lim', 0) or 0, fmt_num)
        ws_sell.write_number(f'C{i}', r.get('actual_sap', 0) or 0, fmt_num)
        ws_sell.write_number(f'D{i}', r.get('actual_total', 0) or 0, fmt_num)
        ws_sell.write_number(f'E{i}', r.get('plan_lim', 0) or 0, fmt_num)
        ws_sell.write_number(f'F{i}', r.get('plan_sap', 0) or 0, fmt_num)
        ws_sell.write_number(f'G{i}', r.get('plan_total', 0) or 0, fmt_num)

    ws_sell.set_column('A:A', 12)
    ws_sell.set_column('B:G', 15)


    # === Sheet Stock_Opname
    ws_inv = workbook.add_worksheet('Stock_Opname')
    ws_inv.write_row('A1', ['Date', 'Production In', 'Selling Out', 'Stock Opname'], fmt_th)

    for i, r in enumerate(inv["rows"], start=2):
        ws_inv.write(f'A{i}', str(r['dt']), fmt_td)
        ws_inv.write_number(f'B{i}', r['total_in'] or 0, fmt_num)       # Production In
        ws_inv.write_number(f'C{i}', r['total_out'] or 0, fmt_num)      # Selling Out
        ws_inv.write_number(f'D{i}', r['running_balance'] or 0, fmt_num) # Stock Opname

    ws_inv.set_column('A:A', 12)
    ws_inv.set_column('B:D', 16)

    # === Sheet Data_Inventory (by dome / pile)
    ws_invlist = workbook.add_worksheet('Data_Inventory')
    ws_invlist.write_row(
        'A1',
        ['Stockpile', 'Pile ID', 'Material', 'Total Ore', 'Released',
        'Total Selling', 'Balance', 'Ni', 'Co', 'Fe', 'MgO', 'SiO2', 'SM'],
        fmt_th
    )

    for i, r in enumerate(invlist["rows"], start=2):
        ws_invlist.write(f'A{i}', r['stockpile'], fmt_td)
        ws_invlist.write(f'B{i}', r['pile_id'], fmt_td)
        ws_invlist.write(f'C{i}', r['nama_material'], fmt_td)
        ws_invlist.write_number(f'D{i}', r['total_ore'] or 0, fmt_num)
        ws_invlist.write_number(f'E{i}', r['released'] or 0, fmt_num)
        ws_invlist.write_number(f'F{i}', r['total_selling'] or 0, fmt_num)
        ws_invlist.write_number(f'G{i}', r['balance'] or 0, fmt_num)
        ws_invlist.write_number(f'H{i}', float(r['ni'] or 0), fmt_dec2)
        ws_invlist.write_number(f'I{i}', float(r['co'] or 0), fmt_dec2)
        ws_invlist.write_number(f'J{i}', float(r['fe'] or 0), fmt_dec2)
        ws_invlist.write_number(f'K{i}', float(r['mgo'] or 0), fmt_dec2)
        ws_invlist.write_number(f'L{i}', float(r['sio2'] or 0), fmt_dec2)
        ws_invlist.write_number(f'M{i}', float(r['sm'] or 0), fmt_dec2)

    ws_invlist.set_column('A:C', 14)   # stockpile, pile id, material
    ws_invlist.set_column('D:G', 14)   # total ore, released, selling, balance
    ws_invlist.set_column('H:M', 10)   # Ni, Co, Fe, MgO, SiO2, SM


    # tambahkan blok summary Quality, Selling, Mining :

    # === Sheet Summary
    ws_sum = workbook.add_worksheet('Summary')
    ws_sum.hide_gridlines(2)   # 2 = hide both screen & print
    ws_sum.write('A1', 'KQMS Unified Report', fmt_title)
    if mode == "range":
        ws_sum.write('A2', f'Range: {date_start} → {date_end}', fmt_small)
    elif mode == "year":
        ws_sum.write('A2', f'Year: {year}', fmt_small)

    ws_sum.write('F2', f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}', fmt_small)

    # ---------------- Mining Section ----------------
    ws_sum.write('A4', 'Mining Metrics', fmt_title)
    ws_sum.write_row('A5', ['Metric', 'Value'], fmt_th)
    row = 6

    total_actual = sum(r["actual_total"] for r in mining["rows"]) if mining["rows"] else 0
    total_plan   = sum(r["plan_total"] for r in mining["rows"]) if mining["rows"] else 0
    max_day = max(mining["rows"], key=lambda r: r["actual_total"]) if mining["rows"] else None
    min_day = min(mining["rows"], key=lambda r: r["actual_total"]) if mining["rows"] else None

    ws_sum.write(f'A{row}', 'Total Actual', fmt_td); ws_sum.write_number(f'B{row}', total_actual, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Total Plan', fmt_td); ws_sum.write_number(f'B{row}', total_plan, fmt_num); row += 1
    if max_day:
        ws_sum.write(f'A{row}', 'Max day', fmt_td)
        ws_sum.write(f'B{row}', f"{max_day['dt']} • {max_day['actual_total']:.2f}", fmt_td)
        row += 1
    if min_day:
        ws_sum.write(f'A{row}', 'Min day', fmt_td)
        ws_sum.write(f'B{row}', f"{min_day['dt']} • {min_day['actual_total']:.2f}", fmt_td)
        row += 1

    # --- Tambahan: total by material ---
    total_lim     = sum(r["lim"] for r in mining["rows"])
    total_sap     = sum(r["sap"] for r in mining["rows"])
    total_waste   = sum(r["waste"] for r in mining["rows"])
    total_quarry  = sum(r["quarry"] for r in mining["rows"])
    total_topsoil = sum(r["topsoil"] for r in mining["rows"])
    total_ob      = sum(r["ob"] for r in mining["rows"])
    total_ballast = sum(r["ballast"] for r in mining["rows"])
    total_biomass = sum(r["biomass"] for r in mining["rows"])

    ws_sum.write(f'A{row}', 'Total LIM', fmt_td); ws_sum.write_number(f'B{row}', total_lim, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Total SAP', fmt_td); ws_sum.write_number(f'B{row}', total_sap, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Total Waste', fmt_td); ws_sum.write_number(f'B{row}', total_waste, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Total Quarry', fmt_td); ws_sum.write_number(f'B{row}', total_quarry, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Total Topsoil', fmt_td); ws_sum.write_number(f'B{row}', total_topsoil, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Total OB', fmt_td); ws_sum.write_number(f'B{row}', total_ob, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Total Ballast', fmt_td); ws_sum.write_number(f'B{row}', total_ballast, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Total Biomass', fmt_td); ws_sum.write_number(f'B{row}', total_biomass, fmt_num); row += 1

    # Chart Mining (stacked bar + line plan)
    if mining["rows"]:
        first, last = 2, len(mining["rows"]) + 1
        chart_m = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})
        chart_m.set_title({'name': 'Mining Trend'})
        chart_m.set_legend({'position': 'top'})

        for col, name in zip("BCDEFGHI", ['LIM','SAP','Waste','Quarry','Topsoil','OB','Ballast','Biomass']):
            chart_m.add_series({
                'name': name,
                'categories': f'=Data_Mining!$A${first}:$A${last}',
                'values': f'=Data_Mining!${col}${first}:${col}${last}',
            })

        line_chart_m = workbook.add_chart({'type': 'line'})
        line_chart_m.add_series({
            'name': 'Plan',
            'categories': f'=Data_Mining!$A${first}:$A${last}',
            'values': f'=Data_Mining!$K${first}:$K${last}',
        })

        chart_m.combine(line_chart_m)
        ws_sum.insert_chart('E5', chart_m, {'x_scale': 2.07, 'y_scale': 1.32})

    # ================= Quality Summary =================
    ws_sum.write('A26', 'Quality Metrics', fmt_title)
    ws_sum.write_row('A27', ['Metric', 'Value'], fmt_th)
    row = 28

    total_all = sum(r["prod_total"] for r in prod["rows"]) if prod["rows"] else 0
    total_lim = sum(r.get("prod_lim", 0) for r in prod["rows"])
    total_sap = sum(r.get("prod_sap", 0) for r in prod["rows"])
    avg_daily = total_all / len(prod["rows"]) if prod["rows"] else 0
    max_day = max(prod["rows"], key=lambda r: r["prod_total"]) if prod["rows"] else None
    min_day = min(prod["rows"], key=lambda r: r["prod_total"]) if prod["rows"] else None
    pct_lim = (100 * total_lim / total_all) if total_all else 0
    pct_sap = (100 * total_sap / total_all) if total_all else 0

    ws_sum.write(f'A{row}', 'Total tonnage', fmt_td); ws_sum.write_number(f'B{row}', total_all, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Average per day', fmt_td); ws_sum.write_number(f'B{row}', avg_daily, fmt_dec2); row += 1
    ws_sum.write(f'A{row}', 'LIM (total)', fmt_td); ws_sum.write_number(f'B{row}', total_lim, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'LIM (%)', fmt_td); ws_sum.write(f'B{row}', f'{pct_lim:.2f}%', fmt_td); row += 1
    ws_sum.write(f'A{row}', 'SAP (total)', fmt_td); ws_sum.write_number(f'B{row}', total_sap, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'SAP (%)', fmt_td); ws_sum.write(f'B{row}', f'{pct_sap:.2f}%', fmt_td); row += 1
    if max_day:
        ws_sum.write(f'A{row}', 'Max day', fmt_td); ws_sum.write(f'B{row}', f"{max_day['dt']} • {max_day['prod_total']:.2f}", fmt_td); row += 1
    if min_day:
        ws_sum.write(f'A{row}', 'Min day', fmt_td); ws_sum.write(f'B{row}', f"{min_day['dt']} • {min_day['prod_total']:.2f}", fmt_td); row += 1

    # Chart Quality
    if prod["rows"]:
        first, last = 2, len(prod["rows"]) + 1
        chart_q = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})
        chart_q.set_title({'name': 'Quality Trend'})
        chart_q.set_legend({'position': 'top'})
        chart_q.add_series({
            'name': 'LIM',
            'categories': f'=Data_Quality!$A${first}:$A${last}',
            'values': f'=Data_Quality!$C${first}:$C${last}',
            'fill': {'color': '#f4b94a'} 
        })
        chart_q.add_series({
            'name': 'SAP',
            'categories': f'=Data_Quality!$A${first}:$A${last}',
            'values': f'=Data_Quality!$D${first}:$D${last}',
            'fill': {'color': '#34d399'} 
        })
        # line_chart_q = workbook.add_chart({'type': 'line'})
        # line_chart_q.add_series({
        #     'name': 'Total',
        #     'categories': f'=Data_Quality!$A${first}:$A${last}',
        #     'values': f'=Data_Quality!$B${first}:$B${last}',
        # })
        # chart_q.combine(line_chart_q)
        ws_sum.insert_chart('E26', chart_q, {'x_scale': 2.07, 'y_scale': 1.32})

   # ================= Selling Summary =================
    ws_sum.write('A47', 'Selling Metrics', fmt_title)
    ws_sum.write_row('A48', ['Metric', 'Value'], fmt_th)
    row = 49

    total_actual = sum(r["actual_total"] for r in sell["rows"]) if sell["rows"] else 0
    total_plan   = sum(r["plan_total"] for r in sell["rows"]) if sell["rows"] else 0
    lim_actual   = sum(r["actual_lim"] for r in sell["rows"]) if sell["rows"] else 0
    sap_actual   = sum(r["actual_sap"] for r in sell["rows"]) if sell["rows"] else 0
    lim_plan     = sum(r["plan_lim"] for r in sell["rows"]) if sell["rows"] else 0
    sap_plan     = sum(r["plan_sap"] for r in sell["rows"]) if sell["rows"] else 0

    avg_actual   = total_actual / len(sell["rows"]) if sell["rows"] else 0
    max_day = max(sell["rows"], key=lambda r: r["actual_total"]) if sell["rows"] else None
    min_day = min(sell["rows"], key=lambda r: r["actual_total"]) if sell["rows"] else None

    ws_sum.write(f'A{row}', 'Total Actual', fmt_td); ws_sum.write_number(f'B{row}', total_actual, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Total Plan', fmt_td); ws_sum.write_number(f'B{row}', total_plan, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Average Actual / day', fmt_td); ws_sum.write_number(f'B{row}', avg_actual, fmt_dec2); row += 1
    ws_sum.write(f'A{row}', 'LIM Actual', fmt_td); ws_sum.write_number(f'B{row}', lim_actual, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'SAP Actual', fmt_td); ws_sum.write_number(f'B{row}', sap_actual, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'LIM Plan', fmt_td); ws_sum.write_number(f'B{row}', lim_plan, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'SAP Plan', fmt_td); ws_sum.write_number(f'B{row}', sap_plan, fmt_num); row += 1
    if max_day:
        ws_sum.write(f'A{row}', 'Max Actual Day', fmt_td)
        ws_sum.write(f'B{row}', f"{max_day['dt']} • {max_day['actual_total']:.2f}", fmt_td); row += 1
    if min_day:
        ws_sum.write(f'A{row}', 'Min Actual Day', fmt_td)
        ws_sum.write(f'B{row}', f"{min_day['dt']} • {min_day['actual_total']:.2f}", fmt_td); row += 1

    # Chart Selling: stacked LIM+SAP actual, line = plan_total
    if sell["rows"]:
        first, last = 2, len(sell["rows"]) + 1
        chart_s = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})
        chart_s.set_title({'name': 'Selling Trend'})
        chart_s.set_legend({'position': 'top'})

        # Actual LIM
        chart_s.add_series({
            'name': 'LIM Actual',
            'categories': f'=Data_Selling!$A${first}:$A${last}',
            'values':     f'=Data_Selling!$B${first}:$B${last}',  # pastikan kolom mapping ke actual LIM
             'fill': {'color': '#f4b94a'} 
        })
        # Actual SAP
        chart_s.add_series({
            'name': 'SAP Actual',
            'categories': f'=Data_Selling!$A${first}:$A${last}',
            'values':     f'=Data_Selling!$C${first}:$C${last}',  # pastikan sesuai kolom
            'fill': {'color': '#34d399'} 
        })

        # Line Plan Total
        line_chart_s = workbook.add_chart({'type': 'line'})
        line_chart_s.add_series({
            'name': 'Plan Total',
            'categories': f'=Data_Selling!$A${first}:$A${last}',
            'values':     f'=Data_Selling!$G${first}:$G${last}',  # kolom plan_total
            'line': {'color': '#f43f5f', 'width': 2.25}  #  warna merah + tebal
        })

        chart_s.combine(line_chart_s)
        ws_sum.insert_chart('E47', chart_s, {'x_scale': 2.07, 'y_scale': 1.32})


    # ================= Inventory Summary =================
    ws_sum.write('A68', 'Inventory Metrics', fmt_title)
    ws_sum.write_row('A69', ['Metric', 'Value'], fmt_th)
    row = 70

    ws_sum.write(f'A{row}', 'Production In', fmt_td); ws_sum.write_number(f'B{row}', inv["summary"]["total_in"], fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Selling Out', fmt_td); ws_sum.write_number(f'B{row}', inv["summary"]["total_out"], fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Stock Opname', fmt_td); ws_sum.write_number(f'B{row}', inv["summary"]["closing_balance"], fmt_num); row += 1

    # === Chart Inventory ===
    if inv["rows"]:
        first, last = 2, len(inv["rows"]) + 1

        if mode == "range":
            # Area chart (harian)
            chart_i = workbook.add_chart({'type': 'area', 'subtype': 'stacked'})
        else:  # mode == "year"
            # Column chart (bulanan)
            chart_i = workbook.add_chart({'type': 'column', 'subtype': 'clustered'})

        chart_i.set_title({'name': 'Inventory Trend'})
        chart_i.set_legend({'position': 'bottom'})

        # Production In
        chart_i.add_series({
            'name': 'Production In',
            'categories': f'=Stock_Opname!$A${first}:$A${last}',
            'values': f'=Stock_Opname!$B${first}:$B${last}',
            # 'fill': {'color': '#22c55f'} 
            'fill': {'color': '#22c55f', 'transparency': 30},  # hijau dengan 30% transparansi
            'smooth': True   # bikin garis halus / smooth
        })

        # Selling Out
        chart_i.add_series({
            'name': 'Selling Out',
            'categories': f'=Stock_Opname!$A${first}:$A${last}',
            'values': f'=Stock_Opname!$C${first}:$C${last}',
            'fill': {'color': '#fa7315','transparency': 40},
            'smooth': True   # bikin garis halus / smooth
        })

        # Stock Opname (line, secondary axis)
        line_chart_i = workbook.add_chart({'type': 'line'})
        line_chart_i.add_series({
            'name': 'Stock Opname',
            'categories': f'=Stock_Opname!$A${first}:$A${last}',
            'values': f'=Stock_Opname!$D${first}:$D${last}',
            'y2_axis': True,
            # 'line': {'color': '#f43f5f', 'width': 2.25}  #  warna merah + tebal
            'line': {'color': '#f43f5f', 'width': 2.5, 'dash_type': 'dash'},
            'smooth': True   # bikin garis halus / smooth
        })

        chart_i.combine(line_chart_i)

        # Axis labels
        chart_i.set_y_axis({'name': 'Production / Selling'})
        chart_i.set_y2_axis({'name': 'Stock Opname'})

        ws_sum.insert_chart('E68', chart_i, {'x_scale': 2.07, 'y_scale': 1.32})


    # Lebarkan kolom summary
    ws_sum.set_column('A:A', 21)
    ws_sum.set_column('B:B', 25)

    # Close workbook
    workbook.close()
    output.seek(0)

    filename = f"KQMS-summary_{date_start}_to_{date_end}.xlsx"
    resp = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp
