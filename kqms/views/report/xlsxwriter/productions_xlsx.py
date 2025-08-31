from io import BytesIO
from django.http import HttpResponse
from django.utils import timezone
import xlsxwriter
from datetime import date

# Contoh fungsi ambil data dari DB — sesuaikan dengan modelmu
def get_ore_rows(date_start: str, date_end: str, material: str = "ALL"):
    """
    Return list[dict]: [{'date':'2025-08-01','total':1200,'lim':700,'sap':500}, ...]
    Ganti dengan query ke DB kamu (aggregate by date).
    """
    # --- DEMO DATA (ganti dengan queryset aggregate kamu) ---
    demo = [
        {"date": "2025-08-01", "total": 1200, "lim": 700, "sap": 500},
        {"date": "2025-08-02", "total": 950,  "lim": 450, "sap": 500},
        {"date": "2025-08-03", "total": 1100, "lim": 600, "sap": 500},
    ]
    # Kalau filter material != ALL, kamu bisa nolkan yang lain atau agregasi sesuai kebutuhan
    if material == "LIM":
        for r in demo:
            r["total"] = r["lim"]
            r["sap"] = 0
    elif material == "SAP":
        for r in demo:
            r["total"] = r["sap"]
            r["lim"] = 0
    return demo

def excel_ore_summary(request):
    # Ambil filter
    date_start = request.GET.get("date_start") or str(date.today().replace(day=1))
    date_end   = request.GET.get("date_end")   or str(date.today())
    material   = request.GET.get("material", "ALL").upper()

    rows = get_ore_rows(date_start, date_end, material)  # <- fungsi kamu sendiri
    n = len(rows)

    # Summary
    total_all = sum(r["total"] for r in rows) if n else 0
    total_lim = sum(r.get("lim", 0) for r in rows)
    total_sap = sum(r.get("sap", 0) for r in rows)
    avg_daily = total_all / n if n else 0
    max_day = max(rows, key=lambda r: r["total"]) if n else None
    min_day = min(rows, key=lambda r: r["total"]) if n else None
    pct_lim = (100 * total_lim / total_all) if total_all else 0
    pct_sap = (100 * total_sap / total_all) if total_all else 0

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})

    # Styles
    fmt_title = workbook.add_format({'bold': True, 'font_size': 14})
    fmt_th    = workbook.add_format({'bold': True, 'bg_color': '#F3F4F6', 'border': 1})
    fmt_td    = workbook.add_format({'border': 1})
    fmt_num   = workbook.add_format({'border': 1, 'num_format': '#,##0'})
    fmt_small = workbook.add_format({'font_size': 9, 'italic': True, 'font_color': '#6B7280'})

    # Sheet Data
    ws_data = workbook.add_worksheet('Data')
    ws_data.write_row('A1', ['Date', 'Total', 'LIM', 'SAP'], fmt_th)
    for i, r in enumerate(rows, start=2):
        ws_data.write(f'A{i}', r['date'], fmt_td)
        ws_data.write_number(f'B{i}', r['total'], fmt_num)
        ws_data.write_number(f'C{i}', r.get('lim', 0), fmt_num)
        ws_data.write_number(f'D{i}', r.get('sap', 0), fmt_num)
    ws_data.set_column('A:A', 12)
    ws_data.set_column('B:D', 12)
    # ws_data.hide()

    # Sheet Summary
    ws_sum = workbook.add_worksheet('Summary')
    ws_sum.write('A1', 'Ore Report — Summary', fmt_title)
    ws_sum.write('A2', f'Range: {date_start} → {date_end}', fmt_small)
    ws_sum.write('A3', f'Material: {material}', fmt_small)
    ws_sum.write('F2', f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}', fmt_small)

    ws_sum.write_row('A5', ['Metric', 'Value'], fmt_th)
    row = 6
    ws_sum.write(f'A{row}', 'Total tonnage', fmt_td); ws_sum.write_number(f'B{row}', total_all, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'Average per day', fmt_td); ws_sum.write_number(f'B{row}', avg_daily, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'LIM (total)', fmt_td); ws_sum.write_number(f'B{row}', total_lim, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'LIM (%)', fmt_td); ws_sum.write(f'B{row}', f'{pct_lim:.1f}%', fmt_td); row += 1
    ws_sum.write(f'A{row}', 'SAP (total)', fmt_td); ws_sum.write_number(f'B{row}', total_sap, fmt_num); row += 1
    ws_sum.write(f'A{row}', 'SAP (%)', fmt_td); ws_sum.write(f'B{row}', f'{pct_sap:.1f}%', fmt_td); row += 1
    if max_day:
        ws_sum.write(f'A{row}', 'Max day', fmt_td); ws_sum.write(f'B{row}', f"{max_day['date']} • {max_day['total']:,}", fmt_td); row += 1
    if min_day:
        ws_sum.write(f'A{row}', 'Min day', fmt_td); ws_sum.write(f'B{row}', f"{min_day['date']} • {min_day['total']:,}", fmt_td); row += 1
    ws_sum.set_column('A:A', 22)
    ws_sum.set_column('B:B', 20)

    # Chart
    if n:
        first = 2
        last = n + 1

        # Stacked Column: LIM + SAP  ✅ gunakan subtype='stacked'
        col_chart = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})
        col_chart.set_title({'name': 'Ore Trend'})
        col_chart.set_legend({'position': 'bottom'})
        col_chart.set_y_axis({'name': 'Tonase'})
        col_chart.set_x_axis({'name': 'Date'})

        col_chart.add_series({
            'name':       '=Data!$C$1',
            'categories': f'=Data!$A${first}:$A${last}',
            'values':     f'=Data!$C${first}:$C${last}',
        })
        col_chart.add_series({
            'name':       '=Data!$D$1',
            'categories': f'=Data!$A${first}:$A${last}',
            'values':     f'=Data!$D${first}:$D${last}',
        })

        col_chart.set_style(10)
        col_chart.set_plotarea({'layout': {'x': 0.10, 'y': 0.20, 'width': 0.80, 'height': 0.65}})
        col_chart.set_plotarea({'border': {'color': '#CCCCCC'}})

        # Line: Total
        line_chart = workbook.add_chart({'type': 'line'})
        line_chart.add_series({
            'name':       '=Data!$B$1',
            'categories': f'=Data!$A${first}:$A${last}',
            'values':     f'=Data!$B${first}:$B${last}',
        })

        # Combine
        col_chart.combine(line_chart)

        # Tempel chart
        ws_sum.insert_chart('D5', col_chart, {'x_scale': 1.2, 'y_scale': 1.2})


    workbook.close()
    output.seek(0)

    filename = f"productions-summary_{date_start}_to_{date_end}.xlsx"
    resp = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp