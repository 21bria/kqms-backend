from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from django.shortcuts import render
from django.http import HttpResponse
from django.db import connections, DatabaseError
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database
import itertools

@login_required
def materialMonthProduction(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
    # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks  = request.GET.get('filter_days')  
    vendors       = request.GET.get('vendors') 
    sources_area  = request.GET.get('sources_area') 
    category_mine = request.GET.get('category_mine') 

    # tanggal_teks  = '2024-09-01'  
    # category_mine = 'Mining' 
    # sources_area  = 'Pit DS' 
    # vendors       = 'PB'

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        tanggal = datetime.now().date()

    hari_ini     = tanggal
    tgl_pertama  = hari_ini.replace(day=1)
    tgl_terakhir = (hari_ini.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    last_day     = tgl_terakhir.day

    tahun = tanggal.year
    bulan = tanggal.month

    # Menginisialisasi query dasar
    query = """
            SELECT 
                 t1.left_date,
                 -- ROUND(COALESCE(SUM(DISTINCT total),0),2) as total_tonagge,
                 -- ROUND(COALESCE(SUM(DISTINCT plan),0),2) as total_plan,
                 ROUND(COALESCE(SUM(DISTINCT TopSoil),0),2) as TopSoil,
                 ROUND(COALESCE(SUM(DISTINCT Soil_plan),0),2) as Soil_plan,
                 ROUND(COALESCE(SUM(DISTINCT OB),0),2) as OB,
                 ROUND(COALESCE(SUM(DISTINCT OB_Plan),0),2) as OB_Plan,
                 ROUND(COALESCE(SUM(DISTINCT LGLO),0),2) as LGLO,
                 ROUND(COALESCE(SUM(DISTINCT LGLO_plan),0),2) as LGLO_plan,
                 ROUND(COALESCE(SUM(DISTINCT MGLO),0),2) as MGLO,
                 ROUND(COALESCE(SUM(DISTINCT MGLO_plan),0),2) as MGLO_plan,
                 ROUND(COALESCE(SUM(DISTINCT HGLO),0),2) as HGLO,
                 ROUND(COALESCE(SUM(DISTINCT HGLO_plan),0),2) as HGLO_plan,
                 ROUND(COALESCE(SUM(DISTINCT Waste),0),2) as Waste,
                 ROUND(COALESCE(SUM(DISTINCT Waste_plan),0),2) as Waste_plan,
                 ROUND(COALESCE(SUM(DISTINCT MWS),0),2) as MWS,
                 ROUND(COALESCE(SUM(DISTINCT MWS_plan),0),2) as MWS_plan,
                 ROUND(COALESCE(SUM(DISTINCT LGSO),0),2) as LGSO,
                 ROUND(COALESCE(SUM(DISTINCT LGSO_plan),0),2) as LGSO_plan,
                 ROUND(COALESCE(SUM(DISTINCT MGSO),0),2) as MGSO,
                 ROUND(COALESCE(SUM(DISTINCT MGSO_plan),0),2) as MGSO_plan,
                 ROUND(COALESCE(SUM(DISTINCT HGSO),0),2) as HGSO,
                 ROUND(COALESCE(SUM(DISTINCT HGSO_plan),0),2) as HGSO_plan,
                 ROUND(COALESCE(SUM(DISTINCT Quarry),0),2) as Quarry,
                 ROUND(COALESCE(SUM(DISTINCT Quarry_plan),0),2) as Quarry_plan,
                 ROUND(COALESCE(SUM(DISTINCT Ballast),0),2) as Ballast,
                 ROUND(COALESCE(SUM(DISTINCT Ballast_plan),0),2) as Ballast_plan,
                 ROUND(COALESCE(SUM(DISTINCT Biomass),0),2) as Biomass,
                 ROUND(COALESCE(SUM(DISTINCT Biomass_plan),0),2) as Biomass_plan
            FROM tanggal t1
            LEFT JOIN (
                    SELECT 
                        left_date,
                        ref_material, 
                        -- SUM(tonnage) AS total,
                        -- ROUND(COALESCE(SUM(DISTINCT TopSoil+OB+LGLO+MGLO+HGLO+Waste+MWS+LGSO+MGSO+HGSO+Quarry+Ballast+Biomass),0),2) as plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN tonnage ELSE 0 END),0),2) TopSoil,
                        ROUND(COALESCE(SUM(DISTINCT TopSoil),0),2) as Soil_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN tonnage ELSE 0 END),0),2) LGLO,
                        ROUND(COALESCE(SUM(DISTINCT LGLO),0),2) as LGLO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN tonnage ELSE 0 END),0),2) OB,
                        ROUND(COALESCE(SUM(DISTINCT OB),0),2) as OB_Plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN tonnage ELSE 0 END),0),2) MGLO,
                        ROUND(COALESCE(SUM(DISTINCT MGLO),0),2) as MGLO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN tonnage ELSE 0 END),0),2) HGLO,
                        ROUND(COALESCE(SUM(DISTINCT HGLO),0),2) as HGLO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN tonnage ELSE 0 END),0),2) Waste,
                        ROUND(COALESCE(SUM(DISTINCT Waste),0),2) as Waste_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN tonnage ELSE 0 END),0),2) MWS,
                        ROUND(COALESCE(SUM(DISTINCT MWS),0),2) as MWS_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN tonnage ELSE 0 END),0),2) LGSO,
                        ROUND(COALESCE(SUM(DISTINCT LGSO),0),2) as LGSO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN tonnage ELSE 0 END),0),2) MGSO,
                        ROUND(COALESCE(SUM(DISTINCT MGSO),0),2) as MGSO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN tonnage ELSE 0 END),0),2) HGSO,
                        ROUND(COALESCE(SUM(DISTINCT HGSO),0),2) as HGSO_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN tonnage ELSE 0 END),0),2) Quarry,
                        ROUND(COALESCE(SUM(DISTINCT Quarry),0),2) as Quarry_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN tonnage ELSE 0 END),0),2) Ballast,
                        ROUND(COALESCE(SUM(DISTINCT Ballast),0),2) as Ballast_plan,
                        ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN tonnage ELSE 0 END),0),2) Biomass,
                        ROUND(COALESCE(SUM(DISTINCT Biomass),0),2) as Biomass_plan
                 	FROM mine_productions
                	LEFT JOIN 
                        plan_productions ON mine_productions.ref_material = plan_productions.ref_plan   
                    WHERE date_production BETWEEN %s AND %s
        """
    # Tambahkan tanggal awal dan akhir ke params
    params.append(tgl_pertama)
    params.append(tgl_terakhir)

    # List untuk menampung filter
    filters = []
 
     # Tambahkan filter berdasarkan parameter yang ada
    if category_mine:
            filters.append("category_mine = %s")
            params.append(category_mine)

    if sources_area:
            filters.append("sources_area = %s")
            params.append(sources_area)

    if vendors:
            filters.append("plan_productions.vendors = %s")
            params.append(vendors)

        # Gabungkan filter jika ada
    if filters:
            query += " AND " + " AND ".join(filters)

    # Menyelesaikan query
    query += """
                GROUP BY left_date, ref_material
            ) AS t2 on t1.left_date = t2.left_date
            WHERE 
                t1.left_date <= %s
            GROUP BY
                t1.left_date
            ORDER By 
                t1.left_date asc
        """

    # Menambahkan last_day ke params
    params.append(last_day)

    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['left_date','TopSoil', 'Soil_plan','OB','OB_plan','LGLO','LGLO_plan',
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

        # Menghitung total dari kolom 
        actual_total = df[['TopSoil','OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']].sum()
        plan_total   = df[['Soil_plan','OB_plan','LGLO_plan','MGLO_plan','HGLO_plan','Waste_plan','MWS_plan', 
                         'LGSO_plan','MGSO_plan','HGSO_plan','Quarry_plan','Ballast_plan','Biomass_plan']].sum()


        x_data      = ['TopSoil', 'OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']
        actual_data = actual_total.tolist()
        plan_data   = plan_total.tolist()

        actual_accumulated = [round(total, 2) for total in itertools.accumulate(actual_data)]
        plan_accumulated   = [round(total, 2) for total in itertools.accumulate(plan_data)]

        # Define month names
        bulan_names = ["Jan", "Feb", "Mar", "Ap", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        bulan = [bulan_names[bulan - 1]]

        # Ambil elemen pertama
        bulan_label = bulan[0] if bulan else '' 

        # Create Plotly figure
        fig = go.Figure()
        # Warna untuk masing-masing trace
        colors = {
            'actual'   : '#00a8b6',
            'plan'     : '#cfd7d9',
            'internal' : '#b4b9ba'
        }

        fig.add_trace(go.Bar(
            x=x_data,
            y=actual_data,
            name='Actual',
            marker = dict(color = colors['actual']),
        ))
        
        fig.add_trace(go.Bar(
            x=x_data,
            y=plan_data,
            name='Plan',
            marker = dict(color = colors['plan']),

        ))
        
        fig.update_layout(
            title       = f"Production of {bulan_label},{tahun} ",
            barmode     = 'group',
            xaxis_title_font=dict(size=12),
            # xaxis=dict(
            #     title='Material'
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
            margin      = dict(l=25, r=25, t=40, b=20),
            height      = 360,
            hovermode   = 'x unified',
            # template    ='plotly_dark'
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
def achievmentMonthProduction(request):
    # Menginisialisasi variabel params sebagai list kosong
    params = []
    # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks  = request.GET.get('filter_days')  
    vendors       = request.GET.get('vendors') 
    sources_area  = request.GET.get('sources_area') 
    category_mine = request.GET.get('category_mine') 

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        tanggal = datetime.now().date()

    hari_ini     = tanggal
    tgl_pertama  = hari_ini.replace(day=1)
    tgl_terakhir = (hari_ini.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    last_day     = tgl_terakhir.day

    bulan = tanggal.month
    tahun = tanggal.year

    # Menginisialisasi query dasar
    query = """
            SELECT 
                t1.left_date,
                ROUND(COALESCE(SUM(DISTINCT tonnage),0),2) as total_tonnage,
                ROUND(COALESCE(SUM(DISTINCT plan_data),0),2) as total_plan
            FROM tanggal t1
            LEFT JOIN (
                SELECT 
                    left_date,
                    category_mine,
			        sources_area,
			        mine_productions.vendors,
                    ref_material, 
                    SUM(tonnage) AS tonnage,
                    ROUND(COALESCE(SUM(DISTINCT TopSoil+OB+LGLO+MGLO+HGLO+Waste+MWS+LGSO+MGSO+HGSO+Quarry+Ballast+Biomass),0),2) as plan_data
                FROM mine_productions
                LEFT JOIN
                     plan_productions ON mine_productions.ref_material = plan_productions.ref_plan 
                WHERE date_production BETWEEN %s AND %s
        """
    # Tambahkan tanggal awal dan akhir ke params
    params.append(tgl_pertama)
    params.append(tgl_terakhir)

    # List untuk menampung filter
    filters = []
 
     # Tambahkan filter berdasarkan parameter yang ada
    if category_mine:
        filters.append("category_mine = %s")
        params.append(category_mine)

    if sources_area:
        filters.append("sources_area = %s")
        params.append(sources_area)

    if vendors:
        filters.append("mine_productions.vendors = %s")
        params.append(vendors)


    # Gabungkan filter jika ada
    if filters:
            query += " AND " + " AND ".join(filters)

    # Menyelesaikan query
    query += """
            GROUP BY left_date,date_production,category_mine,sources_area,mine_productions.vendors,t_load,ref_material) AS t2 on t1.left_date = t2.left_date
            WHERE 
                t1.left_date <= %s
            GROUP BY
                t1.left_date
            ORDER By 
                t1.left_date asc
        """

    # Menambahkan last_day ke params
    params.append(last_day)

    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['left_date', 'total_bcm', 'total_plan'])

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


        # Extract data dari DataFrame
        left_date   = df['left_date'].tolist()  
        total_plan  = df['total_plan'].tolist()  
        total_bcm   = df['total_bcm'].tolist()  

        actual_accumulated = [round(total, 2) for total in itertools.accumulate(total_bcm)]
        plan_accumulated   = [round(total, 2) for total in itertools.accumulate(total_plan)]

        # Define month names
        bulan_names = ["Jan", "Feb", "Mar", "Ap", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        bulan = [bulan_names[bulan - 1]]
        # Ambil elemen pertama
        bulan_label = bulan[0] if bulan else '' 

        # Create Plotly figure
        fig = go.Figure()
        # Warna untuk masing-masing trace
        colors = {
            'actual'   : '#00a8b6',
            'plan'     : '#e44381',
        }

        fig.add_trace(go.Bar(
            x=left_date,
            y=total_bcm,
            name='Actual',
            marker=dict(color = colors['actual']),
        ))

        fig.add_trace(go.Line(
            x=left_date,
            y=total_plan,
            name='Plan',
            mode='lines',
            # yaxis='y1',
            marker=dict(color = colors['plan']),
            #  line = dict(shape = 'linear', color = colors['internal'], dash = 'dash'),
             line = dict(shape = 'linear',  dash = 'dash'),
             connectgaps = True
        ))

        # fig.add_trace(go.Line(
        #     x=left_date,
        #     y=total_plan,
        #     mode='lines+markers+text',
        #     name='Plan',
        #     # yaxis='y1',
        #     marker=dict(color = colors['internal'],  dash="dot", width=2)
        #     # line=dict( dash="dot", width=2)
        # ))
        
        # fig.add_trace(go.Scatter(
        #     x=left_date,
        #     y=plan_accumulated,
        #     mode='lines+markers+text',
        #     name='Cum.Plan',
        #     yaxis='y2',
        #     line=dict(color = colors['internal'],  dash="dot", width=2)
        #     # line=dict( dash="dot", width=2)
        # ))
        
        # fig.add_trace(go.Scatter(
        #     x=left_date,
        #     y=actual_accumulated,
        #     mode='lines+markers+text',
        #     name='Cum.Actual',
        #     yaxis='y2',
        #     marker = dict( size=8,color = colors['surveyor']),
        #     # marker = dict( size=8),
           
        # ))

        fig.update_layout(
            title       =f"Production of {bulan_label},{tahun}",
            barmode     = 'group',
            xaxis_title_font=dict(size=12),
            xaxis=dict(
                tickvals=list(range(1, max(left_date)+1)), 
                ticktext=[str(day) for day in range(1, 32)],
                title='Day of the Month'
            ),
            yaxis=dict(
                title='Bcm',
            ),
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=0, r=0, t=40, b=0),
            height      = 360,
            hovermode   = 'x unified',
            # template    ='plotly_dark'
            # template  ='plotly_white'
            
        )

        plot_html = pio.to_html(fig,full_html=False, config={
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],
        'responsive': True})

        response_data = {
            'x_data'            : left_date,
            'y_plan'            : total_plan,
            'y_data'            : total_bcm,
            'plan_accumulated'  : plan_accumulated,
            'actual_accumulated': actual_accumulated,
            'plot_html'         : plot_html # Include plot HTML
        }

        # Return the JSON response
        return JsonResponse(response_data, safe=False)


    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)
    
