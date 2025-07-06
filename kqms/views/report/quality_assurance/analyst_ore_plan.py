from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections, DatabaseError
from datetime import datetime, timedelta
from collections import Counter
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import logging
logger = logging.getLogger(__name__)
from typing import Sequence

@login_required
def analystOrePlan_page(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
        
    }
    return render(request, 'admin-mgoqa/report-qa/analyst_ore_plan.html',context)
@login_required
def get_data_histograms(request):
    # Generate random data
    a = np.random.normal(1200, 100, 1000)
    b = np.random.normal(1500, 150, 1000)
    df = pd.DataFrame(np.transpose([a, b]), columns=['a', 'b'])

    # Create Plotly figure
    fig = go.Figure()

    values = df['a']

    fig.add_trace(go.Histogram(
        x=df['a'],
        opacity=0.65,
        histnorm='probability',
        name='> 180 t/h',
        # marker_color='#298c9c',
        marker=dict(color='#298c9c'),  # Color with opacity
     ))
    


    # Define layout
    fig.update_layout(
        title='Histogram Comparison',
        barmode='overlay',
        xaxis=dict(
            title='Value'
        ),
        yaxis=dict(
            title=' < 160 t/h'
        ),
        yaxis2=dict(
            title='> 180 t/h',
            overlaying='y',
            side='right'
        ),
        shapes=[
            {
                'type': 'line',
                'x0': df['a'].mean(),
                'x1': df['a'].mean(),
                'xref': 'x',
                'y0': 0,
                'y1': 1,
                'yref': 'paper',
                'line': {
                    'color': '#0099FF',
                    'dash': 'solid',
                    'width': 1
                }
            },
        ],
        annotations=[
            {
                'x': df['a'].mean(),
                'y': 1.05,
                'xref': 'x',
                'yref': 'paper',
                'text': f"Mean a = {df['a'].mean():,.0f}",
                'showarrow': True,
                'arrowhead': 7,
                'ax': 0,
                'ay': -40
            },
        ],
        template='simple_white',
        
    )

    plot_html = pio.to_html(fig,full_html=False, config={
    'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
    'responsive': True})

    response_data = {
            'plot_html': plot_html
    }

    # Return the JSON response
    return JsonResponse(response_data, safe=False)

@login_required
def get_ore_grade_mral(request):
    theme        = request.GET.get('theme', 'light') 
    tgl_pertama  = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')
    dome         = request.GET.get('dome')
    theme        = request.GET.get('theme', 'light')  # Default to 'light'

    query = """
        SELECT
            tonnage, MRAL_Ni,plan_ni_min,plan_ni_max
        FROM 
            details_mral
        WHERE 
            MRAL_Ni IS NOT NULL AND
            tgl_production BETWEEN %s AND %s
        
    """
    # params = [tgl_pertama, tgl_terakhir]
    filters = []
    params  = [tgl_pertama, tgl_terakhir]

    if dome:
        filters.append("pile_id = %s")
        params.append(dome)

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " ORDER BY tgl_production ASC"

    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Create DataFrame from SQL query results
        df = pd.DataFrame(chart_data, columns=['tonnage', 'MRAL_Ni','plan_ni_min','plan_ni_max'])

        if df.empty:
            # Create Plotly figure for empty data
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                plot_bgcolor='#0e1726' if theme == 'dark' else 'rgba(0,0,0,0)',
                paper_bgcolor='#FFFFFF' if theme == 'light' else '#0e1726',
                font=dict(color='#000000' if theme == 'light' else '#FFFFFF'),
                template='plotly_dark' if theme == 'dark' else 'simple_white',
                annotations=[
                    {
                        "text": "No matching data found",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 14}
                    }
                ],
                height=340,
            )
            
            plot_html = pio.to_html(fig, full_html=False)
            return JsonResponse({'plot_html': plot_html})

        # Extract data from DataFrame
        ni_values      = df['MRAL_Ni']
        tonnage_values = df['tonnage']
       

        # Calculate SUMPRODUCT
        sumproduct_value = np.sum(ni_values * tonnage_values)
        total_tonnage    = np.sum(tonnage_values)
        result_value     = sumproduct_value / total_tonnage if total_tonnage != 0 else 0

        # Check lengths of MRAL and Tonnage values
        if len(ni_values) != len(tonnage_values):
            raise ValueError("Length of MRAL values and Tonnage values must be the same.")
        
        # Statistik
        min_ni_raw    = ni_values.min()
        max_ni_raw    = ni_values.max()
        median_mral   = ni_values.median()
        std_deviation = df['MRAL_Ni'].std() 

        # Hitung modus menggunakan pandas
        mode_result = df['MRAL_Ni'].mode()


        # Calculate mode count
        counter     = Counter(df['MRAL_Ni'])
        most_common = counter.most_common()  # Dapatkan semua elemen dengan jumlahnya
        mode_counts = {value: count for value, count in most_common if count == most_common[0][1]}  # Hitung untuk nilai yang paling umum/banyak

        # Ubah hasil mode menjadi nilai tunggal jika tidak kosong []
        mode_value = mode_result.iloc[0] if not mode_result.empty else None
        mode_count = mode_counts.get(mode_value, 0) if mode_value is not None else 0
         
        # Menghitung min_ni dan max_ni untuk tepi bin tanpa pembulatan
        min_ni = np.floor(min_ni_raw * 10) / 10  # Menggunakan floor untuk memastikan tidak ada nilai yang terlewat
        max_ni = np.ceil(max_ni_raw * 10) / 10  # Menggunakan ceil untuk memastikan nilai maksimum termasuk

        
        # Create bins from min_mral to max_mral with a width of 0.1
        # bin_edges = np.arange(min_ni, max_ni + 0.1, 0.1)
        bin_edges = np.arange(min_ni, max_ni + 0.1, 0.1).tolist()
        ni_ranges = [f"{round(edge, 1)} - {round(edge + 0.1, 1)}" for edge in bin_edges[:-1]]

        # Assign ni ranges to each value
        df['Ni_Range'] = pd.cut(df['MRAL_Ni'], bins=bin_edges, labels=ni_ranges, include_lowest=True)

        # Aggregate Tonnage values by MRAL range
        histogram_data = df.groupby('Ni_Range', observed=True)['tonnage'].sum().reset_index()


        # Create Plotly figure
        fig = go.Figure()

        values = histogram_data['tonnage']

        num_data=len(histogram_data['tonnage'])
        bargap = 0.7 if num_data <= 3 else (0.5 if 3 < num_data <= 6 else 0.07)

        fig.add_trace(go.Bar(
            x=histogram_data['Ni_Range'],
            y=histogram_data['tonnage'],
            name='Tonnage by MRAL Range',
            text=histogram_data['tonnage'],
            hoverinfo='text',
            marker=dict(
                color=values,
                colorscale='teal',
                # line=dict(
                #     color='white',
                #     width=1
                # ),
                
            )
        ))


        # Calculate mean, min, and max of MRAL values
        mean_value = ni_values.mean()
        
        if dome:
                dome = request.GET.get('dome') + ':'
                plan_ni_min    = df['plan_ni_min'].iloc[0] if len(df) > 0 else None
                plan_ni_max    = df['plan_ni_max'].iloc[0] if len(df) > 0 else None
        else:
                dome = 'All:'
                plan_ni_min    = 0
                plan_ni_max    = 0


        # Define layout
        # Menentukan warna dan latar belakang berdasarkan tema
        bg_color   = 'rgba(0,0,0,0)' if theme == 'dark' else 'rgba(255,255,255,1)'
        grid_color = 'rgba(255,255,255,0.2)' if theme == 'dark' else 'rgba(0,0,0,0.1)'
        font_color = 'white' if theme == 'dark' else 'black'

        fig.update_layout(
            margin  = dict(l=55, r=55, t=60, b=20),
            title=f"Data by MRAL, {dome}{result_value:.2f} (Plan: {plan_ni_min:.2f} - {plan_ni_max:.2f})",
            xaxis=dict(
                title=f"Median = {median_mral:,.2f},Mean = {mean_value:,.2f},Mode = {mode_value:,.2f}",
                tickangle=-45
            ),
            xaxis_title_font=dict(size=12.5),
            yaxis=dict(
                title='Tonnage'
            ),
            annotations=[
                {
                    'x': mean_value,
                    'y': max(histogram_data['tonnage']) * 0.95,
                    'xref': 'x',
                    'yref': 'y',
                    'text': f"Total = {total_tonnage:,.0f}",
                    'showarrow': True,
                    'arrowhead': 7,
                    'ax': 0,
                    'ay': -30
                },
            ],
            height=390,
            bargap=bargap,
            plot_bgcolor='rgba(201,201,201,0.08)' if theme == 'light' else '#0e1726',
            paper_bgcolor='#FFFFFF' if theme == 'light' else '#0e1726',
            font= dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template= 'plotly_dark' if theme == 'dark' else 'plotly_white',
        )

        plot_html = pio.to_html(fig, full_html=False, config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines', 'pan', 'select', 'lasso'],
            'responsive': True
        })

        achievment = f"{result_value:.2f}"


        # Return the JSON response
        response_data = {
            #  'range_ni': range_ni,
            #  'tonnage' : tonnage,
            #  'dome'    : dome,
             'total_tonnage': total_tonnage,
             'achievment'   : achievment,
             'min_result'   : min_ni_raw,
             'max_result'   : max_ni_raw,
             'median_result': median_mral,
             'mean_result'  : mean_value,
             'mode_value'   : mode_value,
             'mode_count'   : mode_count,
             'std_deviation': std_deviation,
             'plot_html'    : plot_html,
            #  'num_data'     : num_data,
            
        }

        return JsonResponse(response_data, safe=False)
    
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)

@login_required
def get_ore_grade_roa(request):
    # Retrieve date parameters from request
    tgl_pertama  = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')
    dome         = request.GET.get('dome')
    theme        = request.GET.get('theme', 'light')  # Default to 'light'

    query = """
       SELECT
            tonnage,ROA_Ni,plan_ni_min,plan_ni_max
        FROM 
            details_roa
        WHERE 
            ROA_Ni IS NOT NULL AND
            tgl_production BETWEEN %s AND %s
        
    """

    filters = []
    params  = [tgl_pertama, tgl_terakhir]

    if dome:
        filters.append("pile_id = %s")
        params.append(dome)

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " ORDER BY tgl_production ASC"

    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Create DataFrame from SQL query results
        df = pd.DataFrame(chart_data, columns=['tonnage', 'ROA_Ni','plan_ni_min','plan_ni_max'])

        if df.empty:
            # Create Plotly figure for empty data
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                plot_bgcolor='#0e1726' if theme == 'dark' else 'rgba(0,0,0,0)',
                paper_bgcolor='#FFFFFF' if theme == 'light' else '#0e1726',
                font=dict(color='#000000' if theme == 'light' else '#FFFFFF'),
                template='plotly_dark' if theme == 'dark' else 'simple_white',
                annotations=[
                    {
                        "text": "No matching data found",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 14}
                    }
                ],
                height=340,
            )
            
            plot_html = pio.to_html(fig, full_html=False)
            return JsonResponse({'plot_html': plot_html})

        # Extract data from DataFrame
        ni_values      = df['ROA_Ni']
        tonnage_values = df['tonnage']
        

        # Calculate SUMPRODUCT
        sumproduct_value = np.sum(ni_values * tonnage_values)
        total_tonnage    = np.sum(tonnage_values)
        result_value     = sumproduct_value / total_tonnage if total_tonnage != 0 else 0

        # Check lengths of MRAL and Tonnage values
        if len(ni_values) != len(tonnage_values):
            raise ValueError("Length of Roa values and Tonnage values must be the same.")
        
        # Statistik
        min_ni_raw    = ni_values.min()
        max_ni_raw    = ni_values.max()
        median_ni     = ni_values.median()
        std_deviation = df['ROA_Ni'].std()  # Calculate standard deviation

        # Hitung modus menggunakan pandas
        mode_result = df['ROA_Ni'].mode()

        # Calculate mode count
        counter     = Counter(df['ROA_Ni'])
        most_common = counter.most_common()  # Dapatkan semua elemen dengan jumlahnya
        mode_counts = {value: count for value, count in most_common if count == most_common[0][1]}  # Hitung untuk nilai yang paling umum/banyak

        # Ubah hasil mode menjadi nilai tunggal jika tidak kosong []
        mode_value = mode_result.iloc[0] if not mode_result.empty else None
        mode_count = mode_counts.get(mode_value, 0) if mode_value is not None else 0
         
        # Menghitung min_ni dan max_ni untuk tepi bin tanpa pembulatan
        min_ni = np.floor(min_ni_raw * 10) / 10 # Menggunakan floor untuk memastikan tidak ada nilai yang terlewat
        max_ni = np.ceil(max_ni_raw * 10) / 10  # Menggunakan ceil untuk memastikan nilai maksimum termasuk

        
        # Create bins from min_ni to max_ni with a width of 0.1
        # bin_edges = np.arange(min_ni, max_ni + 0.1, 0.1)
        bin_edges = np.arange(min_ni, max_ni + 0.1, 0.1).tolist()
        ni_ranges = [f"{round(edge, 1)} - {round(edge + 0.1, 1)}" for edge in bin_edges[:-1]]

        # Assign Ni ranges to each value
        df['Ni_Range'] = pd.cut(df['ROA_Ni'], bins=bin_edges, labels=ni_ranges, include_lowest=True)

        # Aggregate Tonnage values by ROA range
        histogram_data = df.groupby('Ni_Range', observed=True)['tonnage'].sum().reset_index()


        range_ni= histogram_data['Ni_Range'].to_list()
        tonnage = histogram_data['tonnage'].to_list()

        # Create Plotly figure
        fig = go.Figure()
        values = histogram_data['tonnage']

        num_data=len(histogram_data['tonnage'])
        bargap = 0.7 if num_data <= 3 else (0.5 if 3 < num_data <= 6 else 0.07)

        fig.add_trace(go.Bar(
            x=histogram_data['Ni_Range'],
            y=histogram_data['tonnage'],
            name='Tonnage by Roa',
            text=histogram_data['tonnage'],
            hoverinfo='text',
            marker=dict(
                color=values,
                colorscale='teal',
                # line=dict(
                #     color='white',
                #     width=1
                # )
            )
        ))

        # Calculate mean, min, and max of MRAL values
        mean_value = ni_values.mean()
        
        if dome:
                dome = request.GET.get('dome') + ':'
                plan_ni_min    = df['plan_ni_min'].iloc[0] if len(df) > 0 else None
                plan_ni_max    = df['plan_ni_max'].iloc[0] if len(df) > 0 else None
        else:
                dome = 'All:'
                plan_ni_min    = 0
                plan_ni_max    = 0

        # Define layout
        fig.update_layout(
            margin  = dict(l=55, r=55, t=60, b=20),
            title=f"Data by ROA, {dome}{result_value:.2f} (Plan: {plan_ni_min:.2f} - {plan_ni_max:.2f})",
            xaxis=dict(
                title=f"Median = {median_ni:,.2f},Mean = {mean_value:,.2f},Mode = {mode_value:,.2f}",
                tickangle=-45
            ),
            xaxis_title_font=dict(size=12.5),
            yaxis=dict(
                title='Tonnage'
            ),
             annotations=[
                {
                    'x': mean_value,
                    'y': max(histogram_data['tonnage']) * 0.95,
                    'xref': 'x',
                    'yref': 'y',
                    'text': f"Total = {total_tonnage:,.0f}",
                    'showarrow': True,
                    'arrowhead': 7,
                    'ax': 0,
                    'ay': -30
                },
            ],
            height=390,
            bargap=bargap,
            plot_bgcolor  ='rgba(201,201,201,0.08)' if theme == 'light' else '#0e1726',
            paper_bgcolor ='#FFFFFF' if theme == 'light' else '#0e1726',
            font          = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template      = 'plotly_dark' if theme == 'dark' else 'plotly_white',
        )

        plot_html = pio.to_html(fig, full_html=False, config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines', 'pan', 'select', 'lasso'],
            'responsive': True
        })

        achievment = f"{result_value:.2f}"


        # Return the JSON response
        response_data = {
            #  'range_ni': range_ni,
            #  'tonnage' : tonnage,
            #  'dome'    : dome,
             'total_tonnage': total_tonnage,
             'achievment'   : achievment,
             'min_result'   : min_ni_raw,
             'max_result'   : max_ni_raw,
             'median_result': median_ni,
             'mean_result'  : mean_value,
             'mode_value'   : mode_value,
             'mode_count'   : mode_count,
             'std_deviation': std_deviation,
             'plot_html'    : plot_html,
            
        }

        return JsonResponse(response_data, safe=False)
    
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)

@login_required        
def get_ore_date_qa(request):
    # Retrieve date parameters from request
    tgl_pertama = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')
    theme        = request.GET.get('theme', 'light')  # Default to 'light'

    query = """
        SELECT
            tgl_production, 
            COALESCE(SUM(tonnage), 0) AS total,
            COALESCE(ROUND(SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END), 2), 0) AS total_hpal,
            COALESCE(ROUND(SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END), 2), 0) AS total_rkef
        FROM 
            ore_production
        WHERE 
            tgl_production BETWEEN %s AND %s
        GROUP BY 
            tgl_production
        ORDER BY 
            tgl_production ASC
    """
    params = [tgl_pertama, tgl_terakhir]

    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Create DataFrame from SQL query results
        df = pd.DataFrame(chart_data, columns=['tgl_production','total','total_hpal','total_rkef'])

        if df.empty:
            # Create Plotly figure for empty data
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                plot_bgcolor='#0e1726' if theme == 'dark' else 'rgba(0,0,0,0)',
                paper_bgcolor='#FFFFFF' if theme == 'light' else '#0e1726',
                font=dict(color='#000000' if theme == 'light' else '#FFFFFF'),
                template='plotly_dark' if theme == 'dark' else 'simple_white',
                annotations=[
                    {
                        "text": "No matching data found",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 14}
                    }
                ],
                height=380,
            )
            
            plot_html = pio.to_html(fig, full_html=False)
            return JsonResponse({'plot_html': plot_html})

        # Extract data from DataFrame
        tgl  = df['tgl_production'].tolist()
        hpal = df['total_hpal'].tolist()
        rkef = df['total_rkef'].tolist()

        # Create Plotly figure
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=tgl,
            y=hpal,
            name='HPAL',
            marker=dict(
                color='#5d9fb0',
                # line=dict(
                #     color='white',
                #     width=1
                # )
            )
        ))

        fig.add_trace(go.Bar(
            x=tgl,
            y=rkef,
            name='RKEF',
            # text=rkef,
            # hoverinfo='text',
            # opacity=0.85,
            marker=dict(
                color='#d1eeea',
                line=dict(
                    color='white',
                    width=1
                )
            )
        ))

        # Define layout
        fig.update_layout(
            title='Tonnage by Date',
            xaxis=dict(
                title='Date',
                tickangle=-45
            ),
            yaxis=dict(
                title='Tonnage'
            ),

            legend        = dict(x=0.5, y=1.2, orientation='h'),
            margin        = dict(l=0, r=0, t=40, b=0),
            height        = 380,
            hovermode     = 'x unified',
            bargap        = 0.03,
            plot_bgcolor  ='rgba(201,201,201,0.08)' if theme == 'light' else '#0e1726',
            paper_bgcolor ='#FFFFFF' if theme == 'light' else '#0e1726',
            font          = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template      = 'plotly_dark' if theme == 'dark' else 'plotly_white',
        )

        plot_html = pio.to_html(fig, full_html=False, config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines', 'pan', 'select', 'lasso'],
            'responsive': True
        })

        # Return the JSON response
        response_data = {
            'plot_html': plot_html
        }

        return JsonResponse(response_data, safe=False)
    
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)

@login_required    
def get_ore_dome_qa(request):
    # Retrieve date parameters from request
    tgl_pertama  = request.GET.get('startDate')
    tgl_terakhir = request.GET.get('endDate')
    # theme        = request.GET.get('theme', 'light')  # Default to 'light'

    query = """
        SELECT
            pile_id AS dome,nama_material, COALESCE(SUM(tonnage), 0) AS tonnage
        FROM 
            ore_production
        WHERE 
            tgl_production BETWEEN %s AND %s
        GROUP BY 
            pile_id,nama_material
        ORDER BY 
            nama_material,pile_id ASC
    """
    params = [tgl_pertama, tgl_terakhir]

    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Create DataFrame from SQL query results
        df = pd.DataFrame(chart_data, columns=['dome','nama_material','tonnage'])
       
        if df.empty:
            # Create Plotly figure for empty data
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                # plot_bgcolor='#0e1726' if theme == 'dark' else 'rgba(0,0,0,0)',
                # paper_bgcolor='#FFFFFF' if theme == 'light' else '#0e1726',
                # font=dict(color='#000000' if theme == 'light' else '#FFFFFF'),
                # template='plotly_dark' if theme == 'dark' else 'simple_white',
                annotations=[
                    {
                        "text": "No matching data found",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 14}
                    }
                ],
               height=380,
            )
            
            plot_html = pio.to_html(fig, full_html=False)
            return JsonResponse({'plot_html': plot_html})

        # Extract data from DataFrame
        dome    = df['dome'].tolist()
        tonnage = df['tonnage'].tolist()

        # Create Plotly figure
        fig = go.Figure()

        values = tonnage

        fig.add_trace(go.Bar(
            x=dome,
            y=tonnage,
            name='Tonnage by Dome',
            marker=dict(
                color=values,
                colorscale='teal',
            )
        ))

        # Define layout
        fig.update_layout(
            title='Tonnage by Dome',
            xaxis=dict(
                title='Dome',
            ),
            yaxis=dict(
                title='Tonnage',
            ),
            legend        = dict(x=0.5, y=1.2, orientation='h'),
            margin        = dict(l=0, r=0, t=40, b=0),
            height        = 380,
            hovermode     = 'x unified',
            bargap        = 0.03,  # Adjust bar gap
            # plot_bgcolor  ='rgba(201,201,201,0.08)' if theme == 'light' else '#0e1726',
            # paper_bgcolor ='#FFFFFF' if theme == 'light' else '#0e1726',
            # font          = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            # template      = 'plotly_dark' if theme == 'dark' else 'plotly_white',


        )

        plot_html = pio.to_html(fig, full_html=False, config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines', 'pan', 'select', 'lasso'],
            'responsive': True
        })

        # Return the JSON response
        response_data = {
            'plot_html': plot_html
        }

        return JsonResponse(response_data, safe=False)
    
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)