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
def mine_production_days_pageQ(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    context = {
        'day_date'   : today.strftime('%Y-%m-%d'),
        'last_monday': last_monday.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mine/analyst-productions.html',context)

@login_required
def productionsMineByDaysQ(request):
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
            ROUND(SUM(total_bcm),2) AS total_bcm,
            ROUND(COALESCE(SUM(DISTINCT t2.TopSoil+t2.OB+t2.LGLO+t2.MGLO+t2.HGLO+t2.Waste+t2.MWS+t2.LGSO+t2.MGSO+t2.HGSO+t2.Quarry+t2.Ballast+t2.Biomass),0),2) as total_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Top Soil' THEN total_bcm ELSE 0 END),0),2) TopSoil,
            ROUND(COALESCE(SUM(DISTINCT t2.TopSoil),0),2) as Soil_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='OB' THEN total_bcm ELSE 0 END),0),2) OB,
            ROUND(COALESCE(SUM(DISTINCT t2.OB),0),2) as OB_Plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGLO' THEN total_bcm ELSE 0 END),0),2) LGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGLO),0),2) as LGLO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGLO' THEN total_bcm ELSE 0 END),0),2) MGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGLO),0),2) as MGLO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGLO' THEN total_bcm ELSE 0 END),0),2) HGLO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGLO),0),2) as HGLO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Waste' THEN total_bcm ELSE 0 END),0),2) Waste,
            ROUND(COALESCE(SUM(DISTINCT t2.Waste),0),2) as Waste_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MWS' THEN total_bcm ELSE 0 END),0),2) MWS,
            ROUND(COALESCE(SUM(DISTINCT t2.MWS),0),2) as MWS_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='LGSO' THEN total_bcm ELSE 0 END),0),2) LGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.LGSO),0),2) as LGSO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='MGSO' THEN total_bcm ELSE 0 END),0),2) MGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.MGSO),0),2) as MGSO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='HGSO' THEN total_bcm ELSE 0 END),0),2) HGSO,
            ROUND(COALESCE(SUM(DISTINCT t2.HGSO),0),2) as HGSO_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Quarry' THEN total_bcm ELSE 0 END),0),2) Quarry,
            ROUND(COALESCE(SUM(DISTINCT t2.Quarry),0),2) as Quarry_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Ballast' THEN total_bcm ELSE 0 END),0),2) Ballast,
            ROUND(COALESCE(SUM(DISTINCT t2.Ballast),0),2) as Ballast_plan,
            ROUND(COALESCE(SUM(CASE WHEN nama_material ='Biomass' THEN total_bcm ELSE 0 END),0),2) Biomass,
            ROUND(COALESCE(SUM(DISTINCT t2.Biomass),0),2) as Biomass_plan,
            t1.ref_materials
         FROM 
         (SELECT date_production, nama_material,category_mine,sources_area,vendors,ref_materials, SUM(total_bcm) AS total_bcm
		  FROM mine_productions_quick
          GROUP BY date_production, nama_material,category_mine,sources_area,vendors,ref_materials
		  ) AS t1
        LEFT JOIN 
            plan_productions AS t2 ON t1.ref_materials = t2.ref_plan

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
        df = pd.DataFrame(chart_data, columns=['total_bcm', 'total_plan', 'TopSoil', 'Soil_plan','OB','OB_plan','LGLO','LGLO_plan',
                                   'MGLO', 'MGLO_plan','HGLO','HGLO_plan','Waste','Waste_plan','MWS', 'MWS_plan','LGSO','LGSO_plan','MGSO','MGSO_plan',
                                   'HGSO', 'HGSO_plan','Quarry','Quarry_plan','Ballast','Ballast_plan','Biomass','Biomass_plan','ref_materials'])
   

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
def productionsMineByHoursQ(request):
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
			ROUND(SUM(total_bcm),2) AS total_bcm,
            ROUND(COALESCE(SUM(DISTINCT t2.TopSoil+t2.OB+t2.LGLO+t2.MGLO+t2.HGLO+t2.Waste+t2.MWS+t2.LGSO+t2.MGSO+t2.HGSO+t2.Quarry+t2.Ballast+t2.Biomass),0),2) as total_plan,
            ROUND(COALESCE(SUM(DISTINCT t2.TopSoil+t2.OB+t2.LGLO+t2.MGLO+t2.HGLO+t2.Waste+t2.MWS+t2.LGSO+t2.MGSO+t2.HGSO+t2.Quarry+t2.Ballast+t2.Biomass),0)/22,2) as plan_hs,
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_7 ELSE 0 END),0),1) as '07',
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_8 ELSE 0 END),0),1) as '08',
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_9 ELSE 0 END),0),1) as '09',
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_10 ELSE 0 END),0),1) as '10',
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_11 ELSE 0 END),0),1) as '11',
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_12 ELSE 0 END),0),1) as '12',
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_13 ELSE 0 END),0),1) as '13',
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_14 ELSE 0 END),0),1) as '14',
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_15 ELSE 0 END),0),1) as '15',
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_16 ELSE 0 END),0),1) as '16',
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_17 ELSE 0 END),0),1) as '17',
            ROUND(COALESCE(SUM(CASE WHEN shift ='DS' THEN bcm_18 ELSE 0 END),0),1) as '18',
            -- NS
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_7 ELSE 0 END),0),1) as '19',
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_8 ELSE 0 END),0),1) as '20',
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_9 ELSE 0 END),0),1) as '21',
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_10 ELSE 0 END),0),1) as '22',
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_11 ELSE 0 END),0),1) as '23',
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_12 ELSE 0 END),0),1) as '00',
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_13 ELSE 0 END),0),1) as '01',
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_14 ELSE 0 END),0),1) as '02',
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_15 ELSE 0 END),0),1) as '03',
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_16 ELSE 0 END),0),1) as '04',
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_17 ELSE 0 END),0),1) as '05',
            ROUND(COALESCE(SUM(CASE WHEN shift ='NS' THEN bcm_18 ELSE 0 END),0),1) as '06',
            t1.ref_materials
        FROM 
         (SELECT 
			 date_production,
             shift,
             category_mine,
             sources_area,
             vendors,
             ref_materials,
			 SUM(total_bcm) AS total_bcm,
			 SUM(bcm_7) AS bcm_7,
			 SUM(bcm_8) AS bcm_8,
			 SUM(bcm_9) AS bcm_9,
			 SUM(bcm_10) AS bcm_10,
			 SUM(bcm_11) AS bcm_11,
			 SUM(bcm_12) AS bcm_12,
			 SUM(bcm_13) AS bcm_13,
			 SUM(bcm_14) AS bcm_14,
			 SUM(bcm_15) AS bcm_15,
			 SUM(bcm_16) AS bcm_16,
			 SUM(bcm_17) AS bcm_17,
			 SUM(bcm_18) AS bcm_18
		  FROM mine_productions_quick
          GROUP BY date_production,shift,category_mine,sources_area,vendors,ref_materials
		  ) AS t1    
        LEFT JOIN 
            plan_productions AS t2 ON t1.ref_materials = t2.ref_plan

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
        df = pd.DataFrame(chart_data, columns=['total_bcm', 'total_plan', 'plan_hs','07','08' ,'09','10','11','12','13',
                                   '14', '15','16','17','18','19','20', '21','22','23','00','01','02', '03','04','05','06', 'ref_materials'])
   

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
        total_bcm   = df['total_bcm'].tolist()  
        total_plan  = df['total_plan'].tolist()  
        plan_hs     = df['plan_hs'].tolist()  
        t_07        = df['07'].tolist()  
        t_08        = df['08'].tolist()  
        t_09        = df['09'].tolist()  
        t_10        = df['10'].tolist()  
        t_11        = df['11'].tolist()  
        t_12        = df['12'].tolist()  
        t_13        = df['13'].tolist()  
        t_14        = df['14'].tolist()  
        t_15        = df['15'].tolist()  
        t_16        = df['16'].tolist()  
        t_17        = df['17'].tolist()  
        t_18        = df['18'].tolist()  
        t_19        = df['19'].tolist()  
        t_20        = df['20'].tolist()  
        t_21        = df['21'].tolist()  
        t_22        = df['22'].tolist()  
        t_23        = df['23'].tolist()  
        t_00        = df['00'].tolist()  
        t_01        = df['01'].tolist()  
        t_02        = df['02'].tolist()  
        t_03        = df['03'].tolist()  
        t_04        = df['04'].tolist()  
        t_05        = df['05'].tolist()  
        t_06        = df['06'].tolist()  
 
        x_data = ['07', '08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','00','01','02','03','04','05','06']
        y_data = [t_07[0],t_08[0],t_09[0],t_10[0],t_11[0],t_12[0],t_13[0],t_14[0],t_15[0],t_16[0],t_17[0],t_18[0], 
                  t_19[0],t_20[0],t_21[0],t_22[0],t_23[0],t_00[0],t_01[0],t_02[0],t_03[0],t_04[0],t_05[0],t_06[0]]
        y_plan = [plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0], plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],
                  plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0],plan_hs[0]]

        # Mengubah objek datetime ke string dalam format yang diinginkan
        label_date = tanggal.strftime("%Y/%m/%d")

        # Create Plotly figure
        fig = go.Figure()
        # Warna untuk masing-masing trace
        colors = {
            'actual' : '#5d9fb0',
            'plan'   : '#7488a9',
        }
    
        fig.add_trace(go.Bar(
            x=x_data,
            y=y_data,
            name='Actual',
            marker = dict(color = colors['actual']),
        ))

        fig.add_trace(go.Line(
            x=x_data,
            y=y_plan,
            name='Plan',
            # marker = dict(color = colors['plan']),
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
             height     = 360,
      
        )

        # Save plot as HTML
        plot_html = pio.to_html(fig,full_html=False, config={'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d', 'toggleSpikelines','pan','select','lasso'],'responsive': True})

        # Kirim data JSON ke template menggunakan JsonResponse
        response_data = {
            'x_data'    : x_data,
            'y_data'    : y_data,
            'y_plan'    : y_plan,
            'total_bcm' : total_bcm,
            'total_plan': total_plan,
            'plot_html' : plot_html # Include plot HTML
        }

        return JsonResponse(response_data)

    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': f"Database query failed: {e}"}, status=500)
