from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json 
from ....models.sample_gc_view import GradeExpectationsMral
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import connections,DatabaseError
import logging
import pandas as pd
import plotly.graph_objs as go
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
pio.templates
from scipy.stats import linregress
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)
import warnings
from ....utils.db_utils import get_db_vendor

# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db') 

@login_required
def grade_expect_chart_page(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())

    context = {
        'start_date' : last_monday.strftime('%Y-%m-%d'),
        'end_date'   : today.strftime('%Y-%m-%d'),
    }   
    return render(request, 'admin-mgoqa/report-gc/grade-expect-chart-mral.html',context)

@login_required
def grade_expectations_page(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())

    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mgoqa/report-gc/list-grade-expectations.html',context)

@login_required
def geos_expect_chart_page(request):
    return render(request, 'admin-mgoqa/report-gc/geos-expect-chart-mral.html')


class GradeExpectations_mral(View):
    def post(self, request):
        # Ambil semua data invoice yang valid
        data_sample = self._datatables(request)
        return JsonResponse(data_sample, safe=False)

    def _datatables(self, request):
        datatables = request.POST
        # Ambil draw
        draw = int(datatables.get('draw'))
        # Ambil start
        start = int(datatables.get('start'))
        # Ambil length (limit)
        length = int(datatables.get('length'))
        # Ambil data search
        search = datatables.get('search[value]')
        # Ambil order column
        order_column = int(datatables.get('order[0][column]'))
        # Ambil order direction
        order_dir = datatables.get('order[0][dir]')

        # Gunakan fungsi get_joined_data
        data = GradeExpectationsMral.objects.all()

        if search:
            data = data.filter(
                Q(nama_material__icontains=search) |
                Q(sample_number__icontains=search) |
                Q(ore_class__icontains=search)
            )

        # Filter berdasarkan parameter dari request
        from_date       = request.POST.get('from_date')
        to_date         = request.POST.get('to_date')
        materialFilter  = request.POST.get('materialFilter')
        sourceFilter      = request.POST.get('sourceFilter')
       

        if from_date and to_date:
            data = data.filter(tgl_production__range=[from_date, to_date])

        if materialFilter:
            data = data.filter(nama_material=materialFilter)

        if sourceFilter:
            data = data.filter(prospect_area=sourceFilter)

        # Atur sorting
        if order_dir == 'desc':
            order_by = f'-{data.model._meta.fields[order_column].name}'
        else:
            order_by = f'{data.model._meta.fields[order_column].name}'

        data = data.order_by(order_by)

        # Menghitung jumlah total sebelum filter
        records_total = data.count()

        # Menerapkan pagination
        paginator   = Paginator(data, length)
        total_pages = paginator.num_pages

        # Menghitung jumlah total setelah filter
        total_records_filtered = paginator.count

        # Atur paginator
        try:
            object_list = paginator.page(start // length + 1).object_list
        except PageNotAnInteger:
            object_list = paginator.page(1).object_list
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages).object_list

        data = [
            {
                "tgl_production" : item.tgl_production,
                "shift"          : item.shift,
                "tgl"            : item.tgl,
                "prospect_area"  : item.prospect_area,
                "mine_block"     : item.mine_block,
                "from_rl"        : item.from_rl,
                "to_rl"          : item.to_rl,
                "nama_material"  : item.nama_material,
                "ore_class"      : item.ore_class,
                "ritase"         : item.ritase,
                "tonnage"        : item.tonnage,
                "batch_code"     : item.batch_code,
                "grade_control"  : item.grade_control,
                "sample_number"  : item.sample_number,
                "ex_ni"          : item.ex_ni,
                "ni_act"         : item.ni_act,
                "ni_diff"        : item.ni_diff,
                "ni_abs"         : item.ni_abs,
                "avg_ex"         : item.avg_ex,
                "avg_act"        : item.avg_act
                
            } for item in object_list
        ]

        return {
            'draw'           : draw,
            'recordsTotal'   : records_total,
            'recordsFiltered': total_records_filtered,
            'data'           : data,
            'start'          : start,
            'length'         : length,
            'totalPages'     : total_pages,
        }

# plotly | graphing libaries
@login_required
def scatter_plot_grade_exmral(request):

    startDate = request.GET.get('startDate')
    endDate   = request.GET.get('endDate')
    material  = request.GET.get('material')
    source    = request.GET.get('source', '[]')

    # Parsing JSON hanya jika filter tidak kosong
    try:
        source  = json.loads(source) if source else []
    except json.JSONDecodeError:
        source  = []

    # Query untuk mengambil data by vendor database
    if db_vendor == 'postgresql':
        query = """
            SELECT
                TRIM(sample_number) AS sample_number,
                TO_CHAR(ex_ni, 'FM999990.000') AS ex_ni,
                TO_CHAR(ni_act, 'FM999990.000') AS ni_act
            FROM grade_expectations_mral
            WHERE sample_number IS NOT NULL 
                AND ex_ni IS NOT NULL  
                AND ni_act IS NOT NULL
                AND tgl_production >= %s 
                AND tgl_production <= %s 
                AND nama_material = %s
        """
    elif db_vendor in ['mssql', 'microsoft']:
        query = """
            SELECT
                TRIM(sample_number) AS sample_number,
                FORMAT(ex_ni, 'N2') AS ex_ni,
                FORMAT(ni_act, 'N2') AS ni_act
            FROM grade_expectations_mral
            WHERE sample_number IS NOT NULL 
                AND ex_ni IS NOT NULL  
                AND ni_act IS NOT NULL
                AND tgl_production >= %s 
                AND tgl_production <= %s 
                AND nama_material = %s
        """
    else:
        raise ValueError("Unsupported database vendor.")

   
    filters = []
    params  = [startDate, endDate, material]

    if source:
        placeholders = ', '.join(['%s'] * len(source))  # Buat placeholder sebanyak elemen dalam `source`
        filters.append(f"prospect_area IN ({placeholders})")  # Masukkan ke klausa WHERE
        params.extend(source)  # Tambahkan semua elemen `source` ke `params`

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " GROUP BY sample_number, ex_ni, ni_act"

    try:
        # Menangani peringatan
        with warnings.catch_warnings():
             warnings.simplefilter("ignore")
             # Use the correct database connection
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
                                "font": {"size": 14}
                            }
                        ],
                    height=360,
                    )
                plot_div = fig.to_html(full_html=False)
                return JsonResponse({'plot_div': plot_div})
        
    except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    except Exception as e:
            logger.error(f"An error occurred: {e}")
            return JsonResponse({'error': str(e)}, status=500)
            


    # Calculate maximum and minimum values
    ni_ex       = df['ex_ni'].astype(float).max()
    ni_act      = df['ni_act'].astype(float).max()
    center_ni   = max(ni_ex, ni_act)
    upper_ni    = round(center_ni + (center_ni * 0.05), 3)
    lower_ni    = round(center_ni - (center_ni * 0.05), 3)

    # Drop rows with NaN values
    df = df.dropna()

    # Calculate linear regression and R-squared value
    slope, intercept, r_value, p_value, std_err = linregress(df['ex_ni'].astype(float), df['ni_act'].astype(float))
    r_squared = float(r_value) ** 2

    # Membuat scatter plot
    fig = go.Figure()
    # Menambahkan garis untuk Upper Line
    fig.add_trace(go.Scatter(
            x=[0, center_ni],
            y=[0, upper_ni],
            type='scatter',
            name='Upper',
            line=dict(color='#ff7c7c',dash='dot')
        ))

        # Menambahkan garis untuk Centre Line
    fig.add_trace(go.Scatter(
            x=[0, center_ni],
            y=[0, center_ni],
            type='scatter',
            name='Centre',
            line=dict(color='#ffe16c',dash='dot')
        ))

        # Menambahkan garis untuk Lower Line
    fig.add_trace(go.Scatter(
            x=[0, center_ni],
            y=[0, lower_ni],
            type='scatter',
            name='Lower',
            line=dict(
                color='#88b1b8',dash='dot'
                )
        ))
    
    # Konversi 'ni_act' menjadi numerik jika perlu
    df['ni_act'] = pd.to_numeric(df['ni_act'], errors='coerce')
    
    values = df['ni_act']
    # Menambahkan scatter plot untuk kolom ni
    fig.add_trace(go.Scatter(
            x=df['ex_ni'],
            y=df['ni_act'],
            mode='markers',
            marker=dict(
                color=values,
                # colorbar=dict(title=""),
                colorscale="Aggrnyl",
                size=9, 
                line=dict(width=0.4, 
                color='white')),
            type='scatter',
            name='Ni',
        ))

    fig.update_layout(
            xaxis=dict(
                type='linear',
                range=[0, 2.2],
                title='Expectation',
                tickmode='linear',
                tick0=0.0,
                dtick= 0.5,
                tickformat='.2f',
                showgrid=False, 
                
            ),
            yaxis=dict(
                type='linear',
                range=[0, 2.2],
                title='Actual',
                tickmode='linear',
                tick0=0.0,
                dtick= 0.5,
                tickformat='.2f',
                showgrid=True,  # Menampilkan grid pada sumbu y
                gridcolor='rgba(0,0,0,0.07)'
            ),
            title='Ni expectation vs actual (MRAL)',
            hovermode='closest',
            plot_bgcolor='rgba(201,201,201,0.08)',
            margin=dict(l=10, r=10, t=70, b=20), 
            legend= dict(
                yref= 'paper',
                font= dict(
                    family= 'Arial, sans-serif',
                    color= 'grey',
                ),
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
             ),
              height=375,
        )

    # Menambahkan anotasi untuk menampilkan nilai R^2
    fig.add_annotation(
            xref="paper", yref="paper",
            x=-0.16, y=1.12,
            showarrow=False,
            text=f'R-squared: {r_squared:.2f}',
            font=dict(
                size=12,
            )
        )

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
    'responsive': True})
    return JsonResponse({'plot_div': plot_div})

@login_required  
def line_plot_sample_exmral(request):
    startDate = request.GET.get('startDate')
    endDate   = request.GET.get('endDate')
    material  = request.GET.get('material')
    source    = request.GET.get('source', '[]')

    # Parsing JSON hanya jika filter tidak kosong
    try:
        source  = json.loads(source) if source else []
    except json.JSONDecodeError:
        source  = []
    source    = request.GET.get('source', '[]')

    # Parsing JSON hanya jika filter tidak kosong
    try:
        source  = json.loads(source) if source else []
    except json.JSONDecodeError:
        source  = []

    query = """
        SELECT
            t3.sample_number,
            COALESCE(SUM(t1.tonnage * t1.grade_expect) / NULLIF(
                        SUM(CASE WHEN t3.sample_number IS NOT NULL AND t1.grade_expect IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                    AS ex_ni,
            COALESCE(SUM(t1.tonnage * t4.ni) / NULLIF (
                    SUM(CASE WHEN t3.sample_number IS NOT NULL AND t4.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                    AS ni_act
        FROM ore_productions AS t1
        LEFT JOIN materials AS t2 ON t2.id=t1.id_material
        LEFT JOIN samples_productions as t3 ON t3.kode_batch=t1.kode_batch
        LEFT JOIN assay_mrals as t4 ON t4.sample_id=t3.sample_number
        LEFT JOIN mine_sources_point_loading AS t5 ON t5.id=t1.id_prospect_area
        WHERE 
        t1.grade_expect IS NOT NULL
            AND t3.sample_number IS NOT NULL 
            AND t4.ni IS NOT NULL  
            AND t1.tgl_production >= %s 
            AND t1.tgl_production <= %s 
            AND t2.nama_material = %s
    """
   
    filters = []
    params  = [startDate, endDate, material]

    if source:
        placeholders = ', '.join(['%s'] * len(source))  # Buat placeholder sebanyak elemen dalam `source`
        filters.append(f"t5.loading_point IN ({placeholders})")  # Masukkan ke klausa WHERE
        params.extend(source)  # Tambahkan semua elemen `source` ke `params`

    # Gabungkan query utama dengan filter tambahan
    if filters:
        query += " AND " + " AND ".join(filters)

    query += " GROUP BY t3.sample_number"

    try:
        # Handle warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Use the correct database connection
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
                height=360,
            )
            plot_div = fig.to_html(full_html=False)
            return JsonResponse({'plot_div': plot_div})

        # Prepare data for Plotly
        # sample_numbers = df['sample_number'].tolist()
        # ex_ni = df['ex_ni'].tolist()
        # ni_act = df['ni_act'].tolist()
        # accuration = [
        #     round(
        #         (1 - abs((row['ni_act'] - row['ex_ni']) / max(row['ni_act'], row['ex_ni']) * 100)) * 100, 2
        #     ) for _, row in df.iterrows()
        # ]

        data = []
        for index, row in df.iterrows():
            x = (row['ni_act'] + row['ex_ni']) / 2
            if x == 0:  # Menghindari pembagian dengan nol
                cari = 0
            else:
                cari = round((1 - abs((row['ni_act'] - row['ex_ni']) / x)) * 100, 1)  # Pembulatan ke satu desimal

            data.append({
                'sample_number': row['sample_number'],
                'ex_ni'        : float(row['ex_ni']),
                'ni_act'       : float(row['ni_act']),
                # 'accuration' : f'{cari:.2f}%'
                'accuration'   : float(cari)  # Simpan sebagai float

            })

        # Create Plotly figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[d['sample_number'] for d in data], y=[d['ex_ni'] for d in data], mode='lines+markers', name='Expectation', yaxis='y1'))
        fig.add_trace(go.Scatter(x=[d['sample_number'] for d in data], y=[d['ni_act'] for d in data], mode='lines+markers', name='Actual', yaxis='y2'))
        # fig.add_trace(go.Scatter(x=[d['sample_number'] for d in data], y=[d['accuration'].replace('%', '') for d in data], mode='lines+markers', name='Accuration', yaxis='y3'))

        fig.add_trace(go.Scatter(
              x=[d['sample_number'] for d in data],
              y=[d['accuration'] for d in data], 
              mode='markers+text',
              name='Accuration', 
              yaxis='y3', 
              text=[f'{d["accuration"]:.1f}%' for d in data], 
              textposition='top center',
              textfont=dict(size=10)
              ))

        fig.update_layout(

            title   ='Data Expectation by Samples (MRAL)',
            xaxis_title ='Sample Number',
            xaxis_title_font=dict(size=12),
            yaxis=dict(
                title='Expectation',
                titlefont=dict(color='blue'),
                # tickmode='linear',
                tickvals=[0.5, 1, 1.5, 2, 2.3],
                ticktext=['0.5', '1', '1.5', '2', '2.3'],
                range=[0, 2.3],
                showgrid=True,
                showline=True
            ),
            yaxis2=dict(
                tickvals=[0, 0.5, 1, 1.5, 2, 2.3],
                ticktext=['0', '0.5', '1', '1.5', '2', '2.3'],
                range=[0, 2.3],
                overlaying='y',
                side='right',
                title_font=dict(size=12),
                showgrid=False,
                showline=False,
                showticklabels=False,
                anchor='x'
            ),
            yaxis3=dict(
                # title='Accuration',
                # titlefont=dict(color='green'),
                title_font=dict(size=12),
                side='right',
                overlaying='y',
                showgrid=True,
                showline=True,
                anchor='x',
                showticklabels=True,
                position=0.95,
                tickvals=[25,50, 75, 100],
                ticktext=['25%', '50%', '75%', '100%'],
                range=[0, 120],
                
            ),

            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=0, r=0, t=40, b=0),
            height      = 360,
            hovermode   = 'x unified',
            # template    ='plotly_dark'
            # template  ='plotly_white'
        )


        # Convert Plotly figure to HTML
        plot_div = fig.to_html(full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        return JsonResponse({'plot_div': plot_div})

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def line_plot_date_exmral(request):
    startDate = request.GET.get('startDate')
    endDate   = request.GET.get('endDate')
    material  = request.GET.get('material')
    source    = request.GET.get('source', '[]')

    # Parsing JSON hanya jika filter tidak kosong
    try:
        source  = json.loads(source) if source else []
    except json.JSONDecodeError:
        source  = []

    query = """
        SELECT
            t1.tgl_production AS tgl,
            COALESCE(SUM(t1.tonnage * t1.grade_expect) / NULLIF(
                        SUM(CASE WHEN t3.sample_number IS NOT NULL AND t1.grade_expect IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                    AS ex_ni,
            COALESCE(SUM(t1.tonnage * t4.ni) / NULLIF (
                    SUM(CASE WHEN t3.sample_number IS NOT NULL AND t4.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                    AS ni_act
        FROM ore_productions AS t1
        LEFT JOIN materials AS t2 ON t2.id=t1.id_material
        LEFT JOIN samples_productions as t3 ON t3.kode_batch=t1.kode_batch
        LEFT JOIN assay_mrals as t4 ON t4.sample_id=t3.sample_number
        LEFT JOIN mine_sources_point_loading AS t5 ON t5.id=t1.id_prospect_area
        WHERE 
        t1.grade_expect IS NOT NULL
            AND t3.sample_number IS NOT NULL 
            AND t4.ni IS NOT NULL  
            AND t1.tgl_production >= %s 
            AND t1.tgl_production <= %s 
            AND t2.nama_material = %s
    """
   
    filters = []
    params = [startDate, endDate, material]

    if source:
        placeholders = ', '.join(['%s'] * len(source))  # Buat placeholder sebanyak elemen dalam `source`
        filters.append(f"t5.loading_point IN ({placeholders})")  # Masukkan ke klausa WHERE
        params.extend(source)  # Tambahkan semua elemen `source` ke `params`

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " GROUP BY t1.tgl_production ORDER BY t1.tgl_production ASC"

    try:
        # Handle warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Use the correct database connection
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
                height=360,
            )
            plot_div = fig.to_html(full_html=False)
            return JsonResponse({'plot_div': plot_div})

        # Prepare data for Plotly
        data = []
        for index, row in df.iterrows():
            x = (row['ni_act'] + row['ex_ni']) / 2
            if x == 0:  # Menghindari pembagian dengan nol
                cari = 0
            else:
                cari = round((1 - abs((row['ni_act'] - row['ex_ni']) / x)) * 100, 1)  # Pembulatan ke satu desimal

            data.append({
                'tgl'       : row['tgl'],
                'ex_ni'     : float(row['ex_ni']),
                'ni_act'    : float(row['ni_act']),
                'accuration': float(cari)  # Simpan sebagai float

            })

        # Create Plotly figure
        fig = go.Figure()

        # Prepare data for Plotly
        x_labels   = [d['tgl'] for d in data]  # Label X
        y_ex_ni    = [d['ex_ni'] for d in data]  # Expectation
        y_ni_act   = [d['ni_act'] for d in data]  # Actual
        accuration = [d['accuration'] for d in data]  # Actual

        # Menghitung rata-rata hanya untuk nilai akurasi yang tidak sama dengan nol
        filtered_accuration = [a for a in accuration if a != 0]
        average_accuration  = sum(filtered_accuration) / len(filtered_accuration) if len(filtered_accuration) > 0 else 0

        fig = go.Figure()

        # Expectation sebagai Area Chart
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=y_ex_ni,
            mode="lines+markers",
            line=dict(width=2, color='rgb(111, 231, 219)'),
            name="Expectation",
            yaxis='y1', 
        ))

         # Actual sebagai Line Chart
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=y_ni_act,
            mode="lines+markers",
            line=dict(width=2, color='rgb(131, 90, 241)'),
            name="Actual",
            yaxis='y1', 
        ))
        
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=accuration,
            mode='markers+text',
            name="Accuration",
            text=[f'{d["accuration"]:.1f}%' for d in data], 
            textposition='top center',
            textfont=dict(size=10),
            yaxis='y3', 
            marker=dict(color='rgba(255, 0, 0, 0.7)'), 

        ))

        fig.update_layout(
            title   ='Data Expectation by Date (MRAL)',
            xaxis=dict(
                title='Date',
                title_font=dict(size=12),
                tickformat='%Y-%m-%d',
            ),

            yaxis=dict(
                title='Expectation',
                titlefont=dict(color='blue'),
                tickvals=[0.5, 1, 1.5, 2, 2.3],
                ticktext=['0.5', '1', '1.5', '2', '2.3'],
                range=[0, 2.3],
                showgrid=True,
                showline=True
            ),

            yaxis2=dict(
                tickvals=[0, 0.5, 1, 1.5, 2, 2.3],
                ticktext=['0', '0.5', '1', '1.5', '2', '2.3'],
                range=[0, 2.3],
                overlaying='y',
                side='right',
                title_font=dict(size=12),
                showgrid=False,
                showline=False,
                showticklabels=False,
                anchor='x'
            ),
            yaxis3=dict(
                title_font=dict(size=12),
                side='right',
                overlaying='y',
                showgrid=True,
                showline=True,
                anchor='x',
                showticklabels=True,
                position=0.95,
                tickvals=[25,50, 75, 100],
                ticktext=['25%', '50%', '75%', '100%'],
                range=[0, 120],
            ),
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=0, r=0, t=40, b=0),
            height      = 320,
            hovermode   = 'x unified',
        )

        # Menambahkan anotasi untuk menampilkan nilai average
        fig.add_annotation(
                xref="paper", yref="paper",
                x=0.5, y=1.08,
                showarrow=False,
                text=f'Average: {average_accuration:.2f}%',
                font=dict(
                    size=12,
                    color='lightslategray'
                )
            )


        # Convert Plotly figure to HTML
        plot_div = fig.to_html(full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        return JsonResponse({'plot_div': plot_div})

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required 
def line_plot_geos_exmral(request):
    startDate = request.GET.get('startDate')
    endDate   = request.GET.get('endDate')
    material  = request.GET.get('material')
    source    = request.GET.get('source', '[]')

    # Parsing JSON hanya jika filter tidak kosong
    try:
        source  = json.loads(source) if source else []
    except json.JSONDecodeError:
        source  = []

    query = """
        SELECT
            TRIM(t1.grade_control) as grade_control,
            COALESCE(SUM(t1.tonnage * t1.grade_expect) / NULLIF(
                        SUM(CASE WHEN t3.sample_number IS NOT NULL AND t1.grade_expect IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                    AS ex_ni,
            COALESCE(SUM(t1.tonnage * t4.ni) / NULLIF (
                    SUM(CASE WHEN t3.sample_number IS NOT NULL AND t4.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                    AS ni_act
        FROM ore_productions AS t1
        LEFT JOIN materials AS t2 ON t2.id=t1.id_material
        LEFT JOIN samples_productions as t3 ON t3.kode_batch=t1.kode_batch
        LEFT JOIN assay_mrals as t4 ON t4.sample_id=t3.sample_number
        LEFT JOIN mine_sources_point_loading AS t5 ON t5.id=t1.id_prospect_area
        WHERE 
        t1.grade_expect IS NOT NULL
            AND t3.sample_number IS NOT NULL 
            AND t4.ni IS NOT NULL  
            AND t1.tgl_production >= %s 
            AND t1.tgl_production <= %s 
            AND t2.nama_material = %s
    """
   
    filters = []
    params = [startDate, endDate, material]

    if source:
        placeholders = ', '.join(['%s'] * len(source))  # Buat placeholder sebanyak elemen dalam `source`
        filters.append(f"t5.loading_point IN ({placeholders})")  # Masukkan ke klausa WHERE
        params.extend(source)  # Tambahkan semua elemen `source` ke `params`

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " GROUP BY t1.grade_control"

    try:
        # Handle warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Use the correct database connection
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
                height=360,
            )
            plot_div = fig.to_html(full_html=False)
            return JsonResponse({'plot_div': plot_div})
        

        data = []
        for index, row in df.iterrows():
            x = (row['ni_act'] + row['ex_ni']) / 2
            if x == 0:  # Menghindari pembagian dengan nol
                cari = 0
            else:
                cari = round((1 - abs((row['ni_act'] - row['ex_ni']) / x)) * 100, 1)  # Pembulatan ke satu desimal

            data.append({
                'grade_control': row['grade_control'],
                'ex_ni'        : float(row['ex_ni']),
                'ni_act'       : float(row['ni_act']),
                'accuration'   : float(cari)  # Simpan sebagai float

            })

        # Prepare data for Plotly
        x_labels   = [d['grade_control'] for d in data]  # Label X
        y_ex_ni    = [d['ex_ni'] for d in data]  # Expectation
        y_ni_act   = [d['ni_act'] for d in data]  # Actual
        accuration = [d['accuration'] for d in data]  # Actual

        # Menghitung rata-rata dari akurasi
        # average_accuration = np.mean(accuration)
        # print(f"Rata-rata akurasi: {average_accuration}")

        # Menghitung rata-rata hanya untuk nilai akurasi yang tidak sama dengan nol
        filtered_accuration = [a for a in accuration if a != 0]
        average_accuration = sum(filtered_accuration) / len(filtered_accuration) if len(filtered_accuration) > 0 else 0
        print(f"Rata-rata akurasi (tanpa nol): {average_accuration}")

        fig = go.Figure()

        # Expectation sebagai Area Chart
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=y_ex_ni,
            mode="lines+markers",
            line=dict(width=2, color='rgb(111, 231, 219)'),
            name="Expectation",
            yaxis='y1', 
        ))

         # Actual sebagai Line Chart
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=y_ni_act,
            mode="lines+markers",
            line=dict(width=2, color='rgb(131, 90, 241)'),
            name="Actual",
            yaxis='y1', 
        ))
        
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=accuration,
            mode='markers+text',
            name="Accuration",
            text=[f'{d["accuration"]:.1f}%' for d in data], 
            textposition='top center',
            textfont=dict(size=10),
            yaxis='y3', 
            marker=dict(color='rgba(255, 0, 0, 0.7)'), 

        ))

        fig.update_layout(
            title='Data Expectation by GC (MRAL)',
            barmode="overlay",
            plot_bgcolor='rgba(201,201,201,0.08)',
            height=320,
            legend=dict(x=0.5, y=1.2, orientation='h'),
            margin=dict(l=10, r=10, t=40, b=5),
            hovermode='x unified',
            yaxis=dict(
                title='Expectation',
                titlefont=dict(color='blue'),
                range=[0, 2.3],
                showgrid=True,
                showline=True
            ),
            yaxis2=dict(
                range=[0, 2.3],
                overlaying='y',
                side='right',
                title_font=dict(size=12),
                showgrid=False,
                showline=False,
                showticklabels=False,
                anchor='x'
            ),
            yaxis3=dict(
                title_font=dict(size=12),
                side='right',
                overlaying='y',
                showgrid=True,
                showline=True,
                anchor='x',
                showticklabels=True,
                position=0.95,
                tickvals=[50, 75, 100],
                ticktext=['50%', '75%', '100%'],
            ),

        )

        # Menambahkan anotasi untuk menampilkan nilai average
        fig.add_annotation(
                xref="paper", yref="paper",
                x=0.5, y=1.08,
                showarrow=False,
                text=f'Average: {average_accuration:.2f}%',
                font=dict(
                    size=12,
                    color='lightslategray'
                )
            )


        # Convert Plotly figure to HTML
        plot_div = fig.to_html(full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        return JsonResponse( 
            {
                'plot_div': plot_div
             }
            )

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# Group Mine Geos
@login_required
def scatterMineGeosExmral(request):
    startDate    = request.GET.get('startDate')
    endDate      = request.GET.get('endDate')
    material     = request.GET.get('material')
    gradeControl = request.GET.get('gradeControl')

    # Query untuk mengambil data
    if db_vendor == 'postgresql':
        query = """
            SELECT
                TRIM(sample_number) AS sample_number,
                TO_CHAR(ex_ni, 'FM999990.000') AS ex_ni,
                TO_CHAR(ni_act, 'FM999990.000') AS ni_act
            FROM grade_expectations_mral
            WHERE sample_number IS NOT NULL 
                AND ex_ni IS NOT NULL  
                AND ni_act IS NOT NULL
                AND tgl_production >= %s 
                AND tgl_production <= %s 
                AND nama_material = %s
                AND grade_control = %s
        """
    elif db_vendor in ['mssql', 'microsoft']:
        query = """
            SELECT
                TRIM(sample_number) AS sample_number,
                FORMAT(ex_ni, 'N3') AS ex_ni,
                FORMAT(ni_act, 'N3') AS ni_act
            FROM grade_expectations_mral
            WHERE sample_number IS NOT NULL 
                AND ex_ni IS NOT NULL  
                AND ni_act IS NOT NULL
                AND tgl_production >= %s 
                AND tgl_production <= %s 
                AND nama_material = %s
                AND grade_control = %s
        """
    else:
        raise ValueError("Unsupported database vendor.")

    params  = [startDate, endDate, material,gradeControl]

    query += " GROUP BY sample_number, ex_ni, ni_act"

    try:
        # Menangani peringatan
        with warnings.catch_warnings():
             warnings.simplefilter("ignore")
             # Use the correct database connection
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
                                "font": {"size": 14}
                            }
                        ],
                    height=360,
                    )
                plot_div = fig.to_html(full_html=False)
                return JsonResponse({'plot_div': plot_div})
        
    except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    except Exception as e:
            logger.error(f"An error occurred: {e}")
            return JsonResponse({'error': str(e)}, status=500)
            


    # Calculate maximum and minimum values
    ni_ex       = df['ex_ni'].astype(float).max()
    ni_act      = df['ni_act'].astype(float).max()
    center_ni   = max(ni_ex, ni_act)
    upper_ni    = round(center_ni + (center_ni * 0.05), 3)
    lower_ni    = round(center_ni - (center_ni * 0.05), 3)

    # Drop rows with NaN values
    df = df.dropna()

    # Calculate linear regression and R-squared value
    slope, intercept, r_value, p_value, std_err = linregress(df['ex_ni'].astype(float), df['ni_act'].astype(float))
    r_squared = float(r_value) ** 2

    # Membuat scatter plot
    fig = go.Figure()
    # Menambahkan garis untuk Upper Line
    fig.add_trace(go.Scatter(
            x=[0, center_ni],
            y=[0, upper_ni],
            type='scatter',
            name='Upper',
            line=dict(color='#ff7c7c',dash='dot')
        ))

        # Menambahkan garis untuk Centre Line
    fig.add_trace(go.Scatter(
            x=[0, center_ni],
            y=[0, center_ni],
            type='scatter',
            name='Centre',
            line=dict(color='#ffe16c',dash='dot')
        ))

        # Menambahkan garis untuk Lower Line
    fig.add_trace(go.Scatter(
            x=[0, center_ni],
            y=[0, lower_ni],
            type='scatter',
            name='Lower',
            line=dict(
                color='#88b1b8',dash='dot'
                )
        ))
    
    # Konversi 'ni_act' menjadi numerik jika perlu
    df['ni_act'] = pd.to_numeric(df['ni_act'], errors='coerce')
    # Cek apakah konversi berhasil
    # print(df['ni_act'].dtype)
    
    values = df['ni_act']
    # Menambahkan scatter plot untuk kolom ni
    fig.add_trace(go.Scatter(
            x=df['ex_ni'],
            y=df['ni_act'],
            mode='markers',
            marker=dict(
                color=values,
                # colorbar=dict(title=""),
                colorscale="Aggrnyl",
                size=9, 
                line=dict(width=0.4, 
                color='white')),
            type='scatter',
            name='Ni',
        ))

    fig.update_layout(
            xaxis=dict(
                type='linear',
                range=[0, 2.2],
                title='Expectation',
                tickmode='linear',
                tick0=0.0,
                dtick= 0.5,
                tickformat='.2f',
                showgrid=False, 
                
            ),
            yaxis=dict(
                type='linear',
                range=[0, 2.2],
                title='Actual',
                tickmode='linear',
                tick0=0.0,
                dtick= 0.5,
                tickformat='.2f',
                showgrid=True,  # Menampilkan grid pada sumbu y
                gridcolor='rgba(0,0,0,0.07)'
            ),
            # title='Ni expectation vs actual (MRAL)',
            title=f'Ni (MRAL) analys -  {gradeControl}',
            hovermode='closest',
            plot_bgcolor='rgba(201,201,201,0.08)',
            margin=dict(l=10, r=10, t=70, b=20), 
            legend= dict(
                yref= 'paper',
                font= dict(
                    family= 'Arial, sans-serif',
                    color= 'grey',
                ),
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
             ),
              height=375,
        )

    # Menambahkan anotasi untuk menampilkan nilai R^2
    fig.add_annotation(
            xref="paper", yref="paper",
            x=-0.16, y=1.12,
            showarrow=False,
            text=f'R-squared: {r_squared:.2f}',
            font=dict(
                size=12,
            )
        )

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
    'responsive': True})
    return JsonResponse({'plot_div': plot_div})  

@login_required
def lineMineGeosExmral(request):
    startDate    = request.GET.get('startDate')
    endDate      = request.GET.get('endDate')
    material     = request.GET.get('material')
    gradeControl = request.GET.get('gradeControl')

    query = """
                SELECT
                    t1.tgl_production AS tgl,
                    COALESCE(SUM(t1.tonnage * t1.grade_expect) / NULLIF(
                                SUM(CASE WHEN t3.sample_number IS NOT NULL AND t1.grade_expect IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                            AS ex_ni,
                    COALESCE(SUM(t1.tonnage * t4.ni) / NULLIF (
                            SUM(CASE WHEN t3.sample_number IS NOT NULL AND t4.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                            AS ni_act
                FROM ore_productions AS t1
                LEFT JOIN materials AS t2 ON t2.id=t1.id_material
                LEFT JOIN samples_productions as t3 ON t3.kode_batch=t1.kode_batch
                LEFT JOIN assay_mrals as t4 ON t4.sample_id=t3.sample_number
                LEFT JOIN mine_sources_point_loading AS t5 ON t5.id=t1.id_prospect_area
                WHERE 
                    t1.grade_expect IS NOT NULL
                    AND t3.sample_number IS NOT NULL 
                    AND t4.ni IS NOT NULL  
                    AND t1.tgl_production >= %s 
                    AND t1.tgl_production <= %s 
                    AND t2.nama_material = %s
                    AND t1.grade_control = %s
    """
   
    params  = [startDate, endDate, material,gradeControl]

    query += " GROUP BY t1.tgl_production"

    # Read data from database using pandas
    try:
        # Handle warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Use the correct database connection
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
                height=360,
            )
            plot_div = fig.to_html(full_html=False)
            return JsonResponse({'plot_div': plot_div})

        # Prepare data for Plotly
        data = []
        for index, row in df.iterrows():
            x = (row['ni_act'] + row['ex_ni']) / 2
            if x == 0:  # Menghindari pembagian dengan nol
                cari = 0
            else:
                cari = round((1 - abs((row['ni_act'] - row['ex_ni']) / x)) * 100, 1)  # Pembulatan ke satu desimal

            data.append({
                'tgl'       : row['tgl'],
                'ex_ni'     : float(row['ex_ni']),
                'ni_act'    : float(row['ni_act']),
                'accuration': float(cari)  # Simpan sebagai float

            })

        # Create Plotly figure
        fig = go.Figure()

        # Prepare data for Plotly
        x_labels   = [d['tgl'] for d in data]  # Label X
        y_ex_ni    = [d['ex_ni'] for d in data]  # Expectation
        y_ni_act   = [d['ni_act'] for d in data]  # Actual
        accuration = [d['accuration'] for d in data]  # Actual


        # Menghitung rata-rata hanya untuk nilai akurasi yang tidak sama dengan nol
        filtered_accuration = [a for a in accuration if a != 0]
        average_accuration = sum(filtered_accuration) / len(filtered_accuration) if len(filtered_accuration) > 0 else 0

        fig = go.Figure()

        # Expectation sebagai Area Chart
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=y_ex_ni,
            mode="lines+markers",
            line=dict(width=2, color='rgb(111, 231, 219)'),
            name="Expectation",
            yaxis='y1', 
        ))

         # Actual sebagai Line Chart
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=y_ni_act,
            mode="lines+markers",
            line=dict(width=2, color='rgb(131, 90, 241)'),
            name="Actual",
            yaxis='y1', 
        ))
        
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=accuration,
            mode='markers+text',
            name="Accuration",
            text=[f'{d["accuration"]:.1f}%' for d in data], 
            textposition='top center',
            textfont=dict(size=10),
            yaxis='y3', 
            marker=dict(color='rgba(255, 0, 0, 0.7)'), 

        ))


        fig.update_layout(
            # title  ='Data Expectation by Date (MRAL)',
            title=f'Data by Date (MRAL) -  {gradeControl}',
            xaxis_title ='Date of Mine Geos',
            xaxis_title_font=dict(size=12),
            yaxis=dict(
                title='Expectation',
                titlefont=dict(color='blue'),
                tickvals=[0.5, 1, 1.5, 2, 2.3],
                ticktext=['0.5', '1', '1.5', '2', '2.3'],
                range=[0, 2.3],
                showgrid=True,
                showline=True
            ),
            yaxis2=dict(
                tickvals=[0, 0.5, 1, 1.5, 2, 2.3],
                ticktext=['0', '0.5', '1', '1.5', '2', '2.3'],
                range=[0, 2.3],
                overlaying='y',
                side='right',
                title_font=dict(size=12),
                showgrid=False,
                showline=False,
                showticklabels=False,
                anchor='x'
            ),
            yaxis3=dict(
                title_font=dict(size=12),
                side='right',
                overlaying='y',
                showgrid=True,
                showline=True,
                anchor='x',
                showticklabels=False,
                position=0.95,
                tickvals=[25,50, 75, 100],
                ticktext=['25%', '50%', '75%', '100%'],
                range=[0, 120],
            ),
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=0, r=0, t=40, b=0),
            height      = 360,
            hovermode   = 'x unified',
        )

        # Menambahkan anotasi untuk menampilkan nilai average
        fig.add_annotation(
                xref="paper", yref="paper",
                x=0.5, y=1.08,
                showarrow=False,
                text=f'Average: {average_accuration:.2f}%',
                font=dict(
                    size=12,
                    color='lightslategray'
                )
            )

        # Convert Plotly figure to HTML
        plot_div = fig.to_html(full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        return JsonResponse({'plot_div': plot_div})

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# Apex Charts
@login_required
def line_plot_sample_exmral_apex(request):
    startDate = request.GET.get('startDate')
    endDate   = request.GET.get('endDate')
    material  = request.GET.get('material')
    source    = request.GET.get('source', '[]')

    # Parsing JSON hanya jika filter tidak kosong
    try:
        source  = json.loads(source) if source else []
    except json.JSONDecodeError:
        source  = []

    query = """
                SELECT
                    t3.sample_number,
                    COALESCE(SUM(t1.tonnage * t1.grade_expect) / NULLIF(
                                SUM(CASE WHEN t3.sample_number IS NOT NULL AND t1.grade_expect IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                            AS ex_ni,
                    COALESCE(SUM(t1.tonnage * t4.ni) / NULLIF (
                            SUM(CASE WHEN t3.sample_number IS NOT NULL AND t4.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                            AS ni_act
                FROM ore_productions AS t1
                LEFT JOIN materials AS t2 ON t2.id=t1.id_material
                LEFT JOIN samples_productions as t3 ON t3.kode_batch=t1.kode_batch
                LEFT JOIN assay_mrals as t4 ON t4.sample_id=t3.sample_number
                LEFT JOIN mine_sources_point_loading AS t5 ON t5.id=t1.id_prospect_area
                WHERE 
                t1.grade_expect IS NOT NULL
                    AND t3.sample_number IS NOT NULL 
                    AND t4.ni IS NOT NULL  
                    AND t1.tgl_production >= %s 
                    AND t1.tgl_production <= %s 
                    AND t2.nama_material = %s
    """
   
    filters = []
    params  = [startDate, endDate, material]

    if source:
        filters.append("prospect_area = %s")
        params.append(source)

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " GROUP BY t3.sample_number"

    # Read data from database using pandas
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)

    # print(query)
    
    if not df.empty:
        data = []
        for index, row in df.iterrows():
            x    = (row['ni_act'] + row['ex_ni']) / 2
            cari = (1 - abs(round((row['ni_act'] - row['ex_ni']) / x * 100 / 100, 3))) * 100

            data.append({
                'sample_number' : row['sample_number'],
                'ex_ni'         : float(row['ex_ni']),
                'ni_act'        : float(row['ni_act']),
                'accuration'    : f'{cari:.2f}%'  
            })

        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'No data found for the given criteria'})
    
@login_required    
def line_plot_date_exmral_apex(request):
    startDate = request.GET.get('startDate')
    endDate   = request.GET.get('endDate')
    material  = request.GET.get('material')
    source    = request.GET.get('source', '[]')

    # Parsing JSON hanya jika filter tidak kosong
    try:
        source  = json.loads(source) if source else []
    except json.JSONDecodeError:
        source  = []

    query = """
                SELECT
                    t1.tgl_production AS tgl,
                    COALESCE(SUM(t1.tonnage * t1.grade_expect) / NULLIF(
                                SUM(CASE WHEN t3.sample_number IS NOT NULL AND t1.grade_expect IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                            AS ex_ni,
                    COALESCE(SUM(t1.tonnage * t4.ni) / NULLIF (
                            SUM(CASE WHEN t3.sample_number IS NOT NULL AND t4.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                            AS ni_act
                FROM ore_productions AS t1
                LEFT JOIN materials AS t2 ON t2.id=t1.id_material
                LEFT JOIN samples_productions as t3 ON t3.kode_batch=t1.kode_batch
                LEFT JOIN assay_mrals as t4 ON t4.sample_id=t3.sample_number
                LEFT JOIN mine_sources_point_loading AS t5 ON t5.id=t1.id_prospect_area
                WHERE 
                    t1.grade_expect IS NOT NULL
                    AND t3.sample_number IS NOT NULL 
                    AND t4.ni IS NOT NULL  
                    AND t1.tgl_production >= %s 
                    AND t1.tgl_production <= %s 
                    AND t2.nama_material = %s
    """
   
    filters = []
    params  = [startDate, endDate, material]

    if source:
        filters.append("prospect_area = %s")
        params.append(source)

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " GROUP BY t1.tgl_production"

    # Read data from database using pandas
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)

    # print(query)
    
    if not df.empty:
        data = []
        for index, row in df.iterrows():
            x    = (row['ni_act'] + row['ex_ni']) / 2
            cari = (1 - abs(round((row['ni_act'] - row['ex_ni']) / x * 100 / 100, 3))) * 100
            # Ubah format tanggal dari 'DD-MM-YYYY' menjadi 'DD-MM-YY'
            tgl_short = row['tgl'].strftime('%d-%m-%y')

            data.append({
                'tgl'        : tgl_short,
                'ex_ni'      : float(row['ex_ni']),
                'ni_act'     : float(row['ni_act']),
                'accuration' : f'{cari:.2f}%'  
            })

        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'No data found for the given criteria'})
    
@login_required    
def line_plot_geos_exmral_apex(request):
  
    startDate = request.GET.get('startDate')
    endDate   = request.GET.get('endDate')
    material  = request.GET.get('material')
    source    = request.GET.get('source', '[]')

    # Parsing JSON hanya jika filter tidak kosong
    try:
        source  = json.loads(source) if source else []
    except json.JSONDecodeError:
        source  = []

    query = """
                SELECT
                    t1.grade_control,
                    COALESCE(SUM(t1.tonnage * t1.grade_expect) / NULLIF(
                                SUM(CASE WHEN t3.sample_number IS NOT NULL AND t1.grade_expect IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                            AS ex_ni,
                    COALESCE(SUM(t1.tonnage * t4.ni) / NULLIF (
                            SUM(CASE WHEN t3.sample_number IS NOT NULL AND t4.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0),0) 
                            AS ni_act
                FROM ore_productions AS t1
                LEFT JOIN materials AS t2 ON t2.id=t1.id_material
                LEFT JOIN samples_productions as t3 ON t3.kode_batch=t1.kode_batch
                LEFT JOIN assay_mrals as t4 ON t4.sample_id=t3.sample_number
                LEFT JOIN mine_sources_point_loading AS t5 ON t5.id=t1.id_prospect_area
                WHERE 
                    t1.grade_expect IS NOT NULL
                    AND t3.sample_number IS NOT NULL 
                    AND t4.ni IS NOT NULL  
                    AND t1.tgl_production >= %s 
                    AND t1.tgl_production <= %s 
                    AND t2.nama_material = %s
    """
   
    filters = []
    params  = [startDate, endDate, material]

    if source:
       filters.append("prospect_area = %s")
       params.append(source)

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " GROUP BY t1.grade_control"

    # Read data from database using pandas
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)

    # print(query)
    
    if not df.empty:
        data = []
        for index, row in df.iterrows():
            x    = (row['ni_act'] + row['ex_ni']) / 2
            cari = (1 - abs(round((row['ni_act'] - row['ex_ni']) / x * 100 / 100, 3))) * 100
            data.append({

                'geos'       : row['grade_control'],
                'ex_ni'      : float(row['ex_ni']),
                'ni_act'     : float(row['ni_act']),
                'accuration' : f'{cari:.2f}%'  
            })

        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'No data found for the given criteria'})
    
@login_required    
def scatterMineGeosExmral_apex(request):
    startDate = request.GET.get('startDate')
    endDate   = request.GET.get('endDate')
    material  = request.GET.get('material')
    gradeControl    = request.GET.get('gradeControl')

    query = """
        SELECT
            TRIM(sample_number) AS sample_number,
            FORMAT(ex_ni, 3) AS ex_ni,
            FORMAT(ni_act, 3) AS ni_act
        FROM grade_expectations_mral
        WHERE sample_number IS NOT NULL 
            AND ex_ni IS NOT NULL  
            AND ni_act IS NOT NULL
            AND tgl_production >= %s 
            AND tgl_production <= %s 
            AND nama_material = %s
            AND grade_control = %s
    """
   
    params  = [startDate, endDate, material,gradeControl]

    query += " GROUP BY sample_number, ex_ni, ni_act"

    # Read data from database using pandas
    df = pd.read_sql_query(query, connections['kqms_db'], params=params)

    # print(query)
    
    if not df.empty:
        # Calculate maximum and minimum values
        ni_ex       = df['ex_ni'].astype(float).max()
        ni_act      = df['ni_act'].astype(float).max()
        center_ni   = max(ni_ex, ni_act)
        upper_ni    = round(center_ni + (center_ni * 0.05), 3)
        lower_ni    = round(center_ni - (center_ni * 0.05), 3)
        
        # Calculate linear regression and R-squared value
        slope, intercept, r_value, p_value, std_err = linregress(df['ex_ni'].astype(float), df['ni_act'].astype(float))
        r_squared = float(r_value) ** 2
        
        # Send data and R-squared value to the frontend
        response_data = {
            'x_data'        : df.to_dict('records'),
            'center_ni'     : center_ni,
            'upper_ni'      : upper_ni,
            'lower_ni'      : lower_ni,
            'r_squared'     : round(r_squared, 2)
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({'error': 'No data found for the given criteria'})

