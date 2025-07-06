from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio
pio.templates
from datetime import datetime, timedelta
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import connections
from kqms.utils.db_utils import get_db_vendor

# Deteksi vendor database
db_vendor = get_db_vendor('kqms_db')

@login_required 
def analyseMralRoaPage(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())

    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
        
    }
    # form = DateFilterForm(request.GET or None)
    return render(request, 'admin-mgoqa/report-qa/list-analyse-mral-roa.html',context)

@login_required
def analyseMralRoaChartPage(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())

    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
    }
    # form = DateFilterForm(request.GET or None)
    return render(request, 'admin-mgoqa/report-qa/chart-analyse-mral-roa.html',context)


# For Plotly Chart
@login_required
def plotly_wet_year(request):
    filter_year = request.GET.get('filter_year')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend
    # Gunakan tahun sekarang jika filter_year tidak dipilih
    if not filter_year:
        filter_year = datetime.now().year

    # Pastikan filter_year berupa integer
    if not filter_year:
        filter_year = datetime.now().year
    filter_year = int(filter_year)


    # Deteksi vendor database
    if db_vendor == 'postgresql':
        year_expr = "EXTRACT(YEAR FROM tgl_deliver)"
        round_avg = lambda col: f"ROUND(AVG({col})::numeric, 3)"
    elif db_vendor in ['mysql', 'mariadb', 'microsoft', 'sqlserver', 'mssql']:
        year_expr = "YEAR(tgl_deliver)"
        round_avg = lambda col: f"ROUND(AVG({col}), 3)"
    else:
        raise ValueError("Unsupported database vendor.")

    # Buat query SQL
    query = f"""
        SELECT
            -- Ni
            COUNT(CASE WHEN ni_roa IS NOT NULL THEN 1 END) AS jlm_ni,
            COUNT(CASE WHEN ni_error = '0' AND ni_roa IS NOT NULL THEN 1 END) AS error_ni,
            COUNT(CASE WHEN ni_error = '1' AND ni_roa IS NOT NULL THEN 1 END) AS good_ni,
            {round_avg('ni_roa')} AS avg_ni,

            -- Co
            COUNT(CASE WHEN co_roa IS NOT NULL THEN 1 END) AS jlm_co,
            COUNT(CASE WHEN co_error = '0' AND co_roa IS NOT NULL THEN 1 END) AS error_co,
            COUNT(CASE WHEN co_error = '1' AND co_roa IS NOT NULL THEN 1 END) AS good_co,
            {round_avg('co_roa')} AS avg_co,

            -- Fe
            COUNT(CASE WHEN fe_roa IS NOT NULL THEN 1 END) AS jlm_fe,
            COUNT(CASE WHEN fe_error = '0' AND fe_roa IS NOT NULL THEN 1 END) AS error_fe,
            COUNT(CASE WHEN fe_error = '1' AND fe_roa IS NOT NULL THEN 1 END) AS good_fe,
            {round_avg('fe_roa')} AS avg_fe,

            -- MgO
            COUNT(CASE WHEN mgo_roa IS NOT NULL THEN 1 END) AS jlm_mgo,
            COUNT(CASE WHEN mgo_error = '0' AND mgo_roa IS NOT NULL THEN 1 END) AS error_mgo,
            COUNT(CASE WHEN mgo_error = '1' AND mgo_roa IS NOT NULL THEN 1 END) AS good_mgo,
            {round_avg('mgo_roa')} AS avg_mgo,

            -- SiO2
            COUNT(CASE WHEN sio2_roa IS NOT NULL THEN 1 END) AS jlm_sio2,
            COUNT(CASE WHEN sio2_error = '0' AND sio2_roa IS NOT NULL THEN 1 END) AS error_sio2,
            COUNT(CASE WHEN sio2_error = '1' AND sio2_roa IS NOT NULL THEN 1 END) AS good_sio2,
            {round_avg('sio2_roa')} AS avg_sio2

        FROM mral_roa_analyse
        WHERE {year_expr} = %s
    """

    # Eksekusi dengan parameter tahun
    df = pd.read_sql_query(query, connections['kqms_db'], params=(filter_year,))

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
                    "font": {"size": 20}
                }
            ],
            height=370,
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    # load data
    good_ni     = df['good_ni'][0]
    good_co     = df['good_co'][0]
    good_fe     = df['good_fe'][0]
    good_mgo    = df['good_mgo'][0]
    good_sio2   = df['good_sio2'][0]
    
    error_ni    = df['error_ni'][0]
    error_co    = df['error_co'][0]
    error_fe    = df['error_fe'][0]
    error_mgo   = df['error_mgo'][0]
    error_sio2  = df['error_sio2'][0]

    
    # Menambahkan garis untuk Centre Line
    top_labels = ['Acceptable Sample', 'Error Sample',]
    colors = ['rgba(68, 138, 255, 0.8)', 'rgba(130, 177, 255, 0.6)']


    x_data = [
                [good_sio2, good_mgo, good_fe, good_co, good_ni],
                [error_sio2, error_mgo, error_fe, error_co, error_ni]
            ]

    y_data = ['SiO2', 'MgO', 'Fe', 'Co', 'Ni']
    
    fig = go.Figure()
    
    for i in range(len(x_data)):
        fig.add_trace(go.Bar(
            x=x_data[i], 
            y=y_data,
            orientation='h',
            marker=dict(
                color=colors[i],
                line=dict(color='rgb(248, 248, 249)', width=1)
            ),
            name=top_labels[i]
        ))

    annotations = []

    for yd, good, error in zip(y_data, x_data[0], x_data[1]):
        total = good + error
        good_percentage = (good / total) * 100 if total > 0 else 0
        error_percentage = (error / total) * 100 if total > 0 else 0

        annotations.append(dict(xref='x', yref='y', x=good/2, y=yd,
                                text=f'{good_percentage:.0f}%',
                                font=dict(family='Arial', size=12,
                                          color='rgb(248, 248, 255)'),
                                showarrow=False))
        annotations.append(dict(xref='x', yref='y', x=good + error/2, y=yd,
                                text=f'{error_percentage:.0f}%',
                                font=dict(family='Arial', size=12,
                                          color='rgb(248, 248, 255)'),
                                showarrow=False))
        
    fig.update_layout(
        title=f'Wet analyse of year ({filter_year})',
        title_font=dict(size=19),
        template="plotly_dark" if theme == "dark" else "plotly_white", 
        #margin=dict(l=45, r=20, t=90, b=80),
        title_x=0.5,
        barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=annotations,
        showlegend=True,
        legend=dict(
                orientation='h',
                y=1.0,
                x=0.5,
                xanchor='center',
                yanchor='bottom',
                traceorder='normal'
                ),
         height=370,        
    )
   

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True
})
    return JsonResponse({'plot_div': plot_div})

@login_required
def plotly_wet_month(request):
  # Mendapatkan nilai filter dari request
    filter_year  = request.GET.get('filter_year')
    filter_month = request.GET.get('filter_month')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend
    # Gunakan tahun & bulan sekarang jika filter_year & filter_month tidak dipilih
    if not filter_year:
        filter_year = datetime.now().year
    if not filter_month:
        filter_month = datetime.now().month

    # Pastikan integer (wajib untuk PostgreSQL, MySQL, SQL Server)
    filter_year = int(filter_year)
    filter_month = int(filter_month)

    # Tentukan ekspresi YEAR & MONTH tergantung vendor DB
    if db_vendor == 'postgresql':
        year_expr = "EXTRACT(YEAR FROM tgl_deliver)"
        month_expr = "EXTRACT(MONTH FROM tgl_deliver)"
        round_avg = lambda col: f"ROUND(AVG({col})::numeric, 3)"
    elif db_vendor in ['mysql', 'mariadb', 'sqlserver', 'mssql', 'microsoft']:
        year_expr = "YEAR(tgl_deliver)"
        month_expr = "MONTH(tgl_deliver)"
        round_avg = lambda col: f"ROUND(AVG({col}), 3)"
    else:
        raise ValueError("Unsupported database vendor")

    # Query SQL
    query = f"""
        SELECT
            COUNT(CASE WHEN ni_roa IS NOT NULL THEN 1 END) AS jlm_ni,
            COUNT(CASE WHEN ni_error = '0' AND ni_roa IS NOT NULL THEN 1 END) AS error_ni,
            COUNT(CASE WHEN ni_error = '1' AND ni_roa IS NOT NULL THEN 1 END) AS good_ni,
            {round_avg('ni_roa')} AS avg_ni,

            COUNT(CASE WHEN co_roa IS NOT NULL THEN 1 END) AS jlm_co,
            COUNT(CASE WHEN co_error = '0' AND co_roa IS NOT NULL THEN 1 END) AS error_co,
            COUNT(CASE WHEN co_error = '1' AND co_roa IS NOT NULL THEN 1 END) AS good_co,
            {round_avg('co_roa')} AS avg_co,

            COUNT(CASE WHEN fe_roa IS NOT NULL THEN 1 END) AS jlm_fe,
            COUNT(CASE WHEN fe_error = '0' AND fe_roa IS NOT NULL THEN 1 END) AS error_fe,
            COUNT(CASE WHEN fe_error = '1' AND fe_roa IS NOT NULL THEN 1 END) AS good_fe,
            {round_avg('fe_roa')} AS avg_fe,

            COUNT(CASE WHEN mgo_roa IS NOT NULL THEN 1 END) AS jlm_mgo,
            COUNT(CASE WHEN mgo_error = '0' AND mgo_roa IS NOT NULL THEN 1 END) AS error_mgo,
            COUNT(CASE WHEN mgo_error = '1' AND mgo_roa IS NOT NULL THEN 1 END) AS good_mgo,
            {round_avg('mgo_roa')} AS avg_mgo,

            COUNT(CASE WHEN sio2_roa IS NOT NULL THEN 1 END) AS jlm_sio2,
            COUNT(CASE WHEN sio2_error = '0' AND sio2_roa IS NOT NULL THEN 1 END) AS error_sio2,
            COUNT(CASE WHEN sio2_error = '1' AND sio2_roa IS NOT NULL THEN 1 END) AS good_sio2,
            {round_avg('sio2_roa')} AS avg_sio2

        FROM mral_roa_analyse
        WHERE {year_expr} = %s AND {month_expr} = %s
    """

    # Eksekusi query
    params = (filter_year, filter_month)
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)

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
                    "font": {"size": 16}
                }
            ],
            height=370,
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    # load data
    good_ni     = df['good_ni'][0]
    good_co     = df['good_co'][0]
    good_fe     = df['good_fe'][0]
    good_mgo    = df['good_mgo'][0]
    good_sio2   = df['good_sio2'][0]
    
    error_ni    = df['error_ni'][0]
    error_co    = df['error_co'][0]
    error_fe    = df['error_fe'][0]
    error_mgo   = df['error_mgo'][0]
    error_sio2  = df['error_sio2'][0]

    
    # Menambahkan garis untuk Centre Line
    top_labels = ['Acceptable Sample', 'Error Sample',]
    colors     = ['rgba(96, 207, 158, 0.8)', 'rgba(170, 229, 203, 0.7)']

    x_data = [
                [good_sio2, good_mgo, good_fe, good_co, good_ni],
                [error_sio2, error_mgo, error_fe, error_co, error_ni]
            ]

    y_data = ['SiO2', 'MgO', 'Fe', 'Co', 'Ni']

    fig = go.Figure()
    
    for i in range(len(x_data)):
        fig.add_trace(go.Bar(
            x=x_data[i], 
            y=y_data,
            orientation='h',
            marker=dict(
                color=colors[i],
                line=dict(color='rgb(248, 248, 249)', width=1)
            ),
            name=top_labels[i]
        ))

    annotations = []

    for yd, good, error in zip(y_data, x_data[0], x_data[1]):
        total = good + error
        good_percentage = (good / total) * 100 if total > 0 else 0
        error_percentage = (error / total) * 100 if total > 0 else 0

        annotations.append(dict(xref='x', yref='y', x=good/2, y=yd,
                                text=f'{good_percentage:.0f}%',
                                font=dict(family='Arial', size=12,
                                          color='rgb(248, 248, 255)'),
                                showarrow=False))
        annotations.append(dict(xref='x', yref='y', x=good + error/2, y=yd,
                                text=f'{error_percentage:.0f}%',
                                font=dict(family='Arial', size=12,
                                          color='rgb(248, 248, 255)'),
                                showarrow=False))
        
    # Get month name for title
    # month_name = get_month_name(filter_month)   
    
    fig.update_layout(
        title=f'Wet analyse of month, {filter_month}-{filter_year}',  # Dynamic title with filter_month
        title_font=dict(size=19),
        template="plotly_dark" if theme == "dark" else "plotly_white", 
        #margin=dict(l=45, r=20, t=90, b=80),
        title_x=0.5,
        barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=annotations,
        showlegend=True,
        legend=dict(
                orientation='h',  
                y=1.0,          
                x=0.5,
                xanchor='center',
                yanchor='bottom',
                traceorder='normal'
                ),
        height=370,        
    )

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True
})
    return JsonResponse({'plot_div': plot_div})

@login_required
def plotly_wet_weekly(request):
  # Mendapatkan nilai filter dari request
    startDate  = request.GET.get('startDate')
    endDate = request.GET.get('endDate')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend

    # Tentukan fungsi ROUND sesuai database
    if db_vendor == 'postgresql':
        round_avg = lambda expr: f"ROUND(AVG({expr})::numeric, 3)"
    elif db_vendor in ['mysql', 'mariadb', 'sqlserver', 'mssql', 'microsoft']:
        round_avg = lambda expr: f"ROUND(AVG({expr}), 3)"
    else:
        raise ValueError("Unsupported database vendor")
    # Query dengan parameterisasi untuk keamanan
    query = f"""
            SELECT
                -- Ni
                COUNT(CASE WHEN ni_roa IS NOT NULL THEN 1 END) AS jlm_ni,
                COUNT(CASE WHEN ni_error = '0' AND ni_roa IS NOT NULL THEN 1 END) AS error_ni,
                COUNT(CASE WHEN ni_error = '1' AND ni_roa IS NOT NULL THEN 1 END) AS good_ni,
                {round_avg('ni_roa')} AS avg_ni,

                -- Co
                COUNT(CASE WHEN co_roa IS NOT NULL THEN 1 END) AS jlm_co,
                COUNT(CASE WHEN co_error = '0' AND co_roa IS NOT NULL THEN 1 END) AS error_co,
                COUNT(CASE WHEN co_error = '1' AND co_roa IS NOT NULL THEN 1 END) AS good_co,
                {round_avg('co_roa')} AS avg_co,

                -- Fe
                COUNT(CASE WHEN fe_roa IS NOT NULL THEN 1 END) AS jlm_fe,
                COUNT(CASE WHEN fe_error = '0' AND fe_roa IS NOT NULL THEN 1 END) AS error_fe,
                COUNT(CASE WHEN fe_error = '1' AND fe_roa IS NOT NULL THEN 1 END) AS good_fe,
                {round_avg('fe_roa')} AS avg_fe,

                -- MgO
                COUNT(CASE WHEN mgo_roa IS NOT NULL THEN 1 END) AS jlm_mgo,
                COUNT(CASE WHEN mgo_error = '0' AND mgo_roa IS NOT NULL THEN 1 END) AS error_mgo,
                COUNT(CASE WHEN mgo_error = '1' AND mgo_roa IS NOT NULL THEN 1 END) AS good_mgo,
                {round_avg('mgo_roa')} AS avg_mgo,

                -- SiO2
                COUNT(CASE WHEN sio2_roa IS NOT NULL THEN 1 END) AS jlm_sio2,
                COUNT(CASE WHEN sio2_error = '0' AND sio2_roa IS NOT NULL THEN 1 END) AS error_sio2,
                COUNT(CASE WHEN sio2_error = '1' AND sio2_roa IS NOT NULL THEN 1 END) AS good_sio2,
                {round_avg('sio2_roa')} AS avg_sio2

            FROM mral_roa_analyse
            WHERE tgl_deliver BETWEEN %s AND %s
        """

    params = (startDate, endDate)
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)

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
                    "font": {"size": 16}
                }
            ],
            height=370,
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    # load data
    good_ni     = df['good_ni'][0]
    good_co     = df['good_co'][0]
    good_fe     = df['good_fe'][0]
    good_mgo    = df['good_mgo'][0]
    good_sio2   = df['good_sio2'][0]
    
    error_ni    = df['error_ni'][0]
    error_co    = df['error_co'][0]
    error_fe    = df['error_fe'][0]
    error_mgo   = df['error_mgo'][0]
    error_sio2  = df['error_sio2'][0]

    
    # Menambahkan garis untuk Centre Line
    top_labels = ['Acceptable Sample', 'Error Sample',]
    colors     = ['rgba(254, 176, 25, 0.8)', 'rgba(253, 218, 154, 0.7)']

    x_data = [
                [good_sio2, good_mgo, good_fe, good_co, good_ni],
                [error_sio2, error_mgo, error_fe, error_co, error_ni]
            ]

    y_data = ['SiO2', 'MgO', 'Fe', 'Co', 'Ni']

    fig = go.Figure()
    
    for i in range(len(x_data)):
        fig.add_trace(go.Bar(
            x=x_data[i], 
            y=y_data,
            orientation='h',
            marker=dict(
                color=colors[i],
                line=dict(color='rgb(248, 248, 249)', width=1)
            ),
            name=top_labels[i]
        ))

    annotations = []

    for yd, good, error in zip(y_data, x_data[0], x_data[1]):
        total = good + error
        good_percentage = (good / total) * 100 if total > 0 else 0
        error_percentage = (error / total) * 100 if total > 0 else 0

        annotations.append(dict(xref='x', yref='y', x=good/2, y=yd,
                                text=f'{good_percentage:.0f}%',
                                font=dict(family='Arial', size=12,
                                          color='rgb(248, 248, 255)'),
                                showarrow=False))
        annotations.append(dict(xref='x', yref='y', x=good + error/2, y=yd,
                                text=f'{error_percentage:.0f}%',
                                font=dict(family='Arial', size=12,
                                          color='rgb(248, 248, 255)'),
                                showarrow=False))
        
    # Get month name for title
    # month_name = get_month_name(filter_month)   
    
    fig.update_layout(
        title=f'Wet analyse of, {startDate}-{endDate}',  # Dynamic title with filter_month
        title_font=dict(size=19),
        template="plotly_dark" if theme == "dark" else "plotly_white", 
        # margin=dict(l=10, r=20, t=90, b=80),
        title_x=0.5,
        barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=annotations,
        showlegend=True,
        legend=dict(
                orientation='h',  
                y=1.0,          
                x=0.5,
                xanchor='center',
                yanchor='bottom',
                traceorder='normal'
                ),
        height=350,        
    )

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True
})
    return JsonResponse({'plot_div': plot_div})

# For Apex Chart
@login_required
def yearDataAnalyse(request):
    # Mendapatkan nilai filter dari request
    filter_year  = request.GET.get('filter_year')

    # Gunakan tahun & bulan sekarang jika filter_year & filter_month tidak dipilih
    if not filter_year:
        filter_year = datetime.now().year

    filter_year = int(filter_year)

    # Deteksi vendor database
    if db_vendor == 'postgresql':
        year_expr = "EXTRACT(YEAR FROM tgl_deliver)"
        round_avg = lambda col: f"ROUND(AVG({col})::numeric, 3)"
    elif db_vendor in ['mysql', 'mariadb', 'microsoft', 'sqlserver', 'mssql']:
        year_expr = "YEAR(tgl_deliver)"
        round_avg = lambda col: f"ROUND(AVG({col}), 3)"
    else:
        raise ValueError("Unsupported database vendor.")

    # Buat query SQL
    query = f"""
        SELECT
            -- Ni
            COUNT(CASE WHEN ni_roa IS NOT NULL THEN 1 END) AS jlm_ni,
            COUNT(CASE WHEN ni_error = '0' AND ni_roa IS NOT NULL THEN 1 END) AS error_ni,
            COUNT(CASE WHEN ni_error = '1' AND ni_roa IS NOT NULL THEN 1 END) AS good_ni,
            {round_avg('ni_roa')} AS avg_ni,

            -- Co
            COUNT(CASE WHEN co_roa IS NOT NULL THEN 1 END) AS jlm_co,
            COUNT(CASE WHEN co_error = '0' AND co_roa IS NOT NULL THEN 1 END) AS error_co,
            COUNT(CASE WHEN co_error = '1' AND co_roa IS NOT NULL THEN 1 END) AS good_co,
            {round_avg('co_roa')} AS avg_co,

            -- Fe
            COUNT(CASE WHEN fe_roa IS NOT NULL THEN 1 END) AS jlm_fe,
            COUNT(CASE WHEN fe_error = '0' AND fe_roa IS NOT NULL THEN 1 END) AS error_fe,
            COUNT(CASE WHEN fe_error = '1' AND fe_roa IS NOT NULL THEN 1 END) AS good_fe,
            {round_avg('fe_roa')} AS avg_fe,

            -- MgO
            COUNT(CASE WHEN mgo_roa IS NOT NULL THEN 1 END) AS jlm_mgo,
            COUNT(CASE WHEN mgo_error = '0' AND mgo_roa IS NOT NULL THEN 1 END) AS error_mgo,
            COUNT(CASE WHEN mgo_error = '1' AND mgo_roa IS NOT NULL THEN 1 END) AS good_mgo,
            {round_avg('mgo_roa')} AS avg_mgo,

            -- SiO2
            COUNT(CASE WHEN sio2_roa IS NOT NULL THEN 1 END) AS jlm_sio2,
            COUNT(CASE WHEN sio2_error = '0' AND sio2_roa IS NOT NULL THEN 1 END) AS error_sio2,
            COUNT(CASE WHEN sio2_error = '1' AND sio2_roa IS NOT NULL THEN 1 END) AS good_sio2,
            {round_avg('sio2_roa')} AS avg_sio2

        FROM mral_roa_analyse
        WHERE {year_expr} = %s
    """

    # Eksekusi dengan parameter tahun
    df = pd.read_sql_query(query, connections['kqms_db'], params=(filter_year,))

    # Mencetak hasil DataFrame
    # print(df)

    # load data
    response_data = {
    'jlm_ni'    : int(df['jlm_ni'][0] or 0),
    'error_ni'  : int(df['error_ni'][0] or 0),
    'good_ni'   : int(df['good_ni'][0] or 0),
    'avg_ni'    : float(df['avg_ni'][0] or 0),

    'jlm_co'    : int(df['jlm_co'][0] or 0),
    'error_co'  : int(df['error_co'][0] or 0),
    'good_co'   : int(df['good_co'][0] or 0),
    'avg_co'    : float(df['avg_co'][0] or 0),

    'jlm_fe'    : int(df['jlm_fe'][0] or 0),
    'error_fe'  : int(df['error_fe'][0] or 0),
    'good_fe'   : int(df['good_fe'][0] or 0),
    'avg_fe'    : float(df['avg_fe'][0] or 0),

    'jlm_mgo'   : int(df['jlm_mgo'][0] or 0),
    'error_mgo' : int(df['error_mgo'][0] or 0),
    'good_mgo'  : int(df['good_mgo'][0] or 0),
    'avg_mgo'   : float(df['avg_mgo'][0] or 0),

    'jlm_sio2'  : int(df['jlm_sio2'][0] or 0),
    'error_sio2': int(df['error_sio2'][0] or 0),
    'good_sio2' : int(df['good_sio2'][0] or 0),
    'avg_sio2'  : float(df['avg_sio2'][0] or 0),
}


    return JsonResponse(response_data)

@login_required
def monthDataAnalyse(request):
    # Mendapatkan nilai filter dari request
    filter_year  = request.GET.get('filter_year')
    filter_month = request.GET.get('filter_month')

    # Gunakan tahun & bulan sekarang jika filter_year & filter_month tidak dipilih
    if not filter_year:
        filter_year = datetime.now().year
    if not filter_month:
        filter_month = datetime.now().month

    # Pastikan integer (wajib untuk PostgreSQL, MySQL, SQL Server)
    filter_year = int(filter_year)
    filter_month = int(filter_month)

    # Tentukan ekspresi YEAR & MONTH tergantung vendor DB
    if db_vendor == 'postgresql':
        year_expr = "EXTRACT(YEAR FROM tgl_deliver)"
        month_expr = "EXTRACT(MONTH FROM tgl_deliver)"
        round_avg = lambda col: f"ROUND(AVG({col})::numeric, 3)"
    elif db_vendor in ['mysql', 'mariadb', 'sqlserver', 'mssql', 'microsoft']:
        year_expr = "YEAR(tgl_deliver)"
        month_expr = "MONTH(tgl_deliver)"
        round_avg = lambda col: f"ROUND(AVG({col}), 3)"
    else:
        raise ValueError("Unsupported database vendor")

    # Query SQL
    query = f"""
        SELECT
            COUNT(CASE WHEN ni_roa IS NOT NULL THEN 1 END) AS jlm_ni,
            COUNT(CASE WHEN ni_error = '0' AND ni_roa IS NOT NULL THEN 1 END) AS error_ni,
            COUNT(CASE WHEN ni_error = '1' AND ni_roa IS NOT NULL THEN 1 END) AS good_ni,
            {round_avg('ni_roa')} AS avg_ni,

            COUNT(CASE WHEN co_roa IS NOT NULL THEN 1 END) AS jlm_co,
            COUNT(CASE WHEN co_error = '0' AND co_roa IS NOT NULL THEN 1 END) AS error_co,
            COUNT(CASE WHEN co_error = '1' AND co_roa IS NOT NULL THEN 1 END) AS good_co,
            {round_avg('co_roa')} AS avg_co,

            COUNT(CASE WHEN fe_roa IS NOT NULL THEN 1 END) AS jlm_fe,
            COUNT(CASE WHEN fe_error = '0' AND fe_roa IS NOT NULL THEN 1 END) AS error_fe,
            COUNT(CASE WHEN fe_error = '1' AND fe_roa IS NOT NULL THEN 1 END) AS good_fe,
            {round_avg('fe_roa')} AS avg_fe,

            COUNT(CASE WHEN mgo_roa IS NOT NULL THEN 1 END) AS jlm_mgo,
            COUNT(CASE WHEN mgo_error = '0' AND mgo_roa IS NOT NULL THEN 1 END) AS error_mgo,
            COUNT(CASE WHEN mgo_error = '1' AND mgo_roa IS NOT NULL THEN 1 END) AS good_mgo,
            {round_avg('mgo_roa')} AS avg_mgo,

            COUNT(CASE WHEN sio2_roa IS NOT NULL THEN 1 END) AS jlm_sio2,
            COUNT(CASE WHEN sio2_error = '0' AND sio2_roa IS NOT NULL THEN 1 END) AS error_sio2,
            COUNT(CASE WHEN sio2_error = '1' AND sio2_roa IS NOT NULL THEN 1 END) AS good_sio2,
            {round_avg('sio2_roa')} AS avg_sio2

        FROM mral_roa_analyse
        WHERE {year_expr} = %s AND {month_expr} = %s
    """

    # Eksekusi query
    params = (filter_year, filter_month)
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)


     # load data
  
    response_data = {
        #  TypeError: float() argument must be a string or a real number
        
        'jlm_ni'    : int(df['jlm_ni'][0]) if df['jlm_ni'][0] is not None else 0,
        'error_ni'  : int(df['error_ni'][0]) if df['error_ni'][0] is not None else 0,
        'good_ni'   : int(df['good_ni'][0]) if df['good_ni'][0] is not None else 0,
        'avg_ni'    : float(df['avg_ni'][0]) if df['avg_ni'][0] is not None else 0.0,

        'jlm_co'    : int(df['jlm_co'][0]) if df['jlm_co'][0] is not None else 0,
        'error_co'  : int(df['error_co'][0]) if df['error_co'][0] is not None else 0,
        'good_co'   : int(df['good_co'][0]) if df['good_co'][0] is not None else 0,
        'avg_co'    : float(df['avg_co'][0]) if df['avg_co'][0] is not None else 0.0,

        'jlm_fe'    : int(df['jlm_fe'][0]) if df['jlm_fe'][0] is not None else 0,
        'error_fe'  : int(df['error_fe'][0]) if df['error_fe'][0] is not None else 0,
        'good_fe'   : int(df['good_fe'][0]) if df['good_fe'][0] is not None else 0,
        'avg_fe'    : float(df['avg_fe'][0]) if df['avg_fe'][0] is not None else 0.0,

        'jlm_mgo'   : int(df['jlm_mgo'][0]) if df['jlm_mgo'][0] is not None else 0,
        'error_mgo' : int(df['error_mgo'][0]) if df['error_mgo'][0] is not None else 0,
        'good_mgo'  : int(df['good_mgo'][0]) if df['good_mgo'][0] is not None else 0,
        'avg_mgo'   : float(df['avg_mgo'][0]) if df['avg_mgo'][0] is not None else 0.0,

        'jlm_sio2'  : int(df['jlm_sio2'][0]) if df['jlm_sio2'][0] is not None else 0,
        'error_sio2': int(df['error_sio2'][0]) if df['error_sio2'][0] is not None else 0,
        'good_sio2' : int(df['good_sio2'][0]) if df['good_sio2'][0] is not None else 0,
        'avg_sio2'  : float(df['avg_sio2'][0]) if df['avg_sio2'][0] is not None else 0.0,
    }


    return JsonResponse(response_data)

@login_required    
def weekDataAnalyse(request):

    # Mendapatkan nilai filter dari request
    startDate  = request.GET.get('startDate')
    endDate = request.GET.get('endDate')

     # Tentukan fungsi ROUND sesuai database
    if db_vendor == 'postgresql':
        round_avg = lambda expr: f"ROUND(AVG({expr})::numeric, 3)"
    elif db_vendor in ['mysql', 'mariadb', 'sqlserver', 'mssql', 'microsoft']:
        round_avg = lambda expr: f"ROUND(AVG({expr}), 3)"
    else:
        raise ValueError("Unsupported database vendor")
    # Query dengan parameterisasi untuk keamanan
    query = f"""
            SELECT
                -- Ni
                COUNT(CASE WHEN ni_roa IS NOT NULL THEN 1 END) AS jlm_ni,
                COUNT(CASE WHEN ni_error = '0' AND ni_roa IS NOT NULL THEN 1 END) AS error_ni,
                COUNT(CASE WHEN ni_error = '1' AND ni_roa IS NOT NULL THEN 1 END) AS good_ni,
                {round_avg('ni_roa')} AS avg_ni,

                -- Co
                COUNT(CASE WHEN co_roa IS NOT NULL THEN 1 END) AS jlm_co,
                COUNT(CASE WHEN co_error = '0' AND co_roa IS NOT NULL THEN 1 END) AS error_co,
                COUNT(CASE WHEN co_error = '1' AND co_roa IS NOT NULL THEN 1 END) AS good_co,
                {round_avg('co_roa')} AS avg_co,

                -- Fe
                COUNT(CASE WHEN fe_roa IS NOT NULL THEN 1 END) AS jlm_fe,
                COUNT(CASE WHEN fe_error = '0' AND fe_roa IS NOT NULL THEN 1 END) AS error_fe,
                COUNT(CASE WHEN fe_error = '1' AND fe_roa IS NOT NULL THEN 1 END) AS good_fe,
                {round_avg('fe_roa')} AS avg_fe,

                -- MgO
                COUNT(CASE WHEN mgo_roa IS NOT NULL THEN 1 END) AS jlm_mgo,
                COUNT(CASE WHEN mgo_error = '0' AND mgo_roa IS NOT NULL THEN 1 END) AS error_mgo,
                COUNT(CASE WHEN mgo_error = '1' AND mgo_roa IS NOT NULL THEN 1 END) AS good_mgo,
                {round_avg('mgo_roa')} AS avg_mgo,

                -- SiO2
                COUNT(CASE WHEN sio2_roa IS NOT NULL THEN 1 END) AS jlm_sio2,
                COUNT(CASE WHEN sio2_error = '0' AND sio2_roa IS NOT NULL THEN 1 END) AS error_sio2,
                COUNT(CASE WHEN sio2_error = '1' AND sio2_roa IS NOT NULL THEN 1 END) AS good_sio2,
                {round_avg('sio2_roa')} AS avg_sio2

            FROM mral_roa_analyse
            WHERE tgl_deliver BETWEEN %s AND %s
        """

    params = (startDate, endDate)
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)


     # load data
  
    response_data = {
        #  TypeError: float() argument must be a string or a real number
        
        'jlm_ni'    : int(df['jlm_ni'][0]) if df['jlm_ni'][0] is not None else 0,
        'error_ni'  : int(df['error_ni'][0]) if df['error_ni'][0] is not None else 0,
        'good_ni'   : int(df['good_ni'][0]) if df['good_ni'][0] is not None else 0,
        'avg_ni'    : float(df['avg_ni'][0]) if df['avg_ni'][0] is not None else 0.0,

        'jlm_co'    : int(df['jlm_co'][0]) if df['jlm_co'][0] is not None else 0,
        'error_co'  : int(df['error_co'][0]) if df['error_co'][0] is not None else 0,
        'good_co'   : int(df['good_co'][0]) if df['good_co'][0] is not None else 0,
        'avg_co'    : float(df['avg_co'][0]) if df['avg_co'][0] is not None else 0.0,

        'jlm_fe'    : int(df['jlm_fe'][0]) if df['jlm_fe'][0] is not None else 0,
        'error_fe'  : int(df['error_fe'][0]) if df['error_fe'][0] is not None else 0,
        'good_fe'   : int(df['good_fe'][0]) if df['good_fe'][0] is not None else 0,
        'avg_fe'    : float(df['avg_fe'][0]) if df['avg_fe'][0] is not None else 0.0,

        'jlm_mgo'   : int(df['jlm_mgo'][0]) if df['jlm_mgo'][0] is not None else 0,
        'error_mgo' : int(df['error_mgo'][0]) if df['error_mgo'][0] is not None else 0,
        'good_mgo'  : int(df['good_mgo'][0]) if df['good_mgo'][0] is not None else 0,
        'avg_mgo'   : float(df['avg_mgo'][0]) if df['avg_mgo'][0] is not None else 0.0,

        'jlm_sio2'  : int(df['jlm_sio2'][0]) if df['jlm_sio2'][0] is not None else 0,
        'error_sio2': int(df['error_sio2'][0]) if df['error_sio2'][0] is not None else 0,
        'good_sio2' : int(df['good_sio2'][0]) if df['good_sio2'][0] is not None else 0,
        'avg_sio2'  : float(df['avg_sio2'][0]) if df['avg_sio2'][0] is not None else 0.0,
    }


    return JsonResponse(response_data)

#List Data Tables:
class getAnalyseData(View):
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
            SELECT * FROM mral_roa_analyse
        """
        params = []

        from_date = request.POST.get('from_date')
        to_date   = request.POST.get('to_date')

        # if from_date and to_date:
        sql_query += " WHERE release_date BETWEEN %s AND %s"
        params.extend([from_date, to_date])

        if search_value:
            sql_query += " AND (sample_id LIKE %s OR waybill_number LIKE %s)"
            params.extend([f"%{search_value}%", f"%{search_value}%"])

        if order_dir == 'desc':
            sql_query += f" ORDER BY {order_column_index} DESC"
        else:
            sql_query += f" ORDER BY {order_column_index} ASC"

        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(sql_query, params)
            columns     = [col[0] for col in cursor.description]
            sql_data    = [dict(zip(columns, row)) for row in cursor.fetchall()]

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
            'draw'           : draw,
            'recordsTotal'   : total_records,
            'recordsFiltered': total_records,
            'data'           : data,
            'start'          : start,
            'length'         : length,
            'totalPages'     : total_pages,
        }
