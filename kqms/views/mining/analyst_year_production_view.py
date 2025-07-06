from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np
from django.db import connections, DatabaseError
from datetime import datetime
import logging
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database
import itertools

@login_required
def materialByYearProduction(request):
    params = []

    # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks    = request.GET.get('filter_days')  
    vendors         = request.GET.get('vendors') 
    sources_area    = request.GET.get('sources_area') 
    category_mine   = request.GET.get('category_mine') 

    # tanggal_teks    = '2024-09-01'
    # category_mine   = 'Project'
    # sources_area    = 'Pit DS'
    # vendors         = 'PB'

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        tanggal = datetime.now()

    tahun = tanggal.year

    # Menginisialisasi query dasar
    base_query = """
            SELECT 
                t1.tahun,t1.bulan,
                ROUND(COALESCE(SUM(DISTINCT t1.TopSoil), 0), 2) as TopSoil,
                ROUND(COALESCE(SUM(DISTINCT t2.TopSoil), 0), 2) as Soil_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.OB), 0), 2) as OB,
                ROUND(COALESCE(SUM(DISTINCT t2.OB_Plan), 0), 2) as OB_Plan,
                ROUND(COALESCE(SUM(DISTINCT t1.LGLO), 0), 2) as LGLO,
                ROUND(COALESCE(SUM(DISTINCT t2.LGLO_plan), 0), 2) as LGLO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.MGLO), 0), 2) as MGLO,
                ROUND(COALESCE(SUM(DISTINCT t2.MGLO_plan), 0), 2) as MGLO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.HGLO), 0), 2) as HGLO,
                ROUND(COALESCE(SUM(DISTINCT t2.HGLO_plan), 0), 2) as HGLO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.Waste), 0), 2) as Waste,
                ROUND(COALESCE(SUM(DISTINCT t2.Waste_plan), 0), 2) as Waste_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.MWS), 0), 2) as MWS,
                ROUND(COALESCE(SUM(DISTINCT t2.MWS_plan), 0), 2) as MWS_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.LGSO), 0), 2) as LGSO,
                ROUND(COALESCE(SUM(DISTINCT t2.LGSO_plan), 0), 2) as LGSO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.MGSO), 0), 2) as MGSO,
                ROUND(COALESCE(SUM(DISTINCT t2.MGSO_plan), 0), 2) as MGSO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.HGSO), 0), 2) as HGSO,
                ROUND(COALESCE(SUM(DISTINCT t2.HGSO_plan), 0), 2) as HGSO_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.Quarry), 0), 2) as Quarry,
                ROUND(COALESCE(SUM(DISTINCT t2.Quarry_plan), 0), 2) as Quarry_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.Ballast), 0), 2) as Ballast,
                ROUND(COALESCE(SUM(DISTINCT t2.Ballast_plan), 0), 2) as Ballast_plan,
                ROUND(COALESCE(SUM(DISTINCT t1.Biomass), 0), 2) as Biomass,
                ROUND(COALESCE(SUM(DISTINCT t2.Biomass_plan), 0), 2) as Biomass_plan
            FROM 
                (
                    SELECT 
                        YEAR(date_production) as tahun,
                        MONTH(date_production) as bulan,
                        category_mine,
                        sources_area, vendors,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN tonnage ELSE 0 END), 0), 2) as TopSoil,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN tonnage ELSE 0 END), 0), 2) as OB,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN tonnage ELSE 0 END), 0), 2) as LGLO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN tonnage ELSE 0 END), 0), 2) as MGLO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN tonnage ELSE 0 END), 0), 2) as HGLO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN tonnage ELSE 0 END), 0), 2) as Waste,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN tonnage ELSE 0 END), 0), 2) as MWS,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN tonnage ELSE 0 END), 0), 2) as LGSO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN tonnage ELSE 0 END), 0), 2) as MGSO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN tonnage ELSE 0 END), 0), 2) as HGSO,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN tonnage ELSE 0 END), 0), 2) as Quarry,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN tonnage ELSE 0 END), 0), 2) as Ballast,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN tonnage ELSE 0 END), 0), 2) as Biomass
                    FROM mine_productions
                    WHERE YEAR(date_production) = %s
                    GROUP BY YEAR(date_production), MONTH(date_production), category_mine, sources_area, vendors
                ) AS t1
            LEFT JOIN (
                SELECT 
                    YEAR(date_plan) as tahun,
                    MONTH(date_plan) as bulan,
                    category, sources, vendors,
                    ROUND(COALESCE(SUM(TopSoil), 0), 2) as TopSoil,
                    ROUND(COALESCE(SUM(OB), 0), 2) as OB_Plan,
                    ROUND(COALESCE(SUM(LGLO), 0), 2) as LGLO_plan,
                    ROUND(COALESCE(SUM(MGLO), 0), 2) as MGLO_plan,
                    ROUND(COALESCE(SUM(HGLO), 0), 2) as HGLO_plan,
                    ROUND(COALESCE(SUM(Waste), 0), 2) as Waste_plan,
                    ROUND(COALESCE(SUM(MWS), 0), 2) as MWS_plan,
                    ROUND(COALESCE(SUM(LGSO), 0), 2) as LGSO_plan,
                    ROUND(COALESCE(SUM(MGSO), 0), 2) as MGSO_plan,
                    ROUND(COALESCE(SUM(HGSO), 0), 2) as HGSO_plan,
                    ROUND(COALESCE(SUM(Quarry), 0), 2) as Quarry_plan,
                    ROUND(COALESCE(SUM(Ballast), 0), 2) as Ballast_plan,
                    ROUND(COALESCE(SUM(Biomass), 0), 2) as Biomass_plan
                FROM plan_productions
                WHERE YEAR(date_plan) = %s
                GROUP BY YEAR(date_plan), MONTH(date_plan), category, sources, vendors
                ) AS t2 
				ON t2.tahun = t1.tahun AND t2.bulan = t1.bulan AND t2.category = t1.category_mine AND t2.sources = t1.sources_area  AND t2.vendors = t1.vendors
        """

    # Tambahkan params untuk tahun
    params.extend([tahun, tahun])

    # Menambahkan filter jika ada
    filters = []

    if category_mine:
        filters.append("t1.category_mine = %s")
        filters.append("t2.category = %s")
        params.extend([category_mine, category_mine])

    if sources_area:
        filters.append("t1.sources_area = %s")
        filters.append("t2.sources = %s")
        params.extend([sources_area, sources_area])

    if vendors:
        filters.append("t1.vendors = %s")
        filters.append("t2.vendors = %s")
        params.extend([vendors, vendors])

    # Menggabungkan filter ke query
    if filters:
        query = base_query + " WHERE " + " AND ".join(filters)
    else:
        query = base_query

    # Menambahkan GROUP BY
    query += " GROUP BY t1.tahun,t1.bulan"

    # Execute the query with params
    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['tahun','bulan', 'TopSoil', 'Soil_plan','OB','OB_plan','LGLO','LGLO_plan',
                                   'MGLO', 'MGLO_plan','HGLO','HGLO_plan','Waste','Waste_plan','MWS', 'MWS_plan','LGSO','LGSO_plan','MGSO','MGSO_plan',
                                   'HGSO', 'HGSO_plan','Quarry','Quarry_plan','Ballast','Ballast_plan','Biomass','Biomass_plan'])
        
        # Cek hasil DataFrame
        # print("DataFrame:", df)

        # if df.empty:
        #     print("DataFrame is empty")
        # else:
        #     print("DataFrame:", df)

        if df.empty:
            # Create Plotly figure for empty data
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                plot_bgcolor='rgba(0,0,0,0)', 
                annotations=[
                    {
                        "text"      : "No matching data found",
                        "xref"      : "paper",
                        "yref"      : "paper",
                        "showarrow" : False,
                        "font"      : {"size": 14}
                    }
                ],
                height=265,
            )
            
            plot_html = pio.to_html(fig, full_html=False)
            return JsonResponse({'plot_html': plot_html})     

        # Menghitung total dari kolom 
        actual_total = df[['TopSoil','OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']].sum()
        plan_total   = df[['Soil_plan','OB_plan','LGLO_plan','MGLO_plan','HGLO_plan','Waste_plan','MWS_plan', 
                           'LGSO_plan','MGSO_plan','HGSO_plan','Quarry_plan','Ballast_plan','Biomass_plan']].sum()
        

        x_data      = ['TopSoil', 'OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']
        actual_data = actual_total.tolist()
        plan_data   = plan_total.tolist()

        actual_accumulated = [round(total, 2) for total in itertools.accumulate(actual_data)]
        plan_accumulated   = [round(total, 2) for total in itertools.accumulate(plan_data)]

        # Create Plotly figure
        fig = go.Figure()
        # Warna untuk masing-masing trace
        colors = {
           'actual': '#00a8b6',
           'plan'  : '#cfd7d9',
        }

        fig.add_trace(go.Bar(
            x=x_data,
            y=actual_data,
            name='Actual',
            marker=dict(color = colors['actual']),
        ))
        
        fig.add_trace(go.Bar(
            x=x_data,
            y=plan_data,
            name='Plan',
            # yaxis='y1',
            marker = dict(color = colors['plan']),

        ))

        fig.update_layout(
            title    =f"Production of {tahun}",
            barmode  = 'group',
            xaxis_title_font=dict(size=12),
            # xaxis=dict(
            #     title='Material'
            # ),
            yaxis=dict(
                title='Bcm',
            ),
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=20, r=20, t=40, b=20),
            height      = 360,
            hovermode   = 'x unified',
            # template   ='plotly_dark'
            # template  ='plotly_white'
            
        )

        plot_html = pio.to_html(fig,full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        response_data = {
            'x_data'            : x_data,
            'y_plan'            : plan_data,
            'y_data'            : actual_data,
            'plan_accumulated'  : plan_accumulated,
            'actual_accumulated': actual_accumulated,
            'plot_html'         : plot_html # Include plot HTML
        }

        # Return the JSON response
        return JsonResponse(response_data, safe=False)


    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

@login_required
def achievmentByYearProduction(request):
    params = []

    # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks    = request.GET.get('filter_days')  
    vendors         = request.GET.get('vendors') 
    sources_area    = request.GET.get('sources_area') 
    category_mine   = request.GET.get('category_mine') 

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        tanggal = datetime.now()

    tahun = tanggal.year

    # Menginisialisasi query dasar
    query = """
        SELECT 
            t1.tahun,t1.bulan,
            ROUND(COALESCE(SUM(DISTINCT t1.TopSoil),0),2) as TopSoil,
            ROUND(COALESCE(SUM(DISTINCT t2.TopSoil),0),2) as Soil_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.OB),0),2) as OB,
            ROUND(COALESCE(SUM(DISTINCT t2.OB_Plan),0),2) as OB_Plan,
            ROUND(COALESCE(SUM(DISTINCT t1.LGLO),0),2) as LGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGLO_plan),0),2) as LGLO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.MGLO),0),2) as MGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGLO_plan),0),2) as MGLO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.HGLO),0),2) as HGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGLO_plan),0),2) as HGLO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Waste),0),2) as Waste,
            ROUND(COALESCE(SUM(DISTINCT t2.Waste_plan),0),2) as Waste_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.MWS),0),2) as MWS,
            ROUND(COALESCE(SUM(DISTINCT t2.MWS_plan),0),2) as MWS_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.LGSO),0),2) as LGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGSO_plan),0),2) as LGSO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.MGSO),0),2) as MGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGSO_plan),0),2) as MGSO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.HGSO),0),2) as HGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGSO_plan),0),2) as HGSO_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Quarry),0),2) as Quarry,
            ROUND(COALESCE(SUM(DISTINCT t2.Quarry_plan),0),2) as Quarry_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Ballast),0),2) as Ballast,
            ROUND(COALESCE(SUM(DISTINCT t2.Ballast_plan),0),2) as Ballast_plan,
            ROUND(COALESCE(SUM(DISTINCT t1.Biomass),0),2) as Biomass,
            ROUND(COALESCE(SUM(DISTINCT t2.Biomass_plan),0),2) as Biomass_plan
        FROM 
            (
                SELECT 
                    YEAR(date_production) as tahun,
                    MONTH(date_production) as bulan,
                    category_mine,
                    sources_area,vendors,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN tonnage ELSE 0 END),0),2) TopSoil,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN tonnage ELSE 0 END),0),2) OB,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN tonnage ELSE 0 END),0),2) LGLO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN tonnage ELSE 0 END),0),2) MGLO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN tonnage ELSE 0 END),0),2) HGLO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN tonnage ELSE 0 END),0),2) Waste,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN tonnage ELSE 0 END),0),2) MWS,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN tonnage ELSE 0 END),0),2) LGSO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN tonnage ELSE 0 END),0),2) MGSO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN tonnage ELSE 0 END),0),2) HGSO,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN tonnage ELSE 0 END),0),2) Quarry,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN tonnage ELSE 0 END),0),2) Ballast,
                    ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN tonnage ELSE 0 END),0),2) Biomass
                FROM mine_productions
                WHERE YEAR(date_production) = %s
                GROUP BY YEAR(date_production), MONTH(date_production), category_mine, sources_area, vendors
            ) AS t1
        LEFT JOIN (
           SELECT 
                YEAR(date_plan) as tahun,
                MONTH(date_plan) as bulan,
                category,sources,vendors,
                ROUND(COALESCE(SUM(TopSoil),0),2) as TopSoil,
                ROUND(COALESCE(SUM(OB),0),2) as OB_Plan,
                ROUND(COALESCE(SUM(LGLO),0),2) as LGLO_plan,
                ROUND(COALESCE(SUM(MGLO),0),2) as MGLO_plan,
                ROUND(COALESCE(SUM(HGLO),0),2) as HGLO_plan,
                ROUND(COALESCE(SUM(Waste),0),2) as Waste_plan,
                ROUND(COALESCE(SUM(MWS),0),2) as MWS_plan,
                ROUND(COALESCE(SUM(LGSO),0),2) as LGSO_plan,
                ROUND(COALESCE(SUM(MGSO),0),2) as MGSO_plan,
                ROUND(COALESCE(SUM(HGSO),0),2) as HGSO_plan,
                ROUND(COALESCE(SUM(Quarry),0),2) as Quarry_plan,
                ROUND(COALESCE(SUM(Ballast),0),2) as Ballast_plan,
                ROUND(COALESCE(SUM(Biomass),0),2) as Biomass_plan
            FROM plan_productions
            WHERE YEAR(date_plan) = %s
            GROUP BY YEAR(date_plan), MONTH(date_plan), category, sources, vendors
        ) AS t2  
        ON CONCAT(t2.tahun, t2.bulan, t2.category, t2.sources, t2.vendors) = CONCAT(t1.tahun, t1.bulan, t1.category_mine, t1.sources_area, t1.vendors)
    """

    # Tambahkan tahun ke params
    params.extend([tahun, tahun])

    # List untuk menampung filter
    filters = []

    # Tambahkan filter berdasarkan parameter yang ada jika ada nilai
    if category_mine:
        filters.append("t1.category_mine = %s")
        filters.append("t2.category = %s")
        params.extend([category_mine, category_mine])  # Append for both subqueries

    if sources_area:
        filters.append("t1.sources_area = %s")
        filters.append("t2.sources = %s")
        params.extend([sources_area, sources_area])  # Append for both subqueries

    if vendors:
        filters.append("t1.vendors = %s")
        filters.append("t2.vendors = %s")
        params.extend([vendors, vendors])  # Append for both subqueries

    # Gabungkan filter jika ada
    if filters:
        query += " WHERE " + " AND ".join(filters)  # Pastikan menggunakan WHERE jika query belum memiliki WHERE

    # Menyelesaikan query
    query += """
            GROUP BY t1.tahun, t1.bulan
    """   
    # Execute the query with params
    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['tahun','bulan', 'TopSoil', 'Soil_plan','OB','OB_plan','LGLO','LGLO_plan',
                                   'MGLO', 'MGLO_plan','HGLO','HGLO_plan','Waste','Waste_plan','MWS', 'MWS_plan','LGSO','LGSO_plan','MGSO','MGSO_plan',
                                   'HGSO', 'HGSO_plan','Quarry','Quarry_plan','Ballast','Ballast_plan','Biomass','Biomass_plan'])

        if df.empty:
            # Create Plotly figure for empty data
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                plot_bgcolor='rgba(0,0,0,0)', 
                annotations=[
                    {
                        "text"      : "No matching data found",
                        "xref"      : "paper",
                        "yref"      : "paper",
                        "showarrow" : False,
                        "font"      : {"size": 14}
                    }
                ],
                height=265,
            )
            
            plot_html = pio.to_html(fig, full_html=False)
            return JsonResponse({'plot_html': plot_html})     

        # Membuat kolom tahun dan bulan
        df['tahun'] = df['tahun']
        df['bulan'] = df['bulan']

        # Mengelompokkan berdasarkan tahun dan bulan, lalu menghitung total
        grouped_totals = df.groupby(['tahun', 'bulan']).agg({
            'TopSoil': 'sum',
            'OB'     : 'sum',
            'LGLO'   : 'sum',
            'MGLO'   : 'sum',
            'HGLO'   : 'sum',
            'Waste'  : 'sum',
            'MWS'    : 'sum',
            'LGSO'   : 'sum',
            'MGSO'   : 'sum',
            'HGSO'   : 'sum',
            'Quarry' : 'sum',
            'Ballast': 'sum',
            'Biomass': 'sum'
        }).reset_index()

        # Untuk total rencana
        plan_totals = df.groupby(['tahun', 'bulan']).agg({
            'Soil_plan'   : 'sum',
            'OB_plan'     : 'sum',
            'LGLO_plan'   : 'sum',
            'MGLO_plan'   : 'sum',
            'HGLO_plan'   : 'sum',
            'Waste_plan'  : 'sum',
            'MWS_plan'    : 'sum',
            'LGSO_plan'   : 'sum',
            'MGSO_plan'   : 'sum',
            'HGSO_plan'   : 'sum',
            'Quarry_plan' : 'sum',
            'Ballast_plan': 'sum',
            'Biomass_plan': 'sum'
        }).reset_index()

        # print("Get sum of the grouped data:\n", grouped_totals)

        # Menghitung total untuk setiap bulan
        grouped_totals['Total'] = grouped_totals[['TopSoil','OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO', 
                                                   'Quarry', 'Ballast', 'Biomass']].sum(axis=1)
        
        plan_totals['Total'] = plan_totals[['Soil_plan','OB_plan','LGLO_plan','MGLO_plan','HGLO_plan','Waste_plan','MWS_plan', 
                                            'LGSO_plan','MGSO_plan','HGSO_plan','Quarry_plan','Ballast_plan','Biomass_plan']].sum(axis=1)

        # Membuat DataFrame baru hanya dengan kolom bulan dan total
        monthly_actual = grouped_totals[['bulan', 'Total']]
        monthly_plan   = plan_totals[['bulan', 'Total']]

        # Menampilkan DataFrame baru
        # print("Bulan dan Total:\n", monthly_actual)

        # Mengambil data dari DataFrame
        actual = monthly_actual['Total'].tolist()
        plan   = monthly_plan['Total'].tolist()

        # Define month names
        bulan_names = ["Jan", "Feb", "Mar", "Ap", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        # Convert month numbers to month names for the x-axis
        bulan = [bulan_names[b - 1] for b in monthly_actual['bulan'].tolist()]
 
        # Create Plotly figure
        fig = go.Figure()
        # Warna untuk masing-masing trace
        colors = {
           'actual': '#00a8b6',
           'plan'  : '#cfd7d9',
        }

        fig.add_trace(go.Bar(
            x=bulan,
            y=actual,
            name='Actual',
            marker=dict(color = colors['actual']),
        ))
        
        fig.add_trace(go.Bar(
            x=bulan,
            y=plan,
            name='Plan',
            # mode='lines',
            marker=dict(color = colors['plan']),
            # line = dict(shape = 'linear',  dash = 'dash'),
            # connectgaps = True
        ))

        fig.update_layout(
            title    =f"Production of {tahun}",
            barmode  = 'group',
            xaxis_title_font=dict(size=12),
            # xaxis=dict(
            #     title='Month of Year'
            # ),
            yaxis=dict(
                title='Bcm',
            ),
            yaxis2=dict(
                # range=[0, 2.3],
                overlaying='y',
                side='right',
                title_font=dict(size=12),
                anchor='x',
            ),

            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=0, r=0, t=40, b=0),
            height      = 360,
            hovermode   = 'x unified',
            # template  ='plotly_dark'
            # template  ='plotly_white'
            
        )

        plot_html = pio.to_html(fig,full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        response_data = {
            'x_data'       : bulan,
            'y_plan'       : plan,
            'y_data'       : actual,
            # 'plan_accumulated'  : plan_accumulated,
            # 'actual_accumulated': actual_accumulated,
            'plot_html'         : plot_html # Include plot HTML
        }

        # Return the JSON response
        return JsonResponse(response_data, safe=False)


    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

