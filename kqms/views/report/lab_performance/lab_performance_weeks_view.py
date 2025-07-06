from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connections
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio
pio.templates
import re
from ....utils.db_utils import get_db_vendor
 # Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

@login_required
def sampleWeekTatChart(request):
    return render(request, 'admin-mgoqa/report-qa/sample-tat-weeks-chart.html')

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
        if not re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', t):
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
        
        # return h  # Mengembalikan jam saja
        # Menghitung total jam termasuk jam yang melebihi 24 jam
        total_hours = h + (m / 60) + (s / 3600)
        
        return total_hours
    except ValueError:
        return None

# For plotly Chart
@login_required
def chartWeeksTatMral(request):
    jml_week = request.GET.get('jml_week')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend

    if not jml_week:
        jml_week = 5

    if db_vendor == 'mysql':
        query = f"""
            SELECT 
                YEAR(tgl_produksi) AS year,
                CONCAT('Week ', WEEK(tgl_produksi)) AS minggu,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' THEN sample_number END) AS jml_mral,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'OnTime' AND tat_mral IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'Late' AND tat_mral IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) IS NULL THEN '00:00:00'
                    ELSE 
                        LPAD(FLOOR(AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) / 3600), 2, '0') + ':' +
                        LPAD(FLOOR((AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) % 3600) / 60), 2, '0') + ':' +
                        LPAD(AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) % 60, 2, '0')
                END AS average_time,
                '03:00:00' AS time_limit
            FROM laboratory_performance_tat
            WHERE mral_order = 'Yes' 
                AND tgl_produksi >= DATE_SUB(CURDATE(), INTERVAL {jml_week} WEEK)
            GROUP BY YEAR(tgl_produksi), WEEK(tgl_produksi)
            ORDER BY minggu ASC;
        """
    elif db_vendor in ['mssql', 'microsoft']:
        query = f"""
            SELECT 
                YEAR(tgl_produksi) AS year,
                CONCAT('Week ', DATEPART(WEEK, tgl_produksi)) AS minggu, 
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
            WHERE mral_order = 'Yes' 
                AND tgl_produksi >= DATEADD(WEEK, -{jml_week}, GETDATE())
            GROUP BY YEAR(tgl_produksi), DATEPART(WEEK, tgl_produksi)
            ORDER BY minggu ASC;
        """
    elif db_vendor == 'postgresql':
        query = f"""
            SELECT 
                EXTRACT(YEAR FROM tgl_produksi)::INT AS year,
                CONCAT('Week ', EXTRACT(WEEK FROM tgl_produksi)::INT) AS minggu,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' THEN sample_number END) AS jml_mral,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'OnTime' AND tat_mral IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'Late' AND tat_mral IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NULL THEN sample_number END) AS not_released,
                COALESCE(
                    TO_CHAR(
                        INTERVAL '1 second' * ROUND(AVG(EXTRACT(EPOCH FROM release_mral - delivery))),
                        'HH24:MI:SS'
                    ),
                    '00:00:00'
                ) AS average_time,
                '03:00:00' AS time_limit
            FROM laboratory_performance_tat
            WHERE mral_order = 'Yes' 
                AND tgl_produksi >= CURRENT_DATE - INTERVAL '{jml_week} weeks'
            GROUP BY EXTRACT(YEAR FROM tgl_produksi), EXTRACT(WEEK FROM tgl_produksi)
            ORDER BY minggu ASC;
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
    df['Limit_hours'] = df['time_limit'].apply(extract_hours)
        
    # Konversi kembali ke format waktu untuk ditampilkan pada grafik
    df['TAT_formatted']   = df['TAT_seconds'].apply(seconds_to_time)
    df['Limit_formatted'] = df['Limit_seconds'].apply(seconds_to_time)

    # Mengurutkan DataFrame berdasarkan tanggal produksi
    df = df.sort_values(by='minggu')
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
    x        = df['minggu'].tolist()
    avg_time_formatted = df['TAT_formatted'].tolist()
    limit_formatted    = df['Limit_formatted'].tolist()
    num_data = len(x)
    
    fig = go.Figure()

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
            yaxis='y2',  # Menentukan sumbu y kedua
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
        yaxis='y2', # Menentukan sumbu y kedua
        text=avg_time_formatted,
        texttemplate='%{text}'
    ))

    # Mengatur layout grafik
    fig.update_layout(
        legend=dict(orientation="h"),
        title=f'TAT MRAL of last {num_data} weeks',
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
            # showgrid=False,
            # showline=False
        ),
        yaxis2=dict(
            # title='Average Time (detik)',
            title_font=dict(size=12),
            side='right',
            overlaying='y',  # Menggunakan sumbu y yang sama dengan overlay
            showgrid=False,
            showline=False,
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
def chartWeeksTatRoa(request):
    # Assuming jml_week is fetched from the GET request
    jml_week = request.GET.get('jml_week')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend
    # Sanitasi input jml_week
    try:
        jml_week = int(jml_week)
    except (TypeError, ValueError):
        jml_week = 4  # Default jika invalid

    if db_vendor == 'mysql':
        query = f"""
        SELECT 
                YEAR(tgl_produksi) AS year,
                CONCAT('Week ', WEEK(tgl_produksi)) AS minggu,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' THEN sample_number END) AS jml_roa,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'OnTime' AND tat_roa IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'Late' AND tat_roa IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) IS NULL THEN '00:00:00'
                    ELSE 
                        LPAD(FLOOR(AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) / 3600), 2, '0') + ':' +
                        LPAD(FLOOR((AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) % 3600) / 60), 2, '0') + ':' +
                        LPAD(AVG(TIMESTAMPDIFF(SECOND, delivery, release_roa)) % 60, 2, '0')
                END AS average_time,
                '105:00:00' AS time_limit,
                120 AS time_limit_hours
            FROM laboratory_performance_tat
            WHERE roa_order = 'Yes' 
                AND tgl_produksi >= DATE_SUB(CURDATE(), INTERVAL {jml_week} WEEK)
            GROUP BY YEAR(tgl_produksi), WEEK(tgl_produksi)
            ORDER BY minggu ASC;
        """
    elif db_vendor in ['mssql', 'microsoft']:
        query = f"""
        SELECT 
                YEAR(tgl_produksi) AS year,
                CONCAT('Week ', DATEPART(WEEK, tgl_produksi)) AS minggu,
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
                '105:00:00' AS time_limit,
                120 AS time_limit_hours
            FROM laboratory_performance_tat
            WHERE roa_order = 'Yes' 
                AND tgl_produksi >= DATEADD(WEEK, -{jml_week}, GETDATE())
            GROUP BY YEAR(tgl_produksi), DATEPART(WEEK, tgl_produksi)
            ORDER BY minggu ASC;
        """
    elif db_vendor == 'postgresql':
        query = f"""
        SELECT 
                EXTRACT(YEAR FROM tgl_produksi)::INT AS year,
                CONCAT('Week ', EXTRACT(WEEK FROM tgl_produksi)::INT) AS minggu,
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
                '105:00:00' AS time_limit,
                120 AS time_limit_hours
            FROM laboratory_performance_tat
            WHERE roa_order = 'Yes' 
                AND tgl_produksi >= CURRENT_DATE - INTERVAL '{jml_week} weeks'
            GROUP BY EXTRACT(YEAR FROM tgl_produksi), EXTRACT(WEEK FROM tgl_produksi)
            ORDER BY minggu ASC;
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
    df = df.sort_values(by='minggu')
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
    order    = df['jml_roa'].tolist()
    limit    = df['time_limit_hours'].tolist()
    avg_time = df['Avg_hours'].tolist()
    x        = df['minggu'].tolist()
    avg_time_formatted = df['TAT_formatted'].tolist()
    num_data = len(x)
    
    fig = go.Figure()

    
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
            yaxis='y2',  # Menentukan sumbu y kedua
            text=limit,
            # texttemplate='%{text}'
            texttemplate='%{text} Jam', 
            textposition='top center'
        ))
    
  # Menambahkan garis untuk TAT Mral dengan sumbu y kedua
    fig.add_trace(go.Scatter(
        x=x,
        y=avg_time,
        mode='lines+markers',
        marker=dict(size=7),
        name='TAT ROA',
        yaxis='y2', # Menentukan sumbu y kedua
        text=avg_time_formatted,
        texttemplate='%{text}'
    ))

    # Mengatur layout grafik
    fig.update_layout(
        legend=dict(orientation="h"),
        title=f'TAT ROA of last {num_data} weeks',
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

#  For Count by Week group - list data
@login_required
def getMralGroupWeeks(request):
    jml_week = request.GET.get('jml_week')

    if not jml_week:
        jml_week = 5

    if db_vendor == 'mysql':
        sql_query = f"""
            SELECT 
                YEAR(tgl_produksi) AS year,
                CONCAT('Week ', WEEK(tgl_produksi)) AS minggu,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' THEN sample_number END) AS jml_mral,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'OnTime' AND tat_mral IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'Late' AND tat_mral IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) IS NULL THEN '00:00:00'
                    ELSE 
                        LPAD(FLOOR(AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) / 3600), 2, '0') || ':' ||  -- Hours
                        LPAD(FLOOR((AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) % 3600) / 60), 2, '0') || ':' ||  -- Minutes
                        LPAD(AVG(TIMESTAMPDIFF(SECOND, delivery, release_mral)) % 60, 2, '0')  -- Seconds
                END AS average_time,
                '03:00:00' AS time_limit
            FROM laboratory_performance_tat
            WHERE 
                mral_order='Yes'
                AND tgl_produksi >= DATE_SUB(CURDATE(), INTERVAL {jml_week} WEEK)
            GROUP BY YEAR(tgl_produksi), WEEK(tgl_produksi)
            ORDER BY minggu ASC
        """

    elif db_vendor in ['mssql', 'microsoft']:
        sql_query = f"""
            SELECT 
                YEAR(tgl_produksi) AS year,
                CONCAT('Week ', DATEPART(WEEK, tgl_produksi)) AS minggu,
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
            WHERE 
                mral_order='Yes'
                AND tgl_produksi >= DATEADD(WEEK, -{jml_week}, GETDATE())
            GROUP BY YEAR(tgl_produksi), DATEPART(WEEK, tgl_produksi)
            ORDER BY minggu ASC
        """

    elif db_vendor == 'postgresql':
        sql_query = f"""
            SELECT 
                EXTRACT(YEAR FROM tgl_produksi) AS year,
                'Week ' || EXTRACT(WEEK FROM tgl_produksi)::INT AS minggu,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' THEN sample_number END) AS jml_mral,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'OnTime' AND tat_mral IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND mral_remark = 'Late' AND tat_mral IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN mral_order = 'Yes' AND tat_mral IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(EXTRACT(EPOCH FROM (release_mral - delivery))) IS NULL THEN '00:00:00'
                    ELSE TO_CHAR(
                        TO_TIMESTAMP(AVG(EXTRACT(EPOCH FROM (release_mral - delivery))))::TIME,
                        'HH24:MI:SS'
                    )
                END AS average_time,
                '03:00:00' AS time_limit
            FROM laboratory_performance_tat
            WHERE 
                mral_order = 'Yes'
                AND tgl_produksi >= CURRENT_DATE - INTERVAL '{jml_week} weeks'
            GROUP BY year, minggu
            ORDER BY minggu ASC
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
def getRoaGroupWeeks(request):
    jml_week = request.GET.get('jml_week')

    if not jml_week:
        jml_week = 5
    else:
        jml_week = int(jml_week)

    if db_vendor == 'mysql':
        sql_query = f"""
            SELECT
                YEAR(tgl_produksi) AS year,
                CONCAT('Week ', WEEK(tgl_produksi)) AS minggu,
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
                '105:00:00' AS time_limit,
                120 AS time_limit_hours
            FROM laboratory_performance_tat
            WHERE roa_order = 'Yes'
            AND tgl_produksi >= DATE_SUB(CURDATE(), INTERVAL {jml_week} WEEK)
            GROUP BY YEAR(tgl_produksi), WEEK(tgl_produksi)
            ORDER BY minggu ASC
        """

    elif db_vendor in ['mssql', 'microsoft']:
        sql_query = f"""
            SELECT
                YEAR(tgl_produksi) AS year,
                CONCAT('Week ', DATEPART(WEEK, tgl_produksi)) AS minggu,
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
                '105:00:00' AS time_limit,
                120 AS time_limit_hours
            FROM laboratory_performance_tat
            WHERE roa_order = 'Yes'
            AND tgl_produksi >= DATEADD(WEEK, -{jml_week}, GETDATE())
            GROUP BY YEAR(tgl_produksi), DATEPART(WEEK, tgl_produksi)
            ORDER BY minggu ASC
        """

    elif db_vendor == 'postgresql':
        sql_query = f"""
            SELECT 
                EXTRACT(YEAR FROM tgl_produksi) AS year,
                'Week ' || EXTRACT(WEEK FROM tgl_produksi)::INT AS minggu,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' THEN sample_number END) AS jml_roa,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'OnTime' AND tat_roa IS NOT NULL THEN sample_number END) AS released_on_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND roa_remark = 'Late' AND tat_roa IS NOT NULL THEN sample_number END) AS released_over_tat,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NOT NULL THEN sample_number END) AS total_released,
                COUNT(DISTINCT CASE WHEN roa_order = 'Yes' AND tat_roa IS NULL THEN sample_number END) AS not_released,
                CASE
                    WHEN AVG(EXTRACT(EPOCH FROM (release_roa - delivery))) IS NULL THEN '00:00:00'
                    ELSE TO_CHAR(
                        TO_TIMESTAMP(AVG(EXTRACT(EPOCH FROM (release_roa - delivery))))::TIME,
                        'HH24:MI:SS'
                    )
                END AS average_time,
                '105:00:00' AS time_limit,
                120 AS time_limit_hours
            FROM laboratory_performance_tat
            WHERE roa_order = 'Yes'
            AND tgl_produksi >= CURRENT_DATE - INTERVAL '{jml_week} weeks'
            GROUP BY year, minggu
            ORDER BY minggu ASC
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

