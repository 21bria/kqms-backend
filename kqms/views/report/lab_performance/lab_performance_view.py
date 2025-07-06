from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
pio.templates
from datetime import datetime, timedelta
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import connections,DatabaseError
import re
import logging
logger = logging.getLogger(__name__)
from ....utils.db_utils import get_db_vendor

# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

@login_required
def sampleTatChart(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())

    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mgoqa/report-qa/sample-tat-chart.html',context)

# Fungsi untuk mengonversi detik kembali ke format waktu
def seconds_to_time(seconds):
    if pd.isna(seconds):
        return '-'
    h, remainder = divmod(int(seconds), 3600)
    m, s = divmod(remainder, 60)
    return f'{h:02}:{m:02}:{s:02}'

def time_to_seconds(t):
    if pd.isnull(t) or t == '-' or not isinstance(t, str):
        return None
    try:
        h, m, s = map(int, t.split(':'))
        return h * 3600 + m * 60 + s
    except ValueError:
        return None

def extract_hours(t):
    if pd.isnull(t) or t == '-' or not isinstance(t, str):
        return None
    try:
        # Menghapus karakter yang tidak valid
        t = t.strip()  # Menghapus spasi tambahan
        
        # Memeriksa format waktu dengan regex
        if not re.match(r'^\d{1,3}:\d{2}(:\d{2})?$', t): #sehingga format 105:37:00 dianggap valid.
        # if not re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', t):
            return None  # Format tidak sesuai
        
        # Memproses waktu
        parts = t.split(':')
        h = int(parts[0])
        
        # Validasi panjang bagian menit dan detik
        if len(parts) == 2:  # Format HH:MM
            m = int(parts[1])
            s = 0
        elif len(parts) == 3:  # Format HH:MM:SS
            m = int(parts[1])
            s = int(parts[2])
        else:
            return None
        
        # Pastikan menit dan detik valid
        if not (0 <= m < 60) or not (0 <= s < 60):
            return None
        
        return h  # Mengembalikan jam saja
    except ValueError:
        return None

# For plotly Chart
@login_required
def chartTatMral(request):
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend


    # 🔍 Validasi tanggal dan susun kondisi WHERE
    conditions = ["mral_order = 'Yes'"]
    if start_date and end_date:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            conditions.append(f"tgl_produksi BETWEEN '{start_date}' AND '{end_date}'")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    where_clause = "WHERE " + " AND ".join(conditions)

    # 🛠️ Query berdasarkan DB vendor
    if db_vendor == 'mysql':
        query = f"""
            SELECT 
                tgl_produksi, 
                mral_order,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' THEN sample_number END) AS jml_mral,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'OnTime' AND tat_mral IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'Late' AND tat_mral IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) IS NULL THEN '00:00:00'
                    ELSE CONCAT(
                        LPAD(FLOOR(AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) / 3600), 2, '0'), ':',
                        LPAD(FLOOR((AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) % 3600) / 60), 2, '0'), ':',
                        LPAD(AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) % 60, 2, '0')
                    )
                END AS average_time,
                '03:00:00' AS time_limit   
            FROM laboratory_performance_tat
            {where_clause}
            GROUP BY tgl_produksi, mral_order
            ORDER BY tgl_produksi ASC;
        """

    elif db_vendor in ['mssql', 'microsoft']:
        query = f"""
            SELECT 
                tgl_produksi, 
                mral_order,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' THEN sample_number END) AS jml_mral,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'OnTime' AND tat_mral IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'Late' AND tat_mral IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(DATEDIFF(SECOND, delivery, release_mral)) IS NULL THEN '00:00:00'
                    ELSE 
                        RIGHT('00' + CAST(AVG(DATEDIFF(SECOND, delivery, release_mral)) / 3600 AS VARCHAR), 2) + ':' +
                        RIGHT('00' + CAST((AVG(DATEDIFF(SECOND, delivery, release_mral)) % 3600) / 60 AS VARCHAR), 2) + ':' +
                        RIGHT('00' + CAST(AVG(DATEDIFF(SECOND, delivery, release_mral)) % 60 AS VARCHAR), 2)
                END AS average_time,
                '03:00:00' AS time_limit
            FROM laboratory_performance_tat
            {where_clause}
            GROUP BY tgl_produksi, mral_order
            ORDER BY tgl_produksi ASC;
        """

    elif db_vendor == 'postgresql':
        query = f"""
            SELECT 
                tgl_produksi,
                mral_order,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' THEN sample_number END) AS jml_mral,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'OnTime' AND tat_mral IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'Late' AND tat_mral IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NULL THEN sample_number END) AS not_released,
                COALESCE(
                    TO_CHAR(
                        MAKE_INTERVAL(secs => ROUND(AVG(EXTRACT(EPOCH FROM release_mral - delivery)))), 
                        'HH24:MI:SS'
                    ),
                    '00:00:00'
                ) AS average_time,
                '03:00:00' AS time_limit
            FROM laboratory_performance_tat
            {where_clause}
            GROUP BY tgl_produksi, mral_order
            ORDER BY tgl_produksi ASC;
        """

    else:
        raise ValueError("Unsupported database vendor.")


    # df = pd.read_sql_query(query, connection)
    df = pd.read_sql_query(query, connections['kqms_db'])

    # Mengonversi kolom waktu
    df['TAT_seconds']   = df['average_time'].apply(time_to_seconds)
    df['Limit_seconds'] = df['time_limit'].apply(time_to_seconds)
    # Menambahkan kolom dengan jam saja
    df['Avg_hours']     = df['average_time'].apply(extract_hours)
    df['Limit_hours']   = df['time_limit'].apply(extract_hours)
        
    # Konversi kembali ke format waktu untuk ditampilkan pada grafik
    df['TAT_formatted']   = df['TAT_seconds'].apply(seconds_to_time)
    df['Limit_formatted'] = df['Limit_seconds'].apply(seconds_to_time)

    # Mengurutkan DataFrame berdasarkan tanggal produksi
    df = df.sort_values(by='tgl_produksi')
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(0,0,0,0)', 
            annotations=[
                {
                    "text": "No matching data found",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 14}
                }
            ],
            height=360,
            template="plotly_dark" if theme == "dark" else "plotly_white",
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    # Load data
    order    = df['jml_mral'].tolist()
    limit    = df['Limit_hours'].tolist()
    avg_time = df['Avg_hours'].tolist()
  
    x        = df['tgl_produksi'].tolist()
    avg_time_formatted = df['TAT_formatted'].tolist()
    limit_formatted = df['Limit_formatted'].tolist()
    
    fig = go.Figure()

    # Warna untuk masing-masing trace
    colors = {
        'order'   : '#92cd08',
        'avg_time': '#edda0c',
        'limit'   : '#d68000'
    }
    
    # Menambahkan grafik batang untuk Samples
    fig.add_trace(go.Bar(
        x=x,
        y=order,
        text=order, 
        name="Samples",
        texttemplate='%{text:.0f}',
    ))
   
    # Menambahkan garis untuk TAT Limit dengan sumbu y kedua
    fig.add_trace(go.Scatter(
            x=x,
            y=limit,
            mode='lines+markers',
            marker=dict(size=7),
            name='TAT Limit',
            yaxis='y3',  # Menentukan sumbu y kedua
            text=limit_formatted,
            texttemplate='%{text}'
        ))
    
    # Menambahkan garis untuk TAT Mral dengan sumbu y kedua
    fig.add_trace(go.Scatter(
        x=x,
        y=avg_time,
        mode='lines+markers',
        marker=dict(size=7),
        name='TAT Mral',
        yaxis='y3', # Menentukan sumbu y kedua
        text=avg_time_formatted,
        texttemplate='%{text}'
    ))

    # Mengatur layout grafik
    fig.update_layout(
        legend=dict(orientation="h"),
        title=f'TAT MRAL ({start_date} to {end_date})',
        title_font=dict(size=16),
        #margin=dict(l=40, r=25, t=60, b=25), 
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        xaxis=dict(
            # title='Tanggal Produksi',
            title_font=dict(size=12),
        ),
        yaxis=dict(
            title='Samples Order',
            title_font=dict(size=12),
            side='left',
            showgrid=True,
            showline=True
        ),
        yaxis2=dict(
            # title='Waktu (detik)',
            title_font=dict(size=12),
            side='right',
            overlaying='y',  # Menggunakan sumbu y yang sama dengan overlay
            showgrid=True,
            showline=True,
            showticklabels=False,
            anchor='x'
        ),
        yaxis3=dict(
            # title='Average Time (detik)',
            title_font=dict(size=12),
            side='right',
            overlaying='y',  # Menggunakan sumbu y yang sama dengan overlay
            showgrid=True,
            showline=True,
            anchor='x',
            showticklabels=True,  # Menyembunyikan label teks
            position=0.95,
        ),
        bargap=0.2, 
        height=360,
        template="plotly_dark" if theme == "dark" else "plotly_white",
    )
    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True
})
    return JsonResponse({'plot_div': plot_div})

@login_required
def chartTatRoa(request):
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend

    # 🔍 Validasi dan susun WHERE clause
    conditions = ["roa_order = 'Yes'"]
    if start_date and end_date:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            conditions.append(f"tgl_produksi BETWEEN '{start_date}' AND '{end_date}'")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    where_clause = "WHERE " + " AND ".join(conditions)

    # 🛠️ Query berdasarkan DB vendor
    if db_vendor == 'mysql':
        query = f"""
            SELECT 
                tgl_produksi,
                roa_order,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' THEN sample_number END) AS jml_roa,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'OnTime' AND tat_roa IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'Late' AND tat_roa IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) IS NULL THEN '00:00:00'
                    ELSE 
                        LPAD(FLOOR(AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) / 3600), 2, '0') || ':' ||
                        LPAD(FLOOR((AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) % 3600) / 60), 2, '0') || ':' ||
                        LPAD(AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) % 60, 2, '0')
                END AS average_time,
                '120:00:00' AS time_limit
            FROM laboratory_performance_tat
            {where_clause}
            GROUP BY tgl_produksi, roa_order
            ORDER BY tgl_produksi ASC
        """

    elif db_vendor in ['mssql', 'microsoft']:
        query = f"""
            SELECT 
                tgl_produksi,
                roa_order,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' THEN sample_number END) AS jml_roa,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'OnTime' AND tat_roa IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'Late' AND tat_roa IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(DATEDIFF(SECOND, delivery, release_roa)) IS NULL THEN '00:00:00'
                    ELSE 
                        RIGHT('00' + CAST(AVG(DATEDIFF(SECOND, delivery, release_roa)) / 3600 AS VARCHAR), 2) + ':' +
                        RIGHT('00' + CAST((AVG(DATEDIFF(SECOND, delivery, release_roa)) % 3600) / 60 AS VARCHAR), 2) + ':' +
                        RIGHT('00' + CAST(AVG(DATEDIFF(SECOND, delivery, release_roa)) % 60 AS VARCHAR), 2)
                END AS average_time,
                '120:00:00' AS time_limit
            FROM laboratory_performance_tat
            {where_clause}
            GROUP BY tgl_produksi, roa_order
            ORDER BY tgl_produksi ASC
        """

    elif db_vendor == 'postgresql':
        query = f"""
            SELECT 
                tgl_produksi,
                roa_order,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' THEN sample_number END) AS jml_roa,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'OnTime' AND tat_roa IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'Late' AND tat_roa IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NULL THEN sample_number END) AS not_released,
                COALESCE(
                    TO_CHAR(INTERVAL '1 second' * ROUND(AVG(EXTRACT(EPOCH FROM release_roa - delivery))), 'HH24:MI:SS'),
                    '00:00:00'
                ) AS average_time,
                '120:00:00' AS time_limit
            FROM laboratory_performance_tat
            {where_clause}
            GROUP BY tgl_produksi, roa_order
            ORDER BY tgl_produksi ASC
        """
    else:
        raise ValueError("Unsupported database vendor.")

    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query)
            chart_data = cursor.fetchall()

        # Create DataFrame from SQL query results
        df = pd.DataFrame(chart_data, 
                          columns=['tgl_produksi', 'roa_order','jml_roa','released_on_tat','released_over_tat',
                                   'total_released','not_released','average_time','time_limit'
                                   ])
        
        # Mengonversi kolom waktu
        df['TAT_seconds']   = df['average_time'].apply(time_to_seconds)
        df['Limit_seconds'] = df['time_limit'].apply(time_to_seconds)
        # Menambahkan kolom dengan jam saja
        df['Avg_hours']     = df['average_time'].apply(extract_hours)
        df['Limit_hours']   = df['time_limit'].apply(extract_hours)
            
        # Konversi kembali ke format waktu untuk ditampilkan pada grafik
        df['TAT_formatted']   = df['TAT_seconds'].apply(seconds_to_time)
        df['Limit_formatted'] = df['Limit_seconds'].apply(seconds_to_time)

        # Mengurutkan DataFrame berdasarkan tanggal produksi
        df = df.sort_values(by='tgl_produksi')
        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                plot_bgcolor='rgba(0,0,0,0)', 
                annotations=[
                    {
                        "text": "No matching data found",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 14}
                    }
                ],
                height=360,
                template="plotly_dark" if theme == "dark" else "plotly_white",
            )
            plot_div = fig.to_html(full_html=False)
            return JsonResponse({'plot_div': plot_div})
        
        # Load data
        x        = df['tgl_produksi'].tolist()
        order    = df['jml_roa'].tolist()
        limit    = df['Limit_hours'].tolist()
        avg_time = df['Avg_hours'].tolist()
        # avg_time = df['average_time'].tolist()
        avg_time_formatted = df['TAT_formatted'].tolist()
        limit_formatted    = df['Limit_formatted'].tolist()
        
        fig = go.Figure()

        # Menambahkan grafik batang untuk Samples
        fig.add_trace(go.Bar(
            x=x,
            y=order,
            text=order, 
            name="Samples",
            texttemplate='%{text:.0f}',
            # yaxis='y1', 
        ))
    
        # Menambahkan garis untuk TAT Limit dengan sumbu y kedua
        fig.add_trace(go.Scatter(
                x=x,
                y=limit,
                mode='lines+markers',
                marker=dict(size=7),
                name='TAT Limit',
                yaxis='y3',  # Menentukan sumbu y kedua
                text=limit_formatted,
                textposition='top center',
                texttemplate='%{text}'
            ))
        
    # Menambahkan garis untuk TAT Mral dengan sumbu y kedua
        fig.add_trace(go.Scatter(
            x=x,
            y=avg_time,
            mode='lines+markers',
            marker=dict(size=7),
            name='TAT ROA',
            yaxis='y3', # Menentukan sumbu y kedua
            text=avg_time_formatted,
            texttemplate='%{text}'
        ))

        # Mengatur layout grafik
        fig.update_layout(
            legend=dict(orientation="h"),
            title=f'TAT ROA ({start_date} to {end_date})',
            title_font=dict(size=16),
            #margin=dict(l=40, r=25, t=60, b=25), 
            title_x=0.5,
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
           yaxis=dict(
            title='Samples Order',
            title_font=dict(size=12),
            side='left',
            showgrid=True,
            showline=True
        ),
           yaxis2=dict(
            # title='Waktu (detik)',
            title_font=dict(size=12),
            side='right',
            overlaying='y',  # Menggunakan sumbu y yang sama dengan overlay
            showgrid=True,
            showline=True,
            showticklabels=False,
            anchor='x'
        ),
        yaxis3=dict(
            # title='Average Time (detik)',
            title_font=dict(size=12),
            side='right',
            overlaying='y',  # Menggunakan sumbu y yang sama dengan overlay
            showgrid=True,
            showline=True,
            anchor='x',
            showticklabels=True,  # Menyembunyikan label teks
            position=0.95,
        ),

            bargap=0.2, 
            height=360,
            template="plotly_dark" if theme == "dark" else "plotly_white",
        )
        plot_div = fig.to_html(full_html=False, config={
        'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
        'responsive': True
    })
        # Return the JSON response
        response_data = {
                'tgl'           : df['tgl_produksi'].tolist(),
                'order'         : df['jml_roa'].tolist(),
                'on_tat'        : df['released_on_tat'].tolist(),
                'over_tat'      : df['released_over_tat'].tolist(),
                'total_released': df['total_released'].tolist(),
                'not_released'  : df['not_released'].tolist(),
                'average_time'  : df['average_time'].tolist(),
                'time_limit'    : df['time_limit'].tolist(),
                'plot_div'      : plot_div,
                
            }

        return JsonResponse(response_data, safe=False)
    
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)
    
@login_required    
def getDataMralByWeeks(request):
    start_date = request.GET.get('startDate')
    end_date   = request.GET.get('endDate')

    # 🔍 Validasi dan susun WHERE clause
    conditions = ["mral_order = 'Yes'"]
    if start_date and end_date:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            conditions.append(f"tgl_produksi BETWEEN '{start_date}' AND '{end_date}'")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    where_clause = "WHERE " + " AND ".join(conditions)

    # 🔀 SQL berdasarkan database vendor
    if db_vendor == 'mysql':
        sql_query = f"""
            SELECT 
                tgl_produksi,
                mral_order,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' THEN sample_number END) AS jml_mral,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'OnTime' AND tat_mral IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'Late' AND tat_mral IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) IS NULL THEN '00:00:00'
                    ELSE 
                        LPAD(FLOOR(AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) / 3600), 2, '0') || ':' ||
                        LPAD(FLOOR((AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) % 3600) / 60), 2, '0') || ':' ||
                        LPAD(AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) % 60, 2, '0')
                END AS average_time,
                '03:00:00' AS time_limit
            FROM laboratory_performance_tat
            {where_clause}
            GROUP BY tgl_produksi, mral_order
            ORDER BY tgl_produksi ASC
        """

    elif db_vendor in ['mssql', 'microsoft']:
        sql_query = f"""
            SELECT 
                tgl_produksi,
                mral_order,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' THEN sample_number END) AS jml_mral,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'OnTime' AND tat_mral IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'Late' AND tat_mral IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(DATEDIFF(SECOND, delivery, release_mral)) IS NULL THEN '00:00:00'
                    ELSE 
                        RIGHT('00' + CAST(AVG(DATEDIFF(SECOND, delivery, release_mral)) / 3600 AS VARCHAR), 2) + ':' +
                        RIGHT('00' + CAST((AVG(DATEDIFF(SECOND, delivery, release_mral)) % 3600) / 60 AS VARCHAR), 2) + ':' +
                        RIGHT('00' + CAST(AVG(DATEDIFF(SECOND, delivery, release_mral)) % 60 AS VARCHAR), 2)
                END AS average_time,
                '03:00:00' AS time_limit
            FROM laboratory_performance_tat
            {where_clause}
            GROUP BY tgl_produksi, mral_order
            ORDER BY tgl_produksi ASC
        """

    elif db_vendor == 'postgresql':
        sql_query = f"""
            SELECT 
                tgl_produksi,
                mral_order,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' THEN sample_number END) AS jml_mral,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'OnTime' AND tat_mral IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'Late' AND tat_mral IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NULL THEN sample_number END) AS not_released,
                COALESCE(
                    TO_CHAR(INTERVAL '1 second' * ROUND(AVG(EXTRACT(EPOCH FROM release_mral - delivery))), 'HH24:MI:SS'),
                    '00:00:00'
                ) AS average_time,
                '03:00:00' AS time_limit
            FROM laboratory_performance_tat
            {where_clause}
            GROUP BY tgl_produksi, mral_order
            ORDER BY tgl_produksi ASC
        """
    else:
        raise ValueError("Unsupported database vendor.")


    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    # print(sql_data)  # Cetak hasil query
    
    return JsonResponse({'data': sql_data})

@login_required
def getDataRoaByWeeks(request):
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')

    if db_vendor == 'mysql':
        sql_query = f"""
            SELECT 
                tgl_produksi,
                roa_order,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' THEN sample_number END) AS jml_roa,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'OnTime' AND tat_roa IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'Late' AND tat_roa IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) IS NULL THEN '00:00:00'
                    ELSE CONCAT(
                        LPAD(FLOOR(AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) / 3600), 2, '0'), ':',
                        LPAD(FLOOR((AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) % 3600) / 60), 2, '0'), ':',
                        LPAD(AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) % 60, 2, '0')
                    )
                END AS average_time,
                '120:00:00' AS time_limit
            FROM laboratory_performance_tat
            WHERE roa_order = 'Yes'
        """
    elif db_vendor in ['mssql', 'microsoft']:
        sql_query = f"""
            SELECT 
                tgl_produksi,
                roa_order,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' THEN sample_number END) AS jml_roa,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'OnTime' AND tat_roa IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'Late' AND tat_roa IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(DATEDIFF(SECOND, delivery, release_roa)) IS NULL THEN '00:00:00'
                    ELSE 
                        RIGHT('00' + CAST(AVG(DATEDIFF(SECOND, delivery, release_roa)) / 3600 AS VARCHAR), 2) + ':' +
                        RIGHT('00' + CAST((AVG(DATEDIFF(SECOND, delivery, release_roa)) % 3600) / 60 AS VARCHAR), 2) + ':' +
                        RIGHT('00' + CAST(AVG(DATEDIFF(SECOND, delivery, release_roa)) % 60 AS VARCHAR), 2)
                END AS average_time,
                '120:00:00' AS time_limit
            FROM laboratory_performance_tat
            WHERE roa_order = 'Yes'
        """
    elif db_vendor == 'postgresql':
        sql_query = f"""
            SELECT 
                tgl_produksi,
                roa_order,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' THEN sample_number END) AS jml_roa,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'OnTime' AND tat_roa IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'Late' AND tat_roa IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NULL THEN sample_number END) AS not_released,
                COALESCE(
                    TO_CHAR(
                        INTERVAL '1 second' * ROUND(AVG(EXTRACT(EPOCH FROM release_roa - delivery))),
                        'HH24:MI:SS'
                    ),
                    '00:00:00'
                ) AS average_time,
                '120:00:00' AS time_limit
            FROM laboratory_performance_tat
            WHERE roa_order = 'Yes'
        """
    else:
        raise ValueError("Unsupported database vendor.")

    if start_date and end_date:
        sql_query += f" AND tgl_produksi BETWEEN '{start_date}' AND '{end_date}' "

    sql_query += """
        GROUP BY tgl_produksi, roa_order
        ORDER BY tgl_produksi ASC
    """


    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        sql_data = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    # print(sql_data)  # Cetak hasil query
    return JsonResponse({'data': sql_data})

#List Data Tables:
class SamplesDuplicatedMral(View):
    def post(self, request):
        data_ore = self._datatables(request)
        return JsonResponse(data_ore, safe=False)
    
    def _datatables(self, request):
        datatables          = request.POST
        draw                = int(datatables.get('draw'))
        start               = int(datatables.get('start'))
        length              = int(datatables.get('length'))
        search_value        = datatables.get('search[value]')
        order_column_index  = int(datatables.get('order[0][column]'))
        order_dir           = datatables.get('order[0][dir]')

        sql_query = """
            SELECT release_date, nama_material, sample_number,
                   sample_original, ni, ni_ori, ni_diff, ni_rel_diff, ni_rel_abs, ni_error,
                   co, co_ori, co_diff, co_rel_diff, co_rel_abs, co_error,
                   fe, fe_ori, fe_diff, fe_rel_diff, fe_rel_abs, fe_error,
                   mgo, mgo_ori, mgo_diff, mgo_rel_diff, mgo_rel_abs, mgo_error,
                   sio2, sio2_ori, sio2_diff, sio2_rel_diff, sio2_rel_abs, sio2_error
            FROM sample_duplicated_mral
        """

        params = []

        from_date = request.POST.get('from_date')
        to_date   = request.POST.get('to_date')

        if from_date and to_date:
            sql_query += " WHERE release_date BETWEEN %s AND %s"
            params.extend([from_date, to_date])

        if search_value:
            sql_query += " AND (sample_number LIKE %s OR nama_material LIKE %s)"
            params.extend([f"%{search_value}%", f"%{search_value}%"])   

        if order_dir == 'desc':
            sql_query += f" ORDER BY {order_column_index} DESC"
        else:
            sql_query += f" ORDER BY {order_column_index} ASC"

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(sql_query, params)
            columns = [col[0] for col in cursor.description]
            sql_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        total_records = len(sql_data)

        paginator   = Paginator(sql_data, length)
        total_pages = paginator.num_pages

        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = list(object_list)

        return {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data,
            'start': start,
            'length': length,
            'totalPages': total_pages,
        }
