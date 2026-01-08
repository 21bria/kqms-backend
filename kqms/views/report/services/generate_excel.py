# reports/views.py
from io import BytesIO
from django.http import HttpResponse, HttpResponseBadRequest
from datetime import date,datetime
from django.utils import timezone
from django.utils.timezone import localtime
import xlsxwriter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Line, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.axes import XValueAxis, YValueAxis
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib.colors import HexColor
from reportlab.graphics.charts.legends import Legend
from ....utils.safe_chart import safe_chart_multi
from decimal import Decimal

def safe_float(v):
    try:
        return float(Decimal(v))
    except:
        return 0.0
    
from .compile_range import (
    fetch_production_quality,
    fetch_production_grade,
    fetch_selling,
    fetch_barging,
    fetch_production_mining,
    fetch_inventory_balance,
    fetch_inventory_dome,
    fetch_summary_to_date
)
from .compile_year import (
    fetch_production_quality_year, 
    fetch_production_grade_year,
    fetch_selling_year,
    fetch_barging_year,
    fetch_production_mining_year,
    fetch_inventory_balance_year,
    fetch_inventory_dome_year,
    fetch_summary_to_year
)
def parse_label(dt_val):
    if isinstance(dt_val, date):          # datetime.date / datetime
        return dt_val.day                 # kalau range (daily)
    if isinstance(dt_val, str) and len(dt_val) == 7:  # "YYYY-MM"
        return datetime.strptime(dt_val, "%Y-%m").month
    if isinstance(dt_val, str) and len(dt_val) == 10: # "YYYY-MM-DD"
        return datetime.strptime(dt_val, "%Y-%m-%d").day
    return dt_val


def excel_unified_summary(request):
    mode       = request.GET.get("mode") or "range"   # default: range
    date_start = request.GET.get("date_start") or str(date.today().replace(day=1))
    date_end   = request.GET.get("date_end")   or str(date.today())
    year       = request.GET.get("year")       # untuk mode=year

    # Ambil data
    if mode == "range":
        mining  = fetch_production_mining(date_start, date_end)
        prod    = fetch_production_quality(date_start, date_end)
        grade   = fetch_production_grade(date_start, date_end)
        sell    = fetch_selling(date_start, date_end)
        barging = fetch_barging(date_start, date_end)
        inv     = fetch_inventory_balance(date_start, date_end)
        invlist = fetch_inventory_dome(date_end)
        summary = fetch_summary_to_date(date_end)
    elif mode == "year" and year:
        try:
            year = int(year)
        except ValueError:
            return HttpResponseBadRequest("Invalid year parameter")
        mining  = fetch_production_mining_year(year)
        prod    = fetch_production_quality_year(year)
        grade   = fetch_production_grade_year(year)
        sell    = fetch_selling_year(year)
        barging = fetch_barging_year(year)
        inv     = fetch_inventory_balance_year(year)
        invlist = fetch_inventory_dome_year(year)
        summary = fetch_summary_to_year(year)
    else:
        return HttpResponseBadRequest("Invalid mode or missing parameters")

    output   = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})

    # Styles
    fmt_title = workbook.add_format({'bold': True, 'font_size': 14})
    fmt_th    = workbook.add_format({'bold': True, 'bg_color': '#F3F4F6', 'border': 1})
    fmt_td    = workbook.add_format({'border': 1})
    fmt_num   = workbook.add_format({'border': 1, 'num_format': '#,##0'})
    fmt_num2 = workbook.add_format({'border': 1,'num_format': '0.00'})
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

    # === Sheet Grade_Daily (
    ws_grade = workbook.add_worksheet('Daily_Grade')
    ws_grade.write_row(
        'A1',
        ['Date','Material','Ton','Ni','Co','Fe','MgO','SiO2','SM'],
        fmt_th
    )

    for i, r in enumerate(grade["rows"], start=2):
        ws_grade.write(f'A{i}', str(r['dt']), fmt_td)
        ws_grade.write(f'B{i}', r['nama_material'], fmt_td)
        ws_grade.write_number(f'C{i}', safe_float(r.get('total_ore')), fmt_num)
        ws_grade.write_number(f'D{i}', safe_float(r.get('ni')), fmt_num2)
        ws_grade.write_number(f'E{i}', safe_float(r.get('co')), fmt_num2)
        ws_grade.write_number(f'F{i}', safe_float(r.get('fe')), fmt_num2)
        ws_grade.write_number(f'G{i}', safe_float(r.get('mgo')), fmt_num2)
        ws_grade.write_number(f'H{i}', safe_float(r.get('sio2')), fmt_num2)
        ws_grade.write_number(f'I{i}', safe_float(r.get('sm')), fmt_num2)

    ws_grade.set_column('A:A', 12)      # Date
    ws_grade.set_column('B:B', 12)      # Material
    ws_grade.set_column('C:C', 12)      # Ton
    ws_grade.set_column('D:I', 10)      # Ni..SM


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

  

    # === Sheet Barging ====
    ws_barging = workbook.add_worksheet('Barging')
    ws_barging.write_row(
        'A1',
        ['Date', 'Actual LIM', 'Actual SAP', 'Actual Total',
        'Plan LIM', 'Plan SAP', 'Plan Total', 'By Barge JSON'],
        fmt_th
    )

    for i, r in enumerate(barging["rows"], start=2):
        ws_barging.write(f'A{i}', r['label'], fmt_td)
        ws_barging.write_number(f'B{i}', r['actual_lim'] or 0, fmt_num)
        ws_barging.write_number(f'C{i}', r['actual_sap'] or 0, fmt_num)
        ws_barging.write_number(f'D{i}', r['actual_total'] or 0, fmt_num)
        ws_barging.write_number(f'E{i}', r['plan_lim'] or 0, fmt_num)
        ws_barging.write_number(f'F{i}', r['plan_sap'] or 0, fmt_num)
        ws_barging.write_number(f'G{i}', r['plan_total'] or 0, fmt_num)
        ws_barging.write(f'H{i}', str(r['summary_by_barge']), fmt_td)  # simpan JSON string

    ws_barging.set_column('A:A', 12)
    ws_barging.set_column('B:G', 15)
    ws_barging.set_column('H:H', 120)  # kolom JSON panjang

    # === Sheet Barging_ByBarge
    ws_barging_b = workbook.add_worksheet('Barging_ByBarge')
    ws_barging_b.write('A1', 'Date', fmt_th)

    # Ambil semua barge_code unik dari seluruh rows
    barge_codes = set()
    for r in barging["rows"]:
        for b in r["summary_by_barge"]:
            barge_codes.add(b["barge_code"])

    barge_codes = sorted(barge_codes)  # biar urut
    for idx, code in enumerate(barge_codes, start=2):
        ws_barging_b.write(0, idx-1, code, fmt_th)  # header barge_code (kolom B,C,D...)

    # Isi data per tanggal
    for row_idx, r in enumerate(barging["rows"], start=2):
        ws_barging_b.write(f'A{row_idx}', r['label'], fmt_td)
        barge_map = {b["barge_code"]: b["total"] for b in r["summary_by_barge"]}
        for col_idx, code in enumerate(barge_codes, start=2):
            ws_barging_b.write_number(row_idx-1, col_idx-1, barge_map.get(code, 0), fmt_num)

    ws_barging_b.set_column('A:A', 12)
    ws_barging_b.set_column('B:Z', 14)


    # === Sheet Stock_Opname
    ws_inv = workbook.add_worksheet('Stock_Opname')
    ws_inv.write_row('A1', ['Date', 'Production In', 'Selling Out', 'Stock Opname'], fmt_th)

    row = 2

    # Opening Stock (ambil dari inv["summary"]["opening_balance"])
    opening_stock = inv["summary"].get("opening_balance", 0)
    ws_inv.write('A2', 'Opening Stock', fmt_th)
    ws_inv.write_number('D2', opening_stock, fmt_num)
    row += 1

    # Daily records
    for r in inv["rows"]:
        ws_inv.write(f'A{row}', str(r['dt']), fmt_td)
        ws_inv.write_number(f'B{row}', r['total_in'] or 0, fmt_num)        # Production In
        ws_inv.write_number(f'C{row}', r['total_out'] or 0, fmt_num)       # Selling Out
        ws_inv.write_number(f'D{row}', r['running_balance'] or 0, fmt_num) # Stock Opname
        row += 1

    # Closing summary
    closing_stock  = inv["summary"].get("closing_balance", 0)
    total_in       = inv["summary"].get("total_in", 0)
    total_out      = inv["summary"].get("total_out", 0)
    net_movement   = total_in - total_out

    ws_inv.write(f'A{row}', 'Closing Stock', fmt_th)
    ws_inv.write_number(f'D{row}', closing_stock, fmt_num); row += 1

    ws_inv.write(f'A{row}', 'Net Movement', fmt_th)
    ws_inv.write_number(f'D{row}', net_movement, fmt_num); row += 1

    ws_inv.write(f'A{row}', 'Opening Stock (Next)', fmt_th)
    ws_inv.write_number(f'D{row}', closing_stock, fmt_num); row += 1

    # Set lebar kolom
    ws_inv.set_column('A:A', 20)
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
        # ws_invlist.write(f'N{i}', r['direct_sale'], fmt_td)

    ws_invlist.set_column('A:C', 14)   # stockpile, pile id, material
    ws_invlist.set_column('D:G', 14)   # total ore, released, selling, balance
    ws_invlist.set_column('H:N', 10)   # Ni, Co, Fe, MgO, SiO2, SM,Direct


    # tambahkan blok summary Quality, Selling, Mining :
    # === Sheet Summary
    ws_sum = workbook.add_worksheet('Summary')
    ws_sum.hide_gridlines(2)   # 2 = hide both screen & print
    ws_sum.write('A1', 'KQMS Unified Report', fmt_title)
    if mode == "range":
        ws_sum.write('A2', f'Range: {date_start} → {date_end}', fmt_small)
    elif mode == "year":
        ws_sum.write('A2', f'Year: {year}', fmt_small)

    ws_sum.write('D2', f"Generated: {localtime(timezone.now()).strftime('%Y-%m-%d, %H:%M:%S')}", fmt_small)

    # === Project Summary To-Date ===
    ws_sum.write('A4', 'Project Summary to Date', fmt_title)

    # ---------- Mining (kolom A–B, vertikal) ----------
    ws_sum.write('A6', 'Mining', fmt_th)
    ws_sum.write_row('A7', ['Metric','Value'], fmt_th)
    ws_sum.write('A8',  'Total Actual', fmt_td); ws_sum.write_number('B8', summary['mining']['actual_total'], fmt_num)
    # ws_sum.write('A9',  'Total Plan',   fmt_td); ws_sum.write_number('B9', summary['mining']['plan_total'], fmt_num)
    # ws_sum.write('A10', 'Achievement',  fmt_td); ws_sum.write('B10', f"{(summary['mining']['actual_total']/summary['mining']['plan_total']*100 if summary['mining']['plan_total'] else 0):.0f}%", fmt_td)
    ws_sum.write('A9', 'Total LIM',    fmt_td); ws_sum.write_number('B9', summary['mining']['lim_total'], fmt_num)
    ws_sum.write('A10', 'Total SAP',    fmt_td); ws_sum.write_number('B10', summary['mining']['sap_total'], fmt_num)
    ws_sum.write('A11', 'Total Waste',  fmt_td); ws_sum.write_number('B11', summary['mining']['waste_total'], fmt_num)
    ws_sum.write('A12', 'Total Quarry', fmt_td); ws_sum.write_number('B12', summary['mining']['quarry_total'], fmt_num)
    ws_sum.write('A13', 'Total Topsoil',fmt_td); ws_sum.write_number('B13', summary['mining']['topsoil_total'], fmt_num)
    ws_sum.write('A14', 'Total OB',     fmt_td); ws_sum.write_number('B14', summary['mining']['ob_total'], fmt_num)
    ws_sum.write('A15', 'Total Ballast',fmt_td); ws_sum.write_number('B15', summary['mining']['ballast_total'], fmt_num)
    ws_sum.write('A16', 'Total Biomass',fmt_td); ws_sum.write_number('B16', summary['mining']['biomass_total'], fmt_num)



    # ---------- Quality (kolom D–I, horizontal) ----------
    ws_sum.write('D6', 'Material Type', fmt_th)
    # ws_sum.write_row('D7', ['Metric','Total','LIM (total)','LIM (%)','SAP (total)','SAP (%)'], fmt_th)
    ws_sum.write_row('D7', ['Metric','Total','LIM (total)','SAP (total)'], fmt_th)

    ws_sum.write('D8', 'Value', fmt_td)
    ws_sum.write_number('E8', summary['quality']['total'] or 0, fmt_num)
    ws_sum.write_number('F8', summary['quality']['lim'] or 0, fmt_num)
    # ws_sum.write('G8', f"{(summary['quality']['lim']/summary['quality']['total']*100):.2f}%" if summary['quality']['total'] else "0%", fmt_td)
    ws_sum.write_number('G8', summary['quality']['sap'] or 0, fmt_num)
    # ws_sum.write('I8', f"{(summary['quality']['sap']/summary['quality']['total']*100):.2f}%" if summary['quality']['total'] else "0%", fmt_td)

    # ---------- Selling (kolom D–I, horizontal) ----------
    ws_sum.write('D10', 'Selling', fmt_th)
    ws_sum.write_row('D11', ['Metric','Total Actual','LIM Actual','SAP Actual'], fmt_th)

    ws_sum.write('D12', 'Value', fmt_td)
    ws_sum.write_number('E12', summary['selling']['actual'] or 0, fmt_num)
    # ws_sum.write_number('F12', summary['selling']['plan'] or 0, fmt_num)
    # ws_sum.write('G12', f"{(summary['selling']['actual']/summary['selling']['plan']*100):.0f}%" if summary['selling']['plan'] else "0%", fmt_td)
    ws_sum.write_number('F12', summary['selling']['lim_actual'] or 0, fmt_num)
    ws_sum.write_number('G12', summary['selling']['sap_actual'] or 0, fmt_num)

    # ---------- Inventory (kolom D–H, horizontal) ----------
    ws_sum.write('D14', 'Inventory', fmt_th)
    ws_sum.write_row('D15', ['Metric','Production In','Selling Out','Current Stock'], fmt_th)

    ws_sum.write('D16', 'Value', fmt_td)
    ws_sum.write_number('E16', summary['inventory']['in'] or 0, fmt_num)
    ws_sum.write_number('F16', summary['inventory']['out'] or 0, fmt_num)
    ws_sum.write_number('G16', summary['inventory']['current_stock'] or 0, fmt_num)  # pakai closing balance


    # Atur lebar kolom D–I (Quality & Selling)
    ws_sum.set_column('D:I', 12)

    # Atur lebar kolom D–H (Inventory)
    ws_sum.set_column('D:H', 12)

     # --- Buat judul dinamis ---
    if mode == "range":
        mining_title    = f"Mining by Period (Range: {date_start} → {date_end})"
        quality_title   = f"Material Type by Period (Range: {date_start} → {date_end})"
        # grade_title     = f"Daily Ore by Period (Range: {date_start} → {date_end})"
        selling_title   = f"Selling by Period (Range: {date_start} → {date_end})"
        barging_title   = f"Barging by Period (Range: {date_start} → {date_end})"
        inventory_title = f"Inventory by Period (Range: {date_start} → {date_end})"
    elif mode == "year":
        mining_title    = f"Mining by Period (Year: {year})"
        quality_title   = f"Material Type by Period (Year: {year})"
        # grade_title     = f"Daily Ore by Period  (Year: {year})"
        selling_title   = f"Selling by Period (Year: {year})"
        barging_title   = f"Barging by Period (Year: {year})"
        inventory_title = f"Inventory by Period (Year: {year})"
    else:
        mining_title    = "Mining by Period"
        quality_title   = "Material Type by Period"
        # grade_title     = "Daily Ore by Period "
        selling_title   = "Selling by Period"
        barging_title   = "Barging by Period"
        inventory_title = "Inventory by Period"


    # ---------------- Mining Section ----------------
    ws_sum.write('A20', mining_title, fmt_title)
    ws_sum.write_row('A21', ['Metric', 'Value'], fmt_th)
    row = 22 # mulai dari baris 22

    total_actual = sum(r["actual_total"] for r in mining["rows"]) if mining["rows"] else 0
    total_plan   = sum(r["plan_total"] for r in mining["rows"]) if mining["rows"] else 0
    max_day = max(mining["rows"], key=lambda r: r["actual_total"]) if mining["rows"] else None
    min_day = min(mining["rows"], key=lambda r: r["actual_total"]) if mining["rows"] else None

    ws_sum.write(f'A{row}', 'Total Actual', fmt_td); ws_sum.write_number(f'B{row}', total_actual, fmt_num); row += 1
    # ws_sum.write(f'A{row}', 'Total Plan', fmt_td); ws_sum.write_number(f'B{row}', total_plan, fmt_num); row += 1
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
    material_colors = {
            'LIM'       : "#f5d8aa",      # kuning
            'SAP'       : "#b1dcb5",      # hijau
            'Waste'     : "#d4c399", 
            'Quarry'    : '#365e58',   
            'Topsoil'   : "#b79d46", 
            'OB'        : "#f29b5d",      
            'Ballast'   : "#7f7f7f",  
            'Biomass'   : '#f4b0ad', 
        }   

    if mining["rows"]:
        first, last = 2, len(mining["rows"]) + 1
        categories = f'=Data_Mining!$A${first}:$A${last}'

        series_defs = []
        for col, name in zip("BCDEFGHI", ['LIM','SAP','Waste','Quarry','Topsoil','OB','Ballast','Biomass']):
            series_defs.append({
                'name': name,
                'values': f'=Data_Mining!${col}${first}:${col}${last}',
                'fill': {'color': material_colors.get(name, '#999999')}  # default abu2 kalau gak ketemu
            })

        line_defs = [{
            'name': 'Plan',
            'values': f'=Data_Mining!$K${first}:$K${last}',
            'line': {'color': "#ea5e5e", 'width': 2.25}
        }]
    else:
        categories = None
        series_defs = None
        line_defs = None

    safe_chart_multi(
        workbook,
        ws_sum,
        pos='D21',
        title='Mining Trend',
        rows=mining["rows"],
        categories=categories,
        series_defs=series_defs,
        line_defs=line_defs,   # langsung combine line plan
        scale=(2.07, 1.32),
        stacked=True,
        legend_pos='top'
    )


    # ================= Quality Summary =================
    ws_sum.write('A43', quality_title, fmt_title)
    ws_sum.write_row('A44', ['Metric', 'Value'], fmt_th)
    row = 45    # mulai dari baris 45

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
    # ws_sum.write(f'A{row}', 'LIM (%)', fmt_td); ws_sum.write(f'B{row}', f'{pct_lim:.2f}%', fmt_td); row += 1
    ws_sum.write(f'A{row}', 'SAP (total)', fmt_td); ws_sum.write_number(f'B{row}', total_sap, fmt_num); row += 1
    # ws_sum.write(f'A{row}', 'SAP (%)', fmt_td); ws_sum.write(f'B{row}', f'{pct_sap:.2f}%', fmt_td); row += 1
    if max_day:
        ws_sum.write(f'A{row}', 'Max day', fmt_td); ws_sum.write(f'B{row}', f"{max_day['dt']} • {max_day['prod_total']:.2f}", fmt_td); row += 1
    if min_day:
        ws_sum.write(f'A{row}', 'Min day', fmt_td); ws_sum.write(f'B{row}', f"{min_day['dt']} • {min_day['prod_total']:.2f}", fmt_td); row += 1

    # Chart Quality

    if prod["rows"]:
        first, last = 2, len(prod["rows"]) + 1
        categories  = f'=Data_Quality!$A${first}:$A${last}'

        series_defs = [
            {
                'name': 'LIM',
                'values': f'=Data_Quality!$C${first}:$C${last}',
                'fill': {'color': "#f8dfb7"}
            },
            {
                'name': 'SAP',
                'values': f'=Data_Quality!$D${first}:$D${last}',
                'fill': {'color': '#bdddc0'}
            }
        ]
    else:
        categories = None
        series_defs = None

    chart_q = safe_chart_multi(
        workbook,
        ws_sum,
        pos='D44',
        title='Material Type',
        rows=prod["rows"],
        categories=categories,
        series_defs=series_defs,
        scale=(2.07, 1.32),
        stacked=True,
        legend_pos='top'
    )


   # ================= Selling Summary =================
    ws_sum.write('A65', selling_title, fmt_title)
    ws_sum.write_row('A66', ['Metric', 'Value'], fmt_th)
    row = 67    # mulai dari baris 65

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
    # ws_sum.write(f'A{row}', 'Total Plan', fmt_td); ws_sum.write_number(f'B{row}', total_plan, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'LIM Actual', fmt_td); ws_sum.write_number(f'B{row}', lim_actual, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'SAP Actual', fmt_td); ws_sum.write_number(f'B{row}', sap_actual, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Average Actual / day', fmt_td); ws_sum.write_number(f'B{row}', avg_actual, fmt_dec2); row += 1
    # ws_sum.write(f'A{row}', 'LIM Plan', fmt_td); ws_sum.write_number(f'B{row}', lim_plan, fmt_num); row += 1
    # ws_sum.write(f'A{row}', 'SAP Plan', fmt_td); ws_sum.write_number(f'B{row}', sap_plan, fmt_num); row += 1
    if max_day:
        ws_sum.write(f'A{row}', 'Max Actual Day', fmt_td)
        ws_sum.write(f'B{row}', f"{max_day['dt']} • {max_day['actual_total']:.2f}", fmt_td); row += 1
    if min_day:
        ws_sum.write(f'A{row}', 'Min Actual Day', fmt_td)
        ws_sum.write(f'B{row}', f"{min_day['dt']} • {min_day['actual_total']:.2f}", fmt_td); row += 1

 
    if sell["rows"]:
        first, last = 2, len(sell["rows"]) + 1
        categories = f'=Data_Selling!$A${first}:$A${last}'

        # Series stacked bar
        series_defs = [
            {
                'name': 'LIM',
                'values': f'=Data_Selling!$B${first}:${"B"}${last}',
                'fill': {'color': '#ffedd1'}
            },
            {
                'name': 'SAP',
                'values': f'=Data_Selling!$C${first}:${"C"}${last}',
                'fill': {'color': "#bdddc0"}
            }
        ]

        # Series line
        # line_defs = [
        #     {
        #         'name': 'Plan Total',
        #         'values': f'=Data_Selling!$G${first}:${"G"}${last}',
        #         'line': {'color': "#fe927a", 'width': 2.25}
        #     }
        # ]
    else:
        categories = None
        series_defs = None
        line_defs = None

    safe_chart_multi(
        workbook,
        ws_sum,
        pos='D66',
        title='Selling Trend',
        rows=sell["rows"],
        categories=categories,
        series_defs=series_defs,
        line_defs=None,   #  line langsung combine
        scale=(2.07, 1.32),
        stacked=True,
        legend_pos='top'
    )


    # ================= Barging Summary =================
    ws_sum.write('A87', barging_title, fmt_title)
    ws_sum.write_row('A88', ['Metric', 'Value'], fmt_th)
    row = 89

    summary_b = barging["summary"]

    ws_sum.write(f'A{row}', 'Actual Total', fmt_td); ws_sum.write_number(f'B{row}', summary_b["actual_total"], fmt_num); row += 1
    # ws_sum.write(f'A{row}', 'Plan Total', fmt_td); ws_sum.write_number(f'B{row}', summary_b["plan_total"], fmt_num); row += 1
    ws_sum.write(f'A{row}', 'LIM Actual', fmt_td); ws_sum.write_number(f'B{row}', summary_b["lim_actual"], fmt_num); row += 1
    ws_sum.write(f'A{row}', 'SAP Actual', fmt_td); ws_sum.write_number(f'B{row}', summary_b["sap_actual"], fmt_num); row += 1
    # ws_sum.write(f'A{row}', 'LIM Plan', fmt_td); ws_sum.write_number(f'B{row}', summary_b["lim_plan"], fmt_num); row += 1
    # ws_sum.write(f'A{row}', 'SAP Plan', fmt_td); ws_sum.write_number(f'B{row}', summary_b["sap_plan"], fmt_num); row += 1

    # Palet warna 
    palette = [
        "#72b1ab",  # biru
        "#a4c3f4",  # biru
        "#bddddc",  # hijau
        "#ffedd1",  # kuning
        "#fe927a",  # ungu
        "#d0b97f",  # teal
        "#365e58",  # oranye
        "#8192aa",  # abu2
    ]


    if barging["rows"]:
        first, last = 2, len(barging["rows"]) + 1
        categories  = f'=Barging_ByBarge!$A${first}:$A${last}'
        series_defs = []
        for idx, code in enumerate(barge_codes, start=2):
            color = palette[(idx - 2) % len(palette)]  # ambil warna dari palet
            series_defs.append({
                'name': code,
                'values': f'=Barging_ByBarge!${chr(64+idx)}${first}:${chr(64+idx)}${last}',
                'fill': {'color': color} 
            })
    else:
        categories = None
        series_defs = None

    safe_chart_multi(
        workbook,
        ws_sum,
        pos='D88',
        title='Barging by Barge Code',
        rows=barging["rows"],
        categories=categories,
        series_defs=series_defs,
        scale=(2.07, 1.32),
        stacked=True,
        legend_pos='top'
    )

    

    # ================= Inventory Summary =================
    ws_sum.write('A109', inventory_title, fmt_title)
    ws_sum.write_row('A110', ['Metric', 'Value'], fmt_th)
    row = 111  # mulai dari baris 109

    opening_stock = inv["summary"].get("opening_balance", 0)
    closing_stock = inv["summary"].get("closing_balance", 0)
    total_in      = inv["summary"].get("total_in", 0)
    total_out     = inv["summary"].get("total_out", 0)
    net_movement  = total_in - total_out

    ws_sum.write(f'A{row}', 'Opening Stock', fmt_td)
    ws_sum.write_number(f'B{row}', opening_stock, fmt_num); row += 1

    ws_sum.write(f'A{row}', 'Production In', fmt_td)
    ws_sum.write_number(f'B{row}', total_in, fmt_num); row += 1

    ws_sum.write(f'A{row}', 'Selling Out', fmt_td)
    ws_sum.write_number(f'B{row}', total_out, fmt_num); row += 1

    ws_sum.write(f'A{row}', 'Closing Stock', fmt_td)
    ws_sum.write_number(f'B{row}', closing_stock, fmt_num); row += 1

    ws_sum.write(f'A{row}', 'Net Movement', fmt_td)
    ws_sum.write_number(f'B{row}', net_movement, fmt_num); row += 1

    # buat carry forward
    ws_sum.write(f'A{row}', 'Opening Stock (Next)', fmt_td)
    ws_sum.write_number(f'B{row}', closing_stock, fmt_num); row += 1


    if inv["rows"]:
        first, last = 2, len(inv["rows"]) + 1
        categories = f'=Stock_Opname!$A${first}:$A${last}'

        series_defs = [
            {
                'name': 'Production In',
                'values': f'=Stock_Opname!$B${first}:$B${last}',
                # 'fill': {'color': '#bddddc', 'transparency': 75},
                'fill': {'color': '#bddddc', 'transparency': 25},
                'smooth': True
            },
            {
                'name': 'Selling Out',
                'values': f'=Stock_Opname!$C${first}:$C${last}',
                'fill': {'color': '#ffedd1', 'transparency': 30},
                'smooth': True
            }
        ]

        line_defs = [
            {
                'name': 'Stock Opname',
                'values': f'=Stock_Opname!$D${first}:$D${last}',
                'line': {'color': '#fe927a', 'width': 2.5, 'dash_type': 'dash'},
                'y2_axis': True,
                'smooth': True
            }
        ]
    else:
        categories = None
        series_defs = None
        line_defs = None

    safe_chart_multi(
        workbook,
        ws_sum,
        pos='D110',
        title='Inventory Trend',
        rows=inv["rows"],
        categories=categories,
        series_defs=series_defs,
        line_defs=line_defs,
        scale=(2.07, 1.32),
        chart_type='area' if mode == "range" else 'column',
        stacked=True if mode == "range" else False,
        legend_pos='bottom',
        y_axis={'name': 'Production / Selling'},
        y2_axis={'name': 'Stock Opname'}
    )


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

def pdf_unified_summary(request):
    mode       = request.GET.get("mode") or "range"
    date_start = request.GET.get("date_start") or str(date.today().replace(day=1))
    date_end   = request.GET.get("date_end")   or str(date.today())
    year       = request.GET.get("year")

    # === Ambil data (sama dengan Excel) ===
    if mode == "range":
        mining  = fetch_production_mining(date_start, date_end)
        prod    = fetch_production_quality(date_start, date_end)
        grade   = fetch_production_grade(date_start, date_end)
        sell    = fetch_selling(date_start, date_end)
        barging = fetch_barging(date_start, date_end)
        inv     = fetch_inventory_balance(date_start, date_end)
        summary = fetch_summary_to_date(date_end)
    elif mode == "year" and year:
        year = int(year)
        mining  = fetch_production_mining_year(year)
        prod    = fetch_production_quality_year(year)
        grade   = fetch_production_grade_year(year)
        sell    = fetch_selling_year(year)
        barging = fetch_barging_year(year)
        inv     = fetch_inventory_balance_year(year)
        summary = fetch_summary_to_year(year)
    else:
        return HttpResponseBadRequest("Invalid mode or missing parameters")

    def safe_float(val):
        try:
            return float(val or 0)
        except:
            return 0.0

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        topMargin=25,    # margin atas diperkecil
        bottomMargin=20  # margin bawah diperkecil
    )

    elements = []
    styles = getSampleStyleSheet()

  # Tambah style kanan kecil
    styles.add(ParagraphStyle(
        name="RightSmall",
        parent=styles["Normal"],
        fontSize=8,
        # alignment=TA_RIGHT
    ))

    # === Header PDF ===
    elements.append(Paragraph("KQMS Unified Report - Summary", styles['Title']))
    if mode == "range":
        header_info = Paragraph(
            f"Range: {date_start} → {date_end}<br/>"
            f"Generated: {localtime(timezone.now()).strftime('%Y-%m-%d, %H:%M:%S')}",
            styles['RightSmall']
        )
    else:
        header_info = Paragraph(
            f"Year: {year}<br/>"
            f"Generated: {localtime(timezone.now()).strftime('%Y-%m-%d, %H:%M:%S')}",
            styles['RightSmall']
        )

    elements.append(header_info)
    elements.append(Spacer(1, 4))

    # Fungsi bantu untuk auto scale axis
    def auto_scale_axis(series, n_ticks=6):
        from math import ceil
        max_val = max((max(s) for s in series if s), default=0)
        if max_val == 0:
            return (0, 100, 20)
        step = max(1, round(max_val / (n_ticks - 1), -2))
        vmax = ceil(max_val / step) * step
        return (0, vmax, step)

    def add_section(title, metrics, rows, categories, series, line_series=None, bar_color="#add2bb"):
        elements.append(Paragraph(title, styles['Heading2']))
        elements.append(Spacer(1, 6))

        # Metrics table
        table = Table(metrics, colWidths=[150, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            # Kolom Metric rata kiri
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            # Kolom Value rata kanan
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))

        if rows:
            d = Drawing(700, 300)

            # --- Sumbu Y dihitung dari actual + plan (tidak ada scaling) ---
            combined = list(series)
            if line_series:
                combined.append([safe_float(v) for v in line_series])
            vmin, vmax, vstep = auto_scale_axis(combined)

            # === Bar Chart (Actual) ===
            bc = VerticalBarChart()
            bc.x, bc.y = 50, 50
            bc.height, bc.width = 200, 550
            bc.data = series
            bc.categoryAxis.categoryNames = [str(c) for c in categories]
            bc.barWidth = 12

           # rapikan label tanggal biar tidak numpuk
            bc.categoryAxis.labels.angle = 45  
            bc.categoryAxis.labels.boxAnchor = 'ne'   
            bc.categoryAxis.labels.dy = -4       
            bc.categoryAxis.labels.fontSize = 9      
           

            # Style axis
            bc.valueAxis.valueMin  = vmin
            bc.valueAxis.valueMax  = vmax
            bc.valueAxis.valueStep = vstep
            bc.valueAxis.strokeColor = HexColor("#9ca3af")
            bc.valueAxis.labels.fillColor = HexColor("#6b7280")
            bc.categoryAxis.strokeColor = HexColor("#9ca3af")
            bc.categoryAxis.labels.fillColor = HexColor("#676a6e")
            bc.categoryAxis.visibleTicks = 0

            # warna bar (support multi-series)
            bar_colors = [bar_color] if isinstance(bar_color, str) else bar_color
            for i, c in enumerate(bar_colors):
                if i < len(bc.bars):
                    bc.bars[i].fillColor = HexColor(c)
                    bc.bars[i].strokeColor = HexColor(c)   # triknya: samakan warna stroke dengan fill
                    bc.bars[i].strokeWidth = 0             # pastikan garis pinggir 0
            d.add(bc)
                        
            # === Line Chart (Plan) – tanpa scaling, pakai sumbu yang sama ===
            if line_series:
                lp = LinePlot()
                lp.x, lp.y = 50, 50
                lp.height, lp.width = 200, 550

                # data X numerik 0..N-1 agar segaris dengan kategori bar
                lp.data = [list(enumerate([safe_float(v) for v in line_series]))]


                # definisikan axis numeric dan samakan rentang Y
                lp.xValueAxis = XValueAxis()
                lp.yValueAxis = YValueAxis()
                lp.xValueAxis.valueMin  = 0
                lp.xValueAxis.valueMax  = max(1, len(categories)-1)
                lp.xValueAxis.valueStep = max(1, len(categories)//10)
                lp.yValueAxis.valueMin  = vmin
                lp.yValueAxis.valueMax  = vmax
                lp.yValueAxis.valueStep = vstep

                # >>> matikan label & ticks di X axis (biar 0-28 hilang) <<<
                lp.xValueAxis.labels.fontSize = 0       # sembunyikan tulisan
                lp.xValueAxis.visibleTicks = 0          # sembunyikan garis tick
                # lp.xValueAxis.strokeColor = colors.white  # bikin invisible
                lp.xValueAxis.strokeColor = HexColor("#9ca3af")  # abu-abu halu

                # Y axis tetap jalan
                lp.yValueAxis.valueMin  = vmin
                lp.yValueAxis.valueMax  = vmax
                lp.yValueAxis.valueStep = vstep
                lp.yValueAxis.strokeColor = HexColor("#9ca3af")
                lp.yValueAxis.labels.fillColor = HexColor("#6b7280")

                lp.lines[0].strokeWidth = 0   # garis hilang
                lp.lines[0].strokeColor = None  # tidak ada warna garis    
                # marker tetap tampil
                lp.lines[0].symbol = makeMarker('Circle')
                lp.lines[0].symbol.fillColor = HexColor("#ef4444")   # warna marker isi
                lp.lines[0].symbol.strokeColor = HexColor("#3A3939") # warna outline marker
                lp.lines[0].symbol.size = 4                          # ukuran marker

                d.add(lp)

            elements.append(d)

        elements.append(PageBreak())

    def add_section_with_summary(title, metrics, rows, categories, series, line_series=None, breakdown=None, bar_color="#1f2937"):
        elements.append(Paragraph(title, styles['Heading2']))
        elements.append(Spacer(1, 6))

        # Tabel ringkas
        table = Table(metrics, colWidths=[200, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            # Kolom Metric rata kiri
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            # Kolom Value rata kanan
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        if rows:
            d = Drawing(700, 300)

            # auto-scale
            combined = list(series)
            if line_series:
                combined.append([safe_float(v) for v in line_series])
            vmin, vmax, vstep = auto_scale_axis(combined)

            # === Bar chart ===
            bc = VerticalBarChart()
            bc.x, bc.y = 50, 50
            bc.height, bc.width = 200, 550
            bc.data = series
            bc.categoryAxis.categoryNames = [str(c) for c in categories]
            bc.barWidth = 12
            
            # rapikan label tanggal biar tidak numpuk
            bc.categoryAxis.labels.angle = 45            # miring 45 derajat
            bc.categoryAxis.labels.boxAnchor = 'ne'      # anchor ke atas kanan
            bc.categoryAxis.labels.dy = -3              # geser ke atas sedikit
            bc.categoryAxis.labels.fontSize = 9          # perkecil font biar muat
            bc.categoryAxis.labels.fillColor = HexColor("#9ca3af")  # warna abu

        
            # Style axis
            bc.valueAxis.valueMin  = vmin
            bc.valueAxis.valueMax  = vmax
            bc.valueAxis.valueStep = vstep
            bc.valueAxis.strokeColor = HexColor("#9ca3af")
            bc.valueAxis.labels.fillColor = HexColor("#6b7280")
            bc.categoryAxis.strokeColor = HexColor("#fdfeff")
            bc.categoryAxis.labels.fillColor = HexColor("#676a6e")
            bc.categoryAxis.visibleTicks = 0

            # Bar color
            bc.bars[0].fillColor = HexColor(bar_color)
            for i in range(len(bc.bars)):
                bc.bars[i].strokeColor = None

            d.add(bc)

            # === Marker only (Plan) ===
             # === Line Chart (Plan) – tanpa scaling, pakai sumbu yang sama ===
            if line_series:
                lp = LinePlot()
                lp.x, lp.y = 50, 50
                lp.height, lp.width = 200, 550

                # data X numerik 0..N-1 agar sejajar bar
                lp.data = [list(enumerate([safe_float(v) for v in line_series]))]

                # definisikan axis numeric dan samakan rentang Y
                lp.xValueAxis.valueMin  = 0
                lp.xValueAxis.valueMax  = max(1, len(categories)-1)
                lp.xValueAxis.valueStep = max(1, len(categories)//10)

                # >>> matikan label & ticks di X axis (biar 0-28 hilang) <<<
                lp.xValueAxis.labels.fontSize = 0       # sembunyikan tulisan
                lp.xValueAxis.visibleTicks = 0          # sembunyikan garis tick
                # lp.xValueAxis.strokeColor = colors.white  # bikin invisible
                lp.xValueAxis.strokeColor = HexColor("#9ca3af")  # abu-abu halus

                # Y axis tetap jalan
                lp.yValueAxis.valueMin  = vmin
                lp.yValueAxis.valueMax  = vmax
                lp.yValueAxis.valueStep = vstep
                lp.yValueAxis.strokeColor = HexColor("#9ca3af")
                lp.yValueAxis.labels.fillColor = HexColor("#6b7280")

                lp.lines[0].strokeColor = HexColor("#ef4444")
                lp.lines[0].strokeWidth = 2
                lp.lines[0].symbol = makeMarker('Circle')

                d.add(lp)


            elements.append(d)

        # breakdown tambahan
        if breakdown:
            elements.append(Spacer(1, 12))
            btable = Table(breakdown, colWidths=[78] * len(breakdown[0]))
            btable.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('ALIGN', (0,1), (-1,-1), 'CENTER'),
            ]))
            elements.append(btable)

        elements.append(PageBreak())

    def add_ore_section(title, metrics, rows, categories, bar_series, line_series):
        elements.append(Paragraph(title, styles['Heading2']))
        elements.append(Spacer(1, 6))

        # Metrics table
        table = Table(metrics, colWidths=[120, 120])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            # Kolom Metric rata kiri
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            # Kolom Value rata kanan
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))

        if rows:
            # d = Drawing(700, 200)
            d = Drawing(400, 200)   # lebih kecil agar muat di samping
            # === Bar Chart (Production In & Selling Out) ===
            bc = VerticalBarChart()
            bc.x, bc.y = 30, 30
            bc.height, bc.width = 170, 550
            bc.data = bar_series
            bc.categoryAxis.categoryNames = [str(c) for c in categories]
            bc.barWidth = 8

            # auto scale bar axis
            vmin, vmax, vstep = auto_scale_axis(bar_series)
            bc.valueAxis.valueMin = vmin
            bc.valueAxis.valueMax = vmax
            bc.valueAxis.valueStep = vstep

            bc.bars[0].fillColor = HexColor("#eab672")  # orange
            bc.bars[1].fillColor = HexColor("#a0c481")  # green


            bc.valueAxis.strokeColor = HexColor("#9ca3af")
            bc.valueAxis.labels.fillColor = HexColor("#6b7280")
            bc.categoryAxis.strokeColor = HexColor("#9ca3af")
            bc.categoryAxis.labels.fillColor = HexColor("#676a6e")


            # hilangkan outline (stroke) cukup di level series
            bc.bars[0].strokeColor = None
            bc.bars[0].strokeWidth = 0
            bc.bars[1].strokeColor = None
            bc.bars[1].strokeWidth = 0


            d.add(bc)

            # === Line Chart (Running Balance, pakai axis kanan) ===
            if line_series:
                lp = LinePlot()
                lp.x, lp.y = 50, 50
                lp.height, lp.width = 200, 550
                lp.data = [list(enumerate([safe_float(v) for v in line_series]))]

                lp.lines[0].strokeColor = HexColor("#ef4444")
                lp.lines[0].strokeWidth = 2
                lp.lines[0].symbol = makeMarker('Circle')
                d.add(lp)

                # --- Axis kanan manual ---
                max_line = max(line_series) if line_series else 0
                if max_line > 0:
                    step_line = max(1, round(max_line / 5, -3))  # step ribuan

                    # garis axis kanan
                    d.add(Line(bc.x + bc.width, bc.y, bc.x + bc.width, bc.y + bc.height))

                    # label axis kanan
                    for i in range(0, int(max_line) + 1, int(step_line)):
                        y = bc.y + (i / max_line) * bc.height
                        d.add(String(bc.x + bc.width + 10, y, f"{i:,}", fontSize=7, fillColor=HexColor("#ef4444")))

            # --- Legend di atas chart ---
            legend = Legend()
            legend.x = bc.x + bc.width/2 - 150   # posisikan agak tengah
            legend.y = bc.y + bc.height + 40     # taruh di atas grafik
            legend.dx = 12                       # ukuran kotak warna
            legend.dy = 12
            legend.fontName = 'Helvetica'
            legend.fontSize = 9
            legend.boxAnchor = 'n'
            legend.columnMaximum = 3             # biar semua item 1 baris
            legend.deltax = 100                  # jarak antar item
            legend.deltay = 0                    # jangan bertingkat

            legend.colorNamePairs = [
                (HexColor("#eab672"), "Limonite"),
                (HexColor("#a0c481"), "Saprolite"),
            ]

            d.add(legend)
            elements.append(d)

        elements.append(PageBreak()) 

    def add_inventory_section(title, metrics, rows, categories, bar_series, line_series):
        elements.append(Paragraph(title, styles['Heading2']))
        elements.append(Spacer(1, 6))

        # Metrics table
        table = Table(metrics, colWidths=[120, 120])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            # Kolom Metric rata kiri
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            # Kolom Value rata kanan
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))

        if rows:
            # d = Drawing(700, 200)
            d = Drawing(400, 200)   # lebih kecil agar muat di samping
            # === Bar Chart (Production In & Selling Out) ===
            bc = VerticalBarChart()
            bc.x, bc.y = 30, 30
            bc.height, bc.width = 170, 550
            bc.data = bar_series
            bc.categoryAxis.categoryNames = [str(c) for c in categories]
            bc.barWidth = 8

            # auto scale bar axis
            vmin, vmax, vstep = auto_scale_axis(bar_series)
            bc.valueAxis.valueMin = vmin
            bc.valueAxis.valueMax = vmax
            bc.valueAxis.valueStep = vstep

            bc.bars[0].fillColor = HexColor("#add2bb")  # green
            bc.bars[1].fillColor = HexColor("#eab672")  # orange


            bc.valueAxis.strokeColor = HexColor("#9ca3af")
            bc.valueAxis.labels.fillColor = HexColor("#6b7280")
            bc.categoryAxis.strokeColor = HexColor("#9ca3af")
            bc.categoryAxis.labels.fillColor = HexColor("#676a6e")


            # hilangkan outline (stroke) cukup di level series
            bc.bars[0].strokeColor = None
            bc.bars[0].strokeWidth = 0
            bc.bars[1].strokeColor = None
            bc.bars[1].strokeWidth = 0


            d.add(bc)

            # === Line Chart (Running Balance, pakai axis kanan) ===
            if line_series:
                lp = LinePlot()
                lp.x, lp.y = 50, 50
                lp.height, lp.width = 200, 550
                lp.data = [list(enumerate([safe_float(v) for v in line_series]))]

                lp.lines[0].strokeColor = HexColor("#ef4444")
                lp.lines[0].strokeWidth = 2
                lp.lines[0].symbol = makeMarker('Circle')
                d.add(lp)

                # --- Axis kanan manual ---
                max_line = max(line_series) if line_series else 0
                if max_line > 0:
                    step_line = max(1, round(max_line / 5, -3))  # step ribuan

                    # garis axis kanan
                    d.add(Line(bc.x + bc.width, bc.y, bc.x + bc.width, bc.y + bc.height))

                    # label axis kanan
                    for i in range(0, int(max_line) + 1, int(step_line)):
                        y = bc.y + (i / max_line) * bc.height
                        d.add(String(bc.x + bc.width + 10, y, f"{i:,}", fontSize=7, fillColor=HexColor("#ef4444")))

            # --- Legend di atas chart ---
            legend = Legend()
            legend.x = bc.x + bc.width/2 - 150   # posisikan agak tengah
            legend.y = bc.y + bc.height + 40     # taruh di atas grafik
            legend.dx = 12                       # ukuran kotak warna
            legend.dy = 12
            legend.fontName = 'Helvetica'
            legend.fontSize = 9
            legend.boxAnchor = 'n'
            legend.columnMaximum = 3             # biar semua item 1 baris
            legend.deltax = 100                  # jarak antar item
            legend.deltay = 0                    # jangan bertingkat

            legend.colorNamePairs = [
                (HexColor("#add2bb"), "Production In"),
                (HexColor("#eab672"), "Selling Out"),
            ]

            d.add(legend)
            elements.append(d)

        elements.append(PageBreak()) 


   # === Summary Section ===
    summary_title = Paragraph("Project Summary To-Date", styles['Heading4'])
    elements.append(summary_title)
    elements.append(Spacer(1, 6))

    # --- Mining ---
    mining_table = Table([
        ["Metric", "Value"],
        ["Total Actual", f"{summary['mining'].get('actual_total', 0):,.0f}"],
        ["Ore (Lim + Sap)", f"{summary['mining'].get('ore', 0):,.0f}"],
        ["Non Ore", f"{summary['mining'].get('non_ore', 0):,.0f}"],
    ], colWidths=[120, 100])

    mining_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.4, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
         # Kolom Metric rata kiri
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        # Kolom Value rata kanan
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))

    # --- Quality ---
    quality_table = Table([
        ["Metric", "Value"],
        ["Total Tonnage", f"{summary['quality'].get('total', 0):,.0f}"],
        ["LIM (total)",   f"{summary['quality'].get('lim', 0):,.0f}"],
        # ["LIM (%)",       f"{(summary['quality'].get('lim', 0)/(summary['quality'].get('total',1))*100):.2f}%"],
        ["SAP (total)",   f"{summary['quality'].get('sap', 0):,.0f}"],
        # ["SAP (%)",       f"{(summary['quality'].get('sap', 0)/(summary['quality'].get('total',1))*100):.2f}%"],
    ], colWidths=[120, 100])

    quality_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.4, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
         # Kolom Metric rata kiri
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        # Kolom Value rata kanan
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))

    # --- Selling ---
    actual = summary['selling'].get('actual', 0) or 0
    plan   = summary['selling'].get('plan', 0) or 0
    lim_actual = summary['selling'].get('lim_actual', 0) or 0
    sap_actual = summary['selling'].get('sap_actual', 0) or 0

    # achievement = f"{(actual / plan * 100):.0f}%" if plan > 0 else "0%"

    selling_table = Table([
        ["Metric", "Value"],
        ["Total Actual", f"{actual:,.0f}"],
        # ["Total Plan",   f"{plan:,.0f}"],
        # ["Achievement",  achievement],
        ["LIM Actual",   f"{lim_actual:,.0f}"],
        ["SAP Actual",   f"{sap_actual:,.0f}"],
    ], colWidths=[120, 100])


    selling_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.4, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        # Kolom Metric rata kiri
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        # Kolom Value rata kanan
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))

    # --- Inventory ---
    inv_table = Table([
        ["Metric", "Value"],
        ["Production In", f"{summary['inventory'].get('in', 0):,.0f}"],
        ["Selling Out",   f"{summary['inventory'].get('out', 0):,.0f}"],
        ["Current Stock", f"{summary['inventory'].get('current_stock', 0):,.0f}"],
    ], colWidths=[120, 100])

    inv_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.4, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        # Kolom Metric rata kiri
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        # Kolom Value rata kanan
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))

    # === Gabung jadi 2 kolom ===
    left_col = [Paragraph("Mining", styles['Heading5']), mining_table,
                Spacer(1,4),
                Paragraph("Material Type", styles['Heading5']), quality_table]

    right_col = [Paragraph("Selling", styles['Heading5']), selling_table,
                Spacer(1,4),
                Paragraph("Inventory", styles['Heading5']), inv_table]

    two_col = Table([
        [left_col, right_col]
    ], colWidths=[250, 250])

    elements.append(two_col)
    elements.append(Spacer(1, 10))

    # --- Breakdown Mining ---
    breakdown_table = Table([
        ["Total LIM", "Total SAP", "Total Waste", "Total Quarry",
        "Total Topsoil", "Total OB", "Total Ballast", "Total Biomass"],
        [
            f"{summary['mining'].get('lim_total', 0):,.0f}",
            f"{summary['mining'].get('sap_total', 0):,.0f}",
            f"{summary['mining'].get('waste_total', 0):,.0f}",
            f"{summary['mining'].get('quarry_total', 0):,.0f}",
            f"{summary['mining'].get('topsoil_total', 0):,.0f}",
            f"{summary['mining'].get('ob_total', 0):,.0f}",
            f"{summary['mining'].get('ballast_total', 0):,.0f}",
            f"{summary['mining'].get('biomass_total', 0):,.0f}",
        ]
    ], colWidths=[65,65,65,70,70,70,70,70])

    breakdown_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.4, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),     # kecilkan font
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),  # rapatkan tabel
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))

    elements.append(Paragraph("Productions Mining by Materials", styles['Heading5']))
    elements.append(Spacer(1, 6))
    elements.append(breakdown_table)
    elements.append(PageBreak())

    # === Mining Section ===
    total_actual = sum(safe_float(r.get("actual_total")) for r in mining["rows"])
    total_plan   = sum(safe_float(r.get("plan_total")) for r in mining["rows"])

    # hitung AVG & Achievement
    avg_actual   = total_actual / len(mining["rows"]) if mining["rows"] else 0
    achievement  = (total_actual / total_plan * 100) if total_plan > 0 else 0

    mining_metrics = [
        ["Metric", "Value"],
        ["Total Actual", f"{total_actual:,.0f}"],
        ["Ore (Lim + Sap)",f"{total_plan:,.0f}"],
        ["Non Ore",f"{avg_actual:,.0f}"],
    ]


    # === Hitung Breakdown Mining ===
    lim_total     = sum(safe_float(r.get("lim")) for r in mining["rows"])
    sap_total     = sum(safe_float(r.get("sap")) for r in mining["rows"])
    waste_total   = sum(safe_float(r.get("waste")) for r in mining["rows"])
    quarry_total  = sum(safe_float(r.get("quarry")) for r in mining["rows"])
    topsoil_total = sum(safe_float(r.get("topsoil")) for r in mining["rows"])
    ob_total      = sum(safe_float(r.get("ob")) for r in mining["rows"])
    ballast_total = sum(safe_float(r.get("ballast")) for r in mining["rows"])
    biomass_total = sum(safe_float(r.get("biomass")) for r in mining["rows"])


    # --- Buat judul dinamis ---
    if mode == "range":
        mining_title    = f"Mining by Period (Range: {date_start} → {date_end})"
        quality_title   = f"Material Type by Period (Range: {date_start} → {date_end})"
        grade_title     = f"Daily Ore by Period (Range: {date_start} → {date_end})"
        selling_title   = f"Selling by Period (Range: {date_start} → {date_end})"
        barging_title   = f"Barging by Period (Range: {date_start} → {date_end})"
        inventory_title = f"Inventory by Period (Range: {date_start} → {date_end})"
    elif mode == "year":
        mining_title    = f"Mining by Period (Year: {year})"
        quality_title   = f"Material Type by Period (Year: {year})"
        grade_title     = f"Daily Ore by Period  (Year: {year})"
        selling_title   = f"Selling by Period (Year: {year})"
        barging_title   = f"Barging by Period (Year: {year})"
        inventory_title = f"Inventory by Period (Year: {year})"
    else:
        mining_title    = "Mining by Period"
        quality_title   = "Material Type by Period"
        grade_title     = "Daily Ore by Period "
        selling_title   = "Selling by Period"
        barging_title   = "Barging by Period"
        inventory_title = "Inventory by Period"


    # Mining pakai summary + breakdown
    add_section_with_summary(
        mining_title,
        mining_metrics,
        mining["rows"],
        # [str(r['dt'].day).zfill(2) for r in mining["rows"]],
        [str(parse_label(r['dt'])).zfill(2) for r in mining["rows"]],
        [[safe_float(r.get("actual_total")) for r in mining["rows"]]],
        line_series=[safe_float(r.get("plan_total")) for r in mining["rows"]],
        bar_color="#335871",

        # --- Breakdown Mining ---
        breakdown = [
            ["Total LIM", "Total SAP", "Total Waste", "Total Quarry",
            "Total Topsoil", "Total OB", "Total Ballast", "Total Biomass"],
            [
                f"{lim_total:,.0f}",
                f"{sap_total:,.0f}",
                f"{waste_total:,.0f}",
                f"{quarry_total:,.0f}",
                f"{topsoil_total:,.0f}",
                f"{ob_total:,.0f}",
                f"{ballast_total:,.0f}",
                f"{biomass_total:,.0f}",
            ]
        ]
        
    )

    # === Quality Section ===
    prod_total = sum(safe_float(r.get("prod_total")) for r in prod["rows"])
    prod_lim   = sum(safe_float(r.get("prod_lim")) for r in prod["rows"])
    prod_sap   = sum(safe_float(r.get("prod_sap")) for r in prod["rows"])

    quality_metrics = [
        ["Metric", "Value"],
        ["Total Tonnage", f"{prod_total:,.0f}"],
        ["LIM",    f"{prod_lim:,.0f}"],
        ["SAP",    f"{prod_sap:,.0f}"],

    ]

    quality_series = [
                    [safe_float(r.get("prod_lim")) for r in prod["rows"]],
                    [safe_float(r.get("prod_sap")) for r in prod["rows"]],
                      ]
    add_ore_section(
        quality_title, 
        quality_metrics, prod["rows"],
        # [str(r['dt'].day).zfill(2) for r in prod["rows"]],
        [str(parse_label(r['dt'])).zfill(2) for r in prod["rows"]],
        quality_series,
        line_series=None,
        # bar_color=["#fac849","#9ec57c"]
        )

    # === Daily Grade Detail (auto page break if long) ===
    # grade = fetch_production_grade(date_start, date_end)
    grade_rows = grade["rows"]

    if grade_rows:
        elements.append(Paragraph(grade_title, styles['Heading2']))
        elements.append(Spacer(1, 6))
        
        
        data = [["Date","Material","Tonnage", "Ni", "Co", "Fe", "MgO", "SiO2", "SM"]]
        for r in grade_rows:
            data.append([
                r["dt"],
                r["nama_material"],    
                f"{safe_float(r['total_ore']):,.0f}",
                f"{safe_float(r['ni']):.2f}",
                f"{safe_float(r['co']):.2f}",
                f"{safe_float(r['fe']):.2f}",
                f"{safe_float(r['mgo']):.2f}",
                f"{safe_float(r['sio2']):.2f}",
                f"{safe_float(r['sm']):.2f}",
            ])

        tbl2 = Table(
            data, 
            repeatRows=1, 
            colWidths=[80,100,80,60,60,60,60,60,60]
        )
        tbl2.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#e5e7eb")),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('GRID',(0,0),(-1,-1),0.3,colors.black),

            # Default semua kanan
            ('ALIGN',(0,1),(-1,-1),'RIGHT'),

            # Override Date kiri
            ('ALIGN',(0,1),(0,-1),'LEFT'),

            # Override Material kiri
            ('ALIGN',(1,1),(1,-1),'LEFT'),
        ]))
        elements.append(tbl2)
        elements.append(Spacer(1, 10))

     # === Page break BEFORE selling ===
    elements.append(PageBreak())


    # === Selling Section ===
    rows    = sell["rows"]
    summary = sell["summary"]

    actual_total = summary.get("actual_total", 0)
    lim_actual   = summary.get("lim_actual", 0)
    sap_actual   = summary.get("sap_actual", 0)

    selling_metrics = [
        ["Metric", "Value"],
        ["Total Actual", f"{actual_total:,.0f}"],
        ["LIM Actual",   f"{lim_actual:,.0f}"],
        ["SAP Actual",   f"{sap_actual:,.0f}"],
    ]

    selling_series = [
        [safe_float(r.get("actual_lim")) for r in sell["rows"]],
        [safe_float(r.get("actual_sap")) for r in sell["rows"]]
        ]
    add_ore_section(
        selling_title, 
        selling_metrics, 
        sell["rows"],
        # [str(r['dt'].day).zfill(2) for r in sell["rows"]],
        [str(parse_label(r['dt'])).zfill(2) for r in sell["rows"]],
        selling_series,
        line_series=None,
        )
    
    # === Barging Section ===
    rows    = barging["rows"]
    summary = barging["summary"]

    actual_total = summary.get("actual_total", 0)
    lim_actual   = summary.get("lim_actual", 0)
    sap_actual   = summary.get("sap_actual", 0)

    barging_metrics = [
        ["Metric", "Value"],
        ["Total Actual", f"{actual_total:,.0f}"],
        ["LIM Actual",   f"{lim_actual:,.0f}"],
        ["SAP Actual",   f"{sap_actual:,.0f}"],
    ]

    # 2 BAR SERIES
    barging_series = [
        [safe_float(r.get("actual_lim")) for r in barging["rows"]],
        [safe_float(r.get("actual_sap")) for r in barging["rows"]],
    ]

    add_ore_section(
        barging_title,
        barging_metrics,
        inv["rows"],
        # [str(r['dt'].day).zfill(2) for r in inv["rows"]],
        [str(parse_label(r['dt'])).zfill(2) for r in inv["rows"]],
        barging_series,
        line_series=None,      # ⬅ No line
    )

    

    # === Inventory Section ===
    inv_sum = inv["summary"]
    inv_metrics = [
        ["Metric", "Value"],
        ["Opening Stock", f"{safe_float(inv_sum.get('opening_balance')):,.2f}"],
        ["Production In", f"{safe_float(inv_sum.get('total_in')):,.2f}"],
        ["Selling Out", f"{safe_float(inv_sum.get('total_out')):,.2f}"],
        ["Closing Stock", f"{safe_float(inv_sum.get('closing_balance')):,.2f}"],
    ]

    # 2 bar series
    inv_series = [
        [safe_float(r.get("total_in")) for r in inv["rows"]],
        [safe_float(r.get("total_out")) for r in inv["rows"]],
    ]


    add_inventory_section(
        inventory_title,
        inv_metrics,
        inv["rows"],
        # [str(r['dt'].day).zfill(2) for r in inv["rows"]],
        [str(parse_label(r['dt'])).zfill(2) for r in inv["rows"]],
        bar_series=inv_series,
        line_series=None  # ⬅ Hilangkan line
    )


    # === Build PDF ===
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    # response = HttpResponse(content_type="application/pdf")
    # response['Content-Disposition'] = 'attachment; filename="KQMS-summary.pdf"'
    # response.write(pdf)
    # return response

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'inline; filename="KQMS-summary.pdf"'  # selalu preview
    response.write(pdf)
    return response
