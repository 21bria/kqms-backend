from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np
from django.shortcuts import render
from django.db import connections, DatabaseError
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__) #tambahkan ini untuk multi database

@login_required
def productionsMineByDays(request):
    # params = []
    # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks  = request.GET.get('filter_days') 
    vendors       = request.GET.get('vendors') 
    sources_area  = request.GET.get('sources_area') 
    category_mine = request.GET.get('category_mine') 
    # tanggal_teks  = '2024-09-01' 
    # category_mine = 'Mining' 
    # sources_area  = 'Pit BR1'
    # vendors       = 'PB' 

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        # Jika tidak ada tanggal yang diberikan, gunakan tanggal hari ini
        tanggal = datetime.now().date()
    

    query = """
        SELECT 
            ROUND(SUM(total_tonnage),2) AS total_tonnage,
            ROUND(COALESCE(SUM(DISTINCT t2.TopSoil+t2.OB+t2.LGLO+t2.MGLO+t2.HGLO+t2.Waste+t2.MWS+t2.LGSO+t2.MGSO+t2.HGSO+t2.Quarry+t2.Ballast+t2.Biomass),0),2) as total_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN total_tonnage ELSE 0 END),0),2) TopSoil,
            ROUND(COALESCE(SUM(DISTINCT t2.TopSoil),0),2) as Soil_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN total_tonnage ELSE 0 END),0),2) OB,
            ROUND(COALESCE(SUM(DISTINCT t2.OB),0),2) as OB_Plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN total_tonnage ELSE 0 END),0),2) LGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGLO),0),2) as LGLO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN total_tonnage ELSE 0 END),0),2) MGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGLO),0),2) as MGLO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN total_tonnage ELSE 0 END),0),2) HGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGLO),0),2) as HGLO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN total_tonnage ELSE 0 END),0),2) Waste,
            ROUND(COALESCE(SUM(DISTINCT t2.Waste),0),2) as Waste_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN total_tonnage ELSE 0 END),0),2) MWS,
            ROUND(COALESCE(SUM(DISTINCT t2.MWS),0),2) as MWS_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN total_tonnage ELSE 0 END),0),2) LGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGSO),0),2) as LGSO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN total_tonnage ELSE 0 END),0),2) MGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGSO),0),2) as MGSO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN total_tonnage ELSE 0 END),0),2) HGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGSO),0),2) as HGSO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN total_tonnage ELSE 0 END),0),2) Quarry,
            ROUND(COALESCE(SUM(DISTINCT t2.Quarry),0),2) as Quarry_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN total_tonnage ELSE 0 END),0),2) Ballast,
            ROUND(COALESCE(SUM(DISTINCT t2.Ballast),0),2) as Ballast_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN total_tonnage ELSE 0 END),0),2) Biomass,
            ROUND(COALESCE(SUM(DISTINCT t2.Biomass),0),2) as Biomass_plan
         FROM 
         (SELECT date_production, nama_material,category_mine,sources_area,vendors,ref_material, SUM(tonnage) AS total_tonnage
		  FROM mine_productions
          GROUP BY date_production, nama_material,category_mine,sources_area,vendors,ref_material
		  ) AS t1
        LEFT JOIN 
            plan_productions AS t2 ON t1.ref_material = t2.ref_plan

        WHERE date_production = %s
        """

    filters = []
    params  = [tanggal]

    if category_mine:
        filters.append("t1.category_mine = %s")
        params.append(category_mine)

    if sources_area:
        filters.append("t1.sources_area = %s")
        params.append(sources_area)

    if vendors:
        filters.append("t1.vendors = %s")
        params.append(vendors)

    if filters:
        query += " AND "+" AND ".join(filters)

    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['total_tonnage', 'total_plan', 'TopSoil', 'Soil_plan','OB','OB_plan','LGLO','LGLO_plan',
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
        
        # Extract data dari DataFrame
        actual_total = df[['TopSoil','OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']].sum()
        plan_total   = df[['Soil_plan','OB_plan','LGLO_plan','MGLO_plan','HGLO_plan','Waste_plan','MWS_plan', 
                         'LGSO_plan','MGSO_plan','HGSO_plan','Quarry_plan','Ballast_plan','Biomass_plan']].sum()

        x_data = ['TopSoil', 'OB','LGLO','MGLO','HGLO','Waste','MWS','LGSO','MGSO','HGSO','Quarry','Ballast','Biomass']
        y_data = actual_total.tolist()
        y_plan = plan_total.tolist()

        label_date = tanggal.strftime("%Y/%m/%d")

        # Create Plotly figure
        fig = go.Figure()
        # Warna untuk masing-masing trace
        colors = {
            'actual' : '#5d9fb0',
            'plan'   : '#d1eeea',
            'grey'   : '#cfd7d9',
        }
    
        fig.add_trace(go.Bar(
            x=x_data,
            y=y_data,
            name='Actual',
            marker = dict(color = colors['actual']),
        ))

        fig.add_trace(go.Bar(
            x=x_data,
            y=y_plan,
            name='Plan',
            marker = dict(color = colors['plan']),
       ))
        
        fig.update_layout(
            title       =f"Production of {label_date}",
            yaxis_title ='Bcm',
            barmode     = 'group',
            xaxis_title_font=dict(size=12),
            # xaxis       =dict(title='Materials' ),
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=25, r=25, t=40, b=20),
            hovermode   = 'x unified',
            height      =360, 
        )

        # Save plot as HTML
        plot_html = pio.to_html(fig,full_html=False, config={'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],'responsive': True})

        # Kirim data JSON ke template menggunakan JsonResponse
        response_data = {
            'x_data'  : x_data,
            'y_data'  : y_data,
            'y_plan'  : y_plan,
            'plot_html' : plot_html # Include plot HTML
        }

        return JsonResponse(response_data)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

@login_required
def productionsMineByHours(request):
    # Mendapatkan teks tanggal dari permintaan HTTP
    tanggal_teks  = request.GET.get('filter_days') 
    vendors       = request.GET.get('vendors') 
    sources_area  = request.GET.get('sources_area') 
    category_mine = request.GET.get('category_mine') 
    # tanggal_teks  = '2024-09-01' 
    # category_mine = 'Mining' 
    # sources_area  = 'Pit BR1'
    # vendors       = 'PB' 

    # Mengonversi teks tanggal menjadi objek datetime
    if tanggal_teks:
        tanggal = datetime.strptime(tanggal_teks, "%Y-%m-%d")
    else:
        # Jika tidak ada tanggal yang diberikan, gunakan tanggal hari ini
        tanggal = datetime.now().date()

    filters = []
    params = [tanggal]

    # Menggunakan alias `mine_productions` untuk kondisi dalam subquery
    if category_mine:
        filters.append("mine_productions.category_mine = %s")
        params.append(category_mine)

    if sources_area:
        filters.append("mine_productions.sources_area = %s")
        params.append(sources_area)

    if vendors:
        filters.append("mine_productions.vendors = %s")
        params.append(vendors)


    query = """
        SELECT
            t1.id, 		
            t1.left_time,
            COALESCE(SUM(total_tonnage),0) AS total,
            COALESCE(SUM(plan_data),0) as plan_data
        FROM tanggal_jam  t1
            LEFT JOIN (
                    SELECT 
                        date_production,
					    t_load,
						shift,
			            category_mine,
			            sources_area,
			            mine_productions.vendors,
			            ref_material,
						SUM(tonnage) AS total_tonnage,
						ROUND(COALESCE(SUM(DISTINCT TopSoil+OB+LGLO+MGLO+HGLO+Waste+MWS+LGSO+MGSO+HGSO+Quarry+Ballast+Biomass),0)/22,2) as plan_data
                        FROM mine_productions
                    LEFT JOIN
                    plan_productions ON mine_productions.ref_material = plan_productions.ref_plan   
        WHERE date_production = %s
        """

    if filters:
        query += " AND "+" AND ".join(filters)

    # Menyelesaikan query
    query += """
         GROUP BY date_production,shift,category_mine,sources_area,mine_productions.vendors,t_load,ref_material) AS t2 on t1.left_time = t_load
         GROUP BY
            t1.id,t1.left_time
          ORDER By 
            t1.id asc
        """
    try:
        with connections['kqms_db'].cursor() as cursor:
            cursor.execute(query, params)
            chart_data = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(chart_data, columns=['id', 'left_time', 'total', 'plan_data'])

        print("Columns in df:", df.columns)
        print("df.head():", df.head())


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
        total     = df['total'].tolist()  
        plan      = df['plan_data'].tolist()  

        # Mengonversi 'left_time' ke string dengan menambahkan nol di depan jika perlu
        x_data = df['left_time'] = df['left_time'].apply(lambda x: f"{x:02d}")
        

        # print(x_data.tolist())
        # Mengubah objek datetime ke string dalam format yang diinginkan
        label_date = tanggal.strftime("%Y/%m/%d")

        # Create Plotly figure
        fig = go.Figure()
        # Warna untuk masing-masing trace
        colors = {
            'actual' : '#5d9fb0',
            'plan'   : '#d1eeea'
        }
    
        fig.add_trace(go.Bar(
            x=x_data.tolist(),
            y=total,
            name='Actual',
            marker = dict(color = colors['actual']),
        ))

        fig.add_trace(go.Bar(
            x=x_data.tolist(),
            y=plan,
            name='Plan',
            marker = dict(color = colors['plan']),
       ))
        
        fig.update_layout(
            title       =f"Production of {label_date}",
            yaxis_title ='Bcm',
            barmode     = 'group',
            xaxis_title_font=dict(size=12),
            xaxis=dict(title='Hour of the Day' ),
            plot_bgcolor='rgba(201,201,201,0.08)',
            legend      = dict(x=0.5, y=1.2, orientation='h'),
            margin      = dict(l=25, r=25, t=40, b=20),
            hovermode   = 'x unified',
             height     = 360,
      
        )

        # Save plot as HTML
        plot_html = pio.to_html(fig,full_html=False, config={'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],'responsive': True})

        # Kirim data JSON ke template menggunakan JsonResponse
        response_data = {
            'x_data' : x_data.tolist(),
            'y_data' : total,
            'y_plan' : plan,
            'plot_html' : plot_html # Include plot HTML
        }

        return JsonResponse(response_data)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)

@login_required
def mine_production_days_page(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    context = {
        'day_date'   : today.strftime('%Y-%m-%d'),
        'last_monday': last_monday.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mine/analyst-productions.html',context)
