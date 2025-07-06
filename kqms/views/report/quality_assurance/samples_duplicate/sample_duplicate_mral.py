from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio
pio.templates
from datetime import datetime, timedelta
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import connections


@login_required
def sampleDuplicateWetMral(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())

    context = {
        'start_date'  : last_monday.strftime('%Y-%m-%d'),
        'end_date'    : today.strftime('%Y-%m-%d'),
    }
    # form = DateFilterForm(request.GET or None)
    return render(request, 'admin-mgoqa/report-qa/wet-duplicated-mral.html',context)

@login_required
def sampleDuplicateMral(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date': today.strftime('%Y-%m-%d'),
    }
    # form = DateFilterForm(request.GET or None)
    return render(request, 'admin-mgoqa/report-qa/list-samples-duplicated-mral.html',context)

# plotly | Graphing Libraries
@login_required
def chart_wet_year(request):
    filter_year = request.GET.get('filter_year')

    # Gunakan tahun sekarang jika filter_year tidak dipilih
    if not filter_year:
        filter_year = datetime.now().year

    query = f"""
            SELECT
            COUNT(CASE WHEN ni_ori IS NOT NULL THEN ni_ori END) AS jlm_ni,
            COUNT(CASE WHEN ni_error = 0 AND ni_ori IS NOT NULL THEN ni_ori END) AS error_ni,
            COUNT(CASE WHEN ni_error = 1 AND ni_ori IS NOT NULL THEN ni_ori END) AS good_ni,
            ROUND(AVG(CASE WHEN ni_diff IS NOT NULL THEN ni_diff END), 3) AS avg_ni,

            COUNT(CASE WHEN co_ori IS NOT NULL THEN co_ori END) AS jlm_co,
            COUNT(CASE WHEN co_error = 0 AND co_ori IS NOT NULL THEN co_ori END) AS error_co,
            COUNT(CASE WHEN co_error = 1 AND co_ori IS NOT NULL THEN co_ori END) AS good_co,
            ROUND(AVG(CASE WHEN co_diff IS NOT NULL THEN co_diff END), 3) AS avg_co,
            
            COUNT(CASE WHEN fe_ori IS NOT NULL THEN fe_ori END) AS jlm_fe,
            COUNT(CASE WHEN fe_error = 0 AND fe_ori IS NOT NULL THEN fe_ori END) AS error_fe,
            COUNT(CASE WHEN fe_error = 1 AND fe_ori IS NOT NULL THEN fe_ori END) AS good_fe,
            ROUND(AVG(CASE WHEN fe_diff IS NOT NULL THEN fe_diff END), 3) AS avg_fe,
            
            COUNT(CASE WHEN mgo_ori IS NOT NULL THEN mgo_ori END) AS jlm_mgo,
            COUNT(CASE WHEN mgo_error = 0 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS error_mgo,
            COUNT(CASE WHEN mgo_error = 1 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS good_mgo,
            ROUND(AVG(CASE WHEN mgo_diff IS NOT NULL THEN mgo_diff END), 3) AS avg_mgo,
                
            COUNT(CASE WHEN sio2_ori IS NOT NULL THEN sio2_ori END) AS jlm_sio2,
            COUNT(CASE WHEN sio2_error = 0 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS error_sio2,
            COUNT(CASE WHEN sio2_error = 1 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS good_sio2,
            ROUND(AVG(CASE WHEN sio2_diff IS NOT NULL THEN sio2_diff END), 3) AS avg_sio2
            
        FROM sample_duplicated_mral
        WHERE YEAR(release_date) = {filter_year}                                                    
    """

    # df = pd.read_sql_query(query, connection)
    df = pd.read_sql_query(query, connections['kqms_db'])

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(201,201,201,0.08)', 
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
    good_ni   = df['good_ni'][0]
    good_co   = df['good_co'][0]
    good_fe   = df['good_fe'][0]
    good_mgo  = df['good_mgo'][0]
    good_sio2 = df['good_sio2'][0]
    
    error_ni   = df['error_ni'][0]
    error_co   = df['error_co'][0]
    error_fe   = df['error_fe'][0]
    error_mgo  = df['error_mgo'][0]
    error_sio2 = df['error_sio2'][0]

    
    # Menambahkan garis untuk Centre Line
    top_labels  = ['Acceptable Sample', 'Error Sample',]
    colors      = ['rgba(0, 188, 212, 0.8)', 'rgba(0, 188, 212, 0.3)']
    
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
        title=f'Wet duplicated mral of year ({filter_year})',
        title_font=dict(size=19),
        margin=dict(l=25, r=20, t=90, b=80),
        title_x=0.5,
        barmode='stack',
        hovermode='closest',
        plot_bgcolor='rgba(201,201,201,0.08)',
        annotations=annotations,
        showlegend=True,
        legend=dict(
                orientation='h',
                y=1.0,          
                x=0.5,           
                xanchor  ='center', 
                yanchor   ='bottom',  
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
def chart_wet_month(request):
  # Mendapatkan nilai filter dari request
    filter_year = request.GET.get('filter_year')
    filter_month = request.GET.get('filter_month')

    # Gunakan tahun & bulan sekarang jika filter_year & filter_month tidak dipilih
    if not filter_year:
        filter_year = datetime.now().year

    if not filter_month:
        filter_month = datetime.now().month

    # Query dengan parameterisasi untuk keamanan
    query = """
        SELECT
            COUNT(CASE WHEN ni_ori IS NOT NULL THEN ni_ori END) AS jlm_ni,
            COUNT(CASE WHEN ni_error = 0 AND ni_ori IS NOT NULL THEN ni_ori END) AS error_ni,
            COUNT(CASE WHEN ni_error = 1 AND ni_ori IS NOT NULL THEN ni_ori END) AS good_ni,
            ROUND(AVG(CASE WHEN ni_diff IS NOT NULL THEN ni_diff END), 3) AS avg_ni,

            COUNT(CASE WHEN co_ori IS NOT NULL THEN co_ori END) AS jlm_co,
            COUNT(CASE WHEN co_error = 0 AND co_ori IS NOT NULL THEN co_ori END) AS error_co,
            COUNT(CASE WHEN co_error = 1 AND co_ori IS NOT NULL THEN co_ori END) AS good_co,
            ROUND(AVG(CASE WHEN co_diff IS NOT NULL THEN co_diff END), 3) AS avg_co,

            COUNT(CASE WHEN fe_ori IS NOT NULL THEN fe_ori END) AS jlm_fe,
            COUNT(CASE WHEN fe_error = 0 AND fe_ori IS NOT NULL THEN fe_ori END) AS error_fe,
            COUNT(CASE WHEN fe_error = 1 AND fe_ori IS NOT NULL THEN fe_ori END) AS good_fe,
            ROUND(AVG(CASE WHEN fe_diff IS NOT NULL THEN fe_diff END), 3) AS avg_fe,

            COUNT(CASE WHEN mgo_ori IS NOT NULL THEN mgo_ori END) AS jlm_mgo,
            COUNT(CASE WHEN mgo_error = 0 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS error_mgo,
            COUNT(CASE WHEN mgo_error = 1 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS good_mgo,
            ROUND(AVG(CASE WHEN mgo_diff IS NOT NULL THEN mgo_diff END), 3) AS avg_mgo,

            COUNT(CASE WHEN sio2_ori IS NOT NULL THEN sio2_ori END) AS jlm_sio2,
            COUNT(CASE WHEN sio2_error = 0 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS error_sio2,
            COUNT(CASE WHEN sio2_error = 1 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS good_sio2,
            ROUND(AVG(CASE WHEN sio2_diff IS NOT NULL THEN sio2_diff END), 3) AS avg_sio2

        FROM sample_duplicated_mral
        WHERE YEAR(release_date) = %s AND MONTH(release_date) = %s
    """

    params = (filter_year, filter_month)
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)


    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(201,201,201,0.08)', 
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
    colors     = ['rgba(254, 176, 25, 0.8)', 'rgba(254, 176, 25, 0.3)']
    
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
       title=f'Wet duplicated mral of month, {filter_month}-{filter_year}',
        title_font=dict(size=19),
        margin=dict(l=25, r=20, t=90, b=80),
        title_x=0.5,
        barmode='stack',
        plot_bgcolor='rgba(201,201,201,0.08)',
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
def chart_wet_week(request):
  # Mendapatkan nilai filter dari request
    startDate  = request.GET.get('startDate')
    endDate    = request.GET.get('endDate')

    # Query dengan parameterisasi untuk keamanan
    query = """
        SELECT
            COUNT(CASE WHEN ni_ori IS NOT NULL THEN ni_ori END) AS jlm_ni,
            COUNT(CASE WHEN ni_error = 0 AND ni_ori IS NOT NULL THEN ni_ori END) AS error_ni,
            COUNT(CASE WHEN ni_error = 1 AND ni_ori IS NOT NULL THEN ni_ori END) AS good_ni,
            ROUND(AVG(CASE WHEN ni_diff IS NOT NULL THEN ni_diff END), 3) AS avg_ni,

            COUNT(CASE WHEN co_ori IS NOT NULL THEN co_ori END) AS jlm_co,
            COUNT(CASE WHEN co_error = 0 AND co_ori IS NOT NULL THEN co_ori END) AS error_co,
            COUNT(CASE WHEN co_error = 1 AND co_ori IS NOT NULL THEN co_ori END) AS good_co,
            ROUND(AVG(CASE WHEN co_diff IS NOT NULL THEN co_diff END), 3) AS avg_co,

            COUNT(CASE WHEN fe_ori IS NOT NULL THEN fe_ori END) AS jlm_fe,
            COUNT(CASE WHEN fe_error = 0 AND fe_ori IS NOT NULL THEN fe_ori END) AS error_fe,
            COUNT(CASE WHEN fe_error = 1 AND fe_ori IS NOT NULL THEN fe_ori END) AS good_fe,
            ROUND(AVG(CASE WHEN fe_diff IS NOT NULL THEN fe_diff END), 3) AS avg_fe,

            COUNT(CASE WHEN mgo_ori IS NOT NULL THEN mgo_ori END) AS jlm_mgo,
            COUNT(CASE WHEN mgo_error = 0 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS error_mgo,
            COUNT(CASE WHEN mgo_error = 1 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS good_mgo,
            ROUND(AVG(CASE WHEN mgo_diff IS NOT NULL THEN mgo_diff END), 3) AS avg_mgo,

            COUNT(CASE WHEN sio2_ori IS NOT NULL THEN sio2_ori END) AS jlm_sio2,
            COUNT(CASE WHEN sio2_error = 0 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS error_sio2,
            COUNT(CASE WHEN sio2_error = 1 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS good_sio2,
            ROUND(AVG(CASE WHEN sio2_diff IS NOT NULL THEN sio2_diff END), 3) AS avg_sio2

        FROM sample_duplicated_mral
        WHERE release_date >= %s AND release_date <= %s
    """

    params = (startDate, endDate)
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)


    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(201,201,201,0.08)', 
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
    colors     = ['rgba(255, 82, 82, 0.8)', 'rgba(255, 82, 82, 0.3)']
    
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
        title=f'Wet duplicated mral, {startDate} to {endDate}',
        title_font=dict(size=19),
        margin=dict(l=25, r=20, t=90, b=80),
        title_x=0.5,
        barmode='stack',
        plot_bgcolor='rgba(201,201,201,0.08)',
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

# For Apex Chart
@login_required
def wetYearDataMral(request):

    # Mendapatkan nilai filter dari request
    filter_year  = request.GET.get('filter_year')

    # Gunakan tahun & bulan sekarang jika filter_year & filter_month tidak dipilih
    if not filter_year:
        filter_year = datetime.now().year


    # Query dengan parameterisasi untuk keamanan
    query = """
        SELECT
            COUNT(CASE WHEN ni_ori IS NOT NULL THEN ni_ori END) AS jlm_ni,
            COUNT(CASE WHEN ni_error = 0 AND ni_ori IS NOT NULL THEN ni_ori END) AS error_ni,
            COUNT(CASE WHEN ni_error = 1 AND ni_ori IS NOT NULL THEN ni_ori END) AS good_ni,
            ROUND(AVG(CASE WHEN ni_diff IS NOT NULL THEN ni_diff END), 3) AS avg_ni,

            COUNT(CASE WHEN co_ori IS NOT NULL THEN co_ori END) AS jlm_co,
            COUNT(CASE WHEN co_error = 0 AND co_ori IS NOT NULL THEN co_ori END) AS error_co,
            COUNT(CASE WHEN co_error = 1 AND co_ori IS NOT NULL THEN co_ori END) AS good_co,
            ROUND(AVG(CASE WHEN co_diff IS NOT NULL THEN co_diff END), 3) AS avg_co,

            COUNT(CASE WHEN fe_ori IS NOT NULL THEN fe_ori END) AS jlm_fe,
            COUNT(CASE WHEN fe_error = 0 AND fe_ori IS NOT NULL THEN fe_ori END) AS error_fe,
            COUNT(CASE WHEN fe_error = 1 AND fe_ori IS NOT NULL THEN fe_ori END) AS good_fe,
            ROUND(AVG(CASE WHEN fe_diff IS NOT NULL THEN fe_diff END), 3) AS avg_fe,

            COUNT(CASE WHEN mgo_ori IS NOT NULL THEN mgo_ori END) AS jlm_mgo,
            COUNT(CASE WHEN mgo_error = 0 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS error_mgo,
            COUNT(CASE WHEN mgo_error = 1 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS good_mgo,
            ROUND(AVG(CASE WHEN mgo_diff IS NOT NULL THEN mgo_diff END), 3) AS avg_mgo,

            COUNT(CASE WHEN sio2_ori IS NOT NULL THEN sio2_ori END) AS jlm_sio2,
            COUNT(CASE WHEN sio2_error = 0 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS error_sio2,
            COUNT(CASE WHEN sio2_error = 1 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS good_sio2,
            ROUND(AVG(CASE WHEN sio2_diff IS NOT NULL THEN sio2_diff END), 3) AS avg_sio2

        FROM sample_duplicated_mral
        WHERE YEAR(release_date) = %s
    """

    params = (filter_year,)
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)

    # Mencetak hasil DataFrame
    # print(df)

     # load data
    response_data = {
        'jlm_ni'    : int(df['jlm_ni'][0]),
        'error_ni'  : int(df['error_ni'][0]),
        'good_ni'   : int(df['good_ni'][0]),
        'avg_ni'    : float(df['avg_ni'][0]),

        'jlm_co'    : int(df['jlm_co'][0]),
        'error_co'  : int(df['error_co'][0]),
        'good_co'   : int(df['good_co'][0]),
        'avg_co'    : float(df['avg_co'][0]),

        'jlm_fe'    : int(df['jlm_fe'][0]),
        'error_fe'  : int(df['error_fe'][0]),
        'good_fe'   : int(df['good_fe'][0]),
        'avg_fe'    : float(df['avg_fe'][0]),

        'jlm_mgo'   : int(df['jlm_mgo'][0]),
        'error_mgo' : int(df['error_mgo'][0]),
        'good_mgo'  : int(df['good_mgo'][0]),
        'avg_mgo'   : float(df['avg_mgo'][0]),

        'jlm_sio2'  : int(df['jlm_sio2'][0]),
        'error_sio2': int(df['error_sio2'][0]),
        'good_sio2' : int(df['good_sio2'][0]),
        'avg_sio2'  : float(df['avg_sio2'][0]),
    }

    return JsonResponse(response_data)

@login_required
def wetMonthDataMral(request):

    # Mendapatkan nilai filter dari request
    filter_year  = request.GET.get('filter_year')
    filter_month = request.GET.get('filter_month')

    # Gunakan tahun & bulan sekarang jika filter_year & filter_month tidak dipilih
    if not filter_year:
        filter_year = datetime.now().year

    if not filter_month:
        filter_month = datetime.now().month

    # Query dengan parameterisasi untuk keamanan
    query = """
        SELECT
            COUNT(CASE WHEN ni_ori IS NOT NULL THEN ni_ori END) AS jlm_ni,
            COUNT(CASE WHEN ni_error = 0 AND ni_ori IS NOT NULL THEN ni_ori END) AS error_ni,
            COUNT(CASE WHEN ni_error = 1 AND ni_ori IS NOT NULL THEN ni_ori END) AS good_ni,
            ROUND(AVG(CASE WHEN ni_diff IS NOT NULL THEN ni_diff END), 3) AS avg_ni,

            COUNT(CASE WHEN co_ori IS NOT NULL THEN co_ori END) AS jlm_co,
            COUNT(CASE WHEN co_error = 0 AND co_ori IS NOT NULL THEN co_ori END) AS error_co,
            COUNT(CASE WHEN co_error = 1 AND co_ori IS NOT NULL THEN co_ori END) AS good_co,
            ROUND(AVG(CASE WHEN co_diff IS NOT NULL THEN co_diff END), 3) AS avg_co,

            COUNT(CASE WHEN fe_ori IS NOT NULL THEN fe_ori END) AS jlm_fe,
            COUNT(CASE WHEN fe_error = 0 AND fe_ori IS NOT NULL THEN fe_ori END) AS error_fe,
            COUNT(CASE WHEN fe_error = 1 AND fe_ori IS NOT NULL THEN fe_ori END) AS good_fe,
            ROUND(AVG(CASE WHEN fe_diff IS NOT NULL THEN fe_diff END), 3) AS avg_fe,

            COUNT(CASE WHEN mgo_ori IS NOT NULL THEN mgo_ori END) AS jlm_mgo,
            COUNT(CASE WHEN mgo_error = 0 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS error_mgo,
            COUNT(CASE WHEN mgo_error = 1 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS good_mgo,
            ROUND(AVG(CASE WHEN mgo_diff IS NOT NULL THEN mgo_diff END), 3) AS avg_mgo,

            COUNT(CASE WHEN sio2_ori IS NOT NULL THEN sio2_ori END) AS jlm_sio2,
            COUNT(CASE WHEN sio2_error = 0 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS error_sio2,
            COUNT(CASE WHEN sio2_error = 1 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS good_sio2,
            ROUND(AVG(CASE WHEN sio2_diff IS NOT NULL THEN sio2_diff END), 3) AS avg_sio2

        FROM sample_duplicated_mral
        WHERE YEAR(release_date) = %s AND MONTH(release_date) = %s
    """

    params = (filter_year, filter_month)
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)

    # Mencetak hasil DataFrame
    print(df)

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
def wetWeekDataMral(request):

    # Mendapatkan nilai filter dari request
    startDate  = request.GET.get('startDate')
    endDate = request.GET.get('endDate')

    # Query dengan parameterisasi untuk keamanan
    query = """
        SELECT
            COUNT(CASE WHEN ni_ori IS NOT NULL THEN ni_ori END) AS jlm_ni,
            COUNT(CASE WHEN ni_error = 0 AND ni_ori IS NOT NULL THEN ni_ori END) AS error_ni,
            COUNT(CASE WHEN ni_error = 1 AND ni_ori IS NOT NULL THEN ni_ori END) AS good_ni,
            ROUND(AVG(CASE WHEN ni_diff IS NOT NULL THEN ni_diff END), 3) AS avg_ni,

            COUNT(CASE WHEN co_ori IS NOT NULL THEN co_ori END) AS jlm_co,
            COUNT(CASE WHEN co_error = 0 AND co_ori IS NOT NULL THEN co_ori END) AS error_co,
            COUNT(CASE WHEN co_error = 1 AND co_ori IS NOT NULL THEN co_ori END) AS good_co,
            ROUND(AVG(CASE WHEN co_diff IS NOT NULL THEN co_diff END), 3) AS avg_co,

            COUNT(CASE WHEN fe_ori IS NOT NULL THEN fe_ori END) AS jlm_fe,
            COUNT(CASE WHEN fe_error = 0 AND fe_ori IS NOT NULL THEN fe_ori END) AS error_fe,
            COUNT(CASE WHEN fe_error = 1 AND fe_ori IS NOT NULL THEN fe_ori END) AS good_fe,
            ROUND(AVG(CASE WHEN fe_diff IS NOT NULL THEN fe_diff END), 3) AS avg_fe,

            COUNT(CASE WHEN mgo_ori IS NOT NULL THEN mgo_ori END) AS jlm_mgo,
            COUNT(CASE WHEN mgo_error = 0 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS error_mgo,
            COUNT(CASE WHEN mgo_error = 1 AND mgo_ori IS NOT NULL THEN mgo_ori END) AS good_mgo,
            ROUND(AVG(CASE WHEN mgo_diff IS NOT NULL THEN mgo_diff END), 3) AS avg_mgo,

            COUNT(CASE WHEN sio2_ori IS NOT NULL THEN sio2_ori END) AS jlm_sio2,
            COUNT(CASE WHEN sio2_error = 0 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS error_sio2,
            COUNT(CASE WHEN sio2_error = 1 AND sio2_ori IS NOT NULL THEN sio2_ori END) AS good_sio2,
            ROUND(AVG(CASE WHEN sio2_diff IS NOT NULL THEN sio2_diff END), 3) AS avg_sio2

        FROM sample_duplicated_mral
       WHERE release_date >= %s AND release_date <= %s
    """

    params = (startDate, endDate)
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)

    # Mencetak hasil DataFrame
    print(df)

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
 
