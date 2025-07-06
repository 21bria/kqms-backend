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
from django.db import connections
from ....utils.db_utils import get_db_vendor
# Memanggil fungsi utility
db_vendor = get_db_vendor('kqms_db')

def get_month_name(month_number):
    """Convert month number to month name abbreviation."""
    months = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    return months.get(month_number, 'Unknown')


@login_required
def sampleTypeChart(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())

    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin-mgoqa/report-qa/sample-type-chart.html',context)


# For Plotly Chart
@login_required
def chartTypeYear(request):
    filter_year = request.GET.get('filter_year')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend
    # Gunakan tahun sekarang jika filter_year tidak dipilih
    if not filter_year:
        filter_year = datetime.now().year

     # Pastikan berupa integer
    filter_year = int(filter_year)

    # Tentukan fungsi ekstraksi tahun yang sesuai untuk SELECT dan GROUP BY
    if db_vendor == 'postgresql':
        year_expr = "EXTRACT(YEAR FROM tgl_produksi)"
        where_clause = f"{year_expr} = %s"
    elif db_vendor in ['mssql', 'microsoft', 'mysql']:
        year_expr = "YEAR(tgl_produksi)"
        where_clause = f"{year_expr} = %s"
    else:
        raise ValueError("Unsupported database vendor.")

    query = f"""
        SELECT
            {year_expr} AS tahun,
            COUNT(CASE WHEN type_sample = 'CKS' AND sample_method IN ('BS', 'CS', 'FS', 'GRB', 'TP', 'BS_DT', 'BS_ADT') THEN 1 END) +
            COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_GC' THEN 1 END) AS gc,
            COUNT(CASE WHEN type_sample = 'PDS' THEN 1 END) +
            COUNT(CASE WHEN type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) +
            COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS qa,
            COUNT(CASE WHEN type_sample = 'HOS' THEN 1 END) AS hos,
            COUNT(CASE WHEN type_sample = 'ROS' THEN 1 END) AS ros
        FROM sample_type_count
        WHERE {where_clause}
        GROUP BY {year_expr}
    """

    df = pd.read_sql_query(query, connections['kqms_db'], params=(filter_year,))

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(0,0,0,0)', 
            template="plotly_dark" if theme == "dark" else "plotly_white",
            height=360,
            annotations=[
                {
                    "text": "No matching data found",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 14}
                }
            ]
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    # load data
    gc      = df['gc'][0]
    qa      = df['qa'][0]
    hos     = df['hos'][0]
    ros     = df['ros'][0]

    x_data = [ros, hos, qa, gc]
    y_data = ['ROS', 'HOS', 'QA', 'GC']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=x_data,
        y=y_data,
        orientation='h',
        text=x_data,  # Display the actual values as text labels
        # textposition='outside',  # Position the labels outside the bars
        marker=dict(
            color='#ffb03a',
        ),
        texttemplate='%{text:.0f}',  # Format the text to show with two decimal places
    ))

        
    fig.update_layout(
      title=f'Sample Production for {filter_year}',  # Dynamic title with filter_month
        title_font=dict(size=20),
        margin=dict(l=70, r=80, t=90, b=80),
        title_x=0.5,
        # barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(
            # title='Value',
            title_font=dict(size=12),
            tickvals=[0, max(x_data)], 
            showgrid=True,
            gridcolor='rgba(0,0,0,0.07)' 
        ),
      bargap=0.2,
      height=360,
      template="plotly_dark" if theme == "dark" else "plotly_white"
    )
   

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True
})
    return JsonResponse({'plot_div': plot_div})

@login_required
def chartOrdersYear(request):
    filter_year = request.GET.get('filter_year')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend
    print(f"DEBUG theme: {theme}")
    # Gunakan tahun sekarang jika filter_year tidak dipilih
    if not filter_year:
        filter_year = datetime.now().year
    filter_year = int(filter_year)

    # Penyesuaian fungsi tahun tergantung database
    if db_vendor == 'postgresql':
        year_expr = "EXTRACT(YEAR FROM tgl_produksi)"
        where_clause = f"{year_expr} = %s"
    elif db_vendor in ['mysql', 'mssql', 'microsoft']:
        year_expr = "YEAR(tgl_produksi)"
        where_clause = f"{year_expr} = %s"
    else:
        raise ValueError("Unsupported database vendor")

    # Query
    query = f"""
        SELECT
            {year_expr} AS tahun,

            COUNT(CASE WHEN mral_order = 'Yes' AND type_sample = 'CKS' THEN 1 END) + 
            COUNT(CASE WHEN mral_order = 'Yes' AND type_sample = 'SPC' AND sample_method = 'SPC_GC' THEN 1 END) AS gc_mral_order,

            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NOT NULL AND type_sample = 'CKS' THEN 1 END) +
            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NOT NULL AND type_sample = 'SPC' AND sample_method = 'SPC_GC' THEN 1 END) AS gc_mral_released,

            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NULL AND type_sample = 'CKS' THEN 1 END) +
            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NULL AND type_sample = 'SPC' AND sample_method = 'SPC_GC' THEN 1 END) AS gc_mral_pre_released,

            COUNT(CASE WHEN mral_order = 'Yes' AND type_sample = 'PDS' THEN 1 END) +
            COUNT(CASE WHEN mral_order = 'Yes' AND type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) +
            COUNT(CASE WHEN mral_order = 'Yes' AND type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS qa_mral_order,

            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NOT NULL AND type_sample = 'PDS' THEN 1 END) +
            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NOT NULL AND type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) +
            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NOT NULL AND type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS qa_mral_released,

            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NULL AND type_sample = 'PDS' THEN 1 END) +
            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NULL AND type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) +
            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NULL AND type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS qa_mral_pre_released,

            COUNT(CASE WHEN roa_order = 'Yes' AND type_sample = 'PDS' THEN 1 END) +
            COUNT(CASE WHEN roa_order = 'Yes' AND type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) +
            COUNT(CASE WHEN roa_order = 'Yes' AND type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS qa_roa_order,

            COUNT(CASE WHEN roa_order = 'Yes' AND release_roa IS NOT NULL AND type_sample = 'PDS' THEN 1 END) +
            COUNT(CASE WHEN roa_order = 'Yes' AND release_roa IS NOT NULL AND type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) +
            COUNT(CASE WHEN roa_order = 'Yes' AND release_roa IS NOT NULL AND type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS qa_roa_released,

            COUNT(CASE WHEN roa_order = 'Yes' AND release_roa IS NULL AND type_sample = 'PDS' THEN 1 END) +
            COUNT(CASE WHEN roa_order = 'Yes' AND release_roa IS NULL AND type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) +
            COUNT(CASE WHEN roa_order = 'Yes' AND release_roa IS NULL AND type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS qa_roa_pre_released,

            COUNT(CASE WHEN mral_order = 'Yes' AND type_sample = 'HOS' THEN 1 END) AS hos_mral_order,
            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NOT NULL AND type_sample = 'HOS' THEN 1 END) AS hos_mral_released,
            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NULL AND type_sample = 'HOS' THEN 1 END) AS hos_mral_pre_released,

            COUNT(CASE WHEN roa_order = 'Yes' AND type_sample = 'HOS' THEN 1 END) AS hos_roa_order,
            COUNT(CASE WHEN roa_order = 'Yes' AND release_roa IS NOT NULL AND type_sample = 'HOS' THEN 1 END) AS hos_roa_released,
            COUNT(CASE WHEN roa_order = 'Yes' AND release_roa IS NULL AND type_sample = 'HOS' THEN 1 END) AS hos_roa_pre_released,

            COUNT(CASE WHEN mral_order = 'Yes' AND type_sample = 'ROS' THEN 1 END) AS ros_mral_order,
            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NOT NULL AND type_sample = 'ROS' THEN 1 END) AS ros_mral_released,
            COUNT(CASE WHEN mral_order = 'Yes' AND release_mral IS NULL AND type_sample = 'ROS' THEN 1 END) AS ros_mral_pre_released,

            COUNT(CASE WHEN roa_order = 'Yes' AND type_sample = 'ROS' THEN 1 END) AS ros_roa_order,
            COUNT(CASE WHEN roa_order = 'Yes' AND release_roa IS NOT NULL AND type_sample = 'ROS' THEN 1 END) AS ros_roa_released,
            COUNT(CASE WHEN roa_order = 'Yes' AND release_roa IS NULL AND type_sample = 'ROS' THEN 1 END) AS ros_roa_pre_released

        FROM sample_type_count
        WHERE {where_clause}
        GROUP BY {year_expr}
    """

    # Jalankan query
    df = pd.read_sql_query(query, connections['kqms_db'], params=(filter_year,))

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(0,0,0,0)', 
            height=360,
            template="plotly_dark" if theme == "dark" else "plotly_white",
            annotations=[
                {
                    "text": "No matching data found",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 14}
                }
            ]
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    #  Load data
    data_order = [
                df['ros_roa_order'][0],
                df['ros_mral_order'][0],
                df['hos_roa_order'][0],
                df['hos_mral_order'][0],
                df['qa_roa_order'][0],
                df['qa_mral_order'][0],
                df['gc_mral_order'][0],
               ]
    
    data_released = [
                df['ros_roa_released'][0],
                df['ros_mral_released'][0],
                df['hos_roa_released'][0],
                df['hos_mral_released'][0],
                df['qa_roa_released'][0],
                df['qa_roa_released'][0],
                df['gc_mral_released'][0],
               ]
    
    data_unreleased = [
                df['ros_roa_pre_released'][0],
                df['ros_mral_pre_released'][0],
                df['hos_roa_pre_released'][0],
                df['hos_mral_pre_released'][0],
                df['qa_roa_pre_released'][0],
                df['qa_mral_pre_released'][0],
                df['gc_mral_pre_released'][0],
               ]

    y=['ROS-ROA', 'ROS-MRAL', 'HOS-ROA', 'HOS-MRAL','QA-ROA', 'QA-MRAL', 'GC-MRAL']
    
    fig = go.Figure()
    

    fig.add_trace(go.Bar(
        y=y, 
        x=data_order, 
        orientation='h',
        text=data_order, 
        texttemplate='%{text:.0f}',
        name='Orders',
        marker=dict(
            color='#abc4aa',
        ),
        ))
    fig.add_trace(go.Bar(
        y=y, 
        x=data_released,
        orientation='h',
        text=data_released, 
        texttemplate='%{text:.0f}',
        name='Released',
         marker=dict(
               color='#c8b6a6',
            ),
        ))
    fig.add_trace(go.Bar(
            y=y, 
            x=data_unreleased,
            orientation='h',
            text=data_unreleased, 
            texttemplate='%{text:.0f}',
            name='PreReleased',
            marker=dict(
               color='#f6e1c3',
            ),
             ))
        
    fig.update_layout(
      title=f'Sample Production for {filter_year}',  
        title_font=dict(size=20),
        margin=dict(l=70, r=80, t=90, b=80),  
        title_x=0.5,
        barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        xaxis=dict(
            title_font=dict(size=12),
            # tickvals=[0, max(y)],
        ),
      bargap=0.1,
      height=360,
      template="plotly_dark" if theme == "dark" else "plotly_white",
    )
   

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True
})
    return JsonResponse({'plot_div': plot_div})


@login_required
def chartTypeMonth(request):
    filter_year  = request.GET.get('filter_year')
    filter_month = request.GET.get('filter_month')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend
   # Default ke tanggal sekarang jika tidak disediakan
    now = datetime.now()
    filter_year = int(filter_year) if filter_year else now.year
    filter_month = int(filter_month) if filter_month else now.month

    # Tentukan fungsi ekstraksi waktu sesuai database
    if db_vendor == 'postgresql':
        year_expr = "EXTRACT(YEAR FROM tgl_produksi)"
        month_expr = "EXTRACT(MONTH FROM tgl_produksi)"
        group_expr = year_expr  # atau group_expr = f"{year_expr}, {month_expr}" jika perlu per bulan
    elif db_vendor in ['mysql', 'mssql', 'microsoft']:
        year_expr = "YEAR(tgl_produksi)"
        month_expr = "MONTH(tgl_produksi)"
        group_expr = year_expr
    else:
        raise ValueError("Unsupported database vendor")

    # Query dinamis
    query = f"""
        SELECT
            {year_expr} AS tahun,
            COUNT(CASE WHEN type_sample = 'CKS' AND sample_method IN ('BS', 'CS', 'FS', 'GRB', 'TP', 'BS_DT', 'BS_ADT') THEN 1 END) +
            COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_GC' THEN 1 END) AS gc,
            COUNT(CASE WHEN type_sample = 'PDS' THEN 1 END) +
            COUNT(CASE WHEN type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) +
            COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS qa,
            COUNT(CASE WHEN type_sample = 'HOS' THEN 1 END) AS hos,
            COUNT(CASE WHEN type_sample = 'ROS' THEN 1 END) AS ros
        FROM sample_type_count
        WHERE {year_expr} = %s AND {month_expr} = %s
        GROUP BY {group_expr}
    """

    # Eksekusi query dengan parameter yang aman
    df = pd.read_sql_query(query, connections['kqms_db'], params=[filter_year, filter_month])

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(0,0,0,0)', 
            template="plotly_dark" if theme == "dark" else "plotly_white",
            annotations=[
                {
                    "text": "No matching data found",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 14}
                }
            ],
            # width=320,
            height=360,
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    # Load data
    gc  = df['gc'][0]
    qa  = df['qa'][0]
    hos = df['hos'][0]
    ros = df['ros'][0]

    x_data = [ros, hos, qa, gc]
    y_data = ['ROS', 'HOS', 'QA', 'GC']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=x_data,
        y=y_data,
        orientation='h',
        text=x_data,  # Display the actual values as text labels
        textposition='outside',  # Position the labels outside the bars
        marker=dict(
            # color='rgba(50, 171, 96, 0.6)',
            color='#a0d429',
            line=dict(
                color='rgba(50, 171, 96, 1.0)',
                width=0
            ),
        ),
        texttemplate='%{text:.0f}',  # Format the text to show with two decimal places
        # width=0.3  # Adjust the width of the bars
    ))

     
    # Get month name for title
    month_name = get_month_name(filter_month)   

    fig.update_layout(
        title=f'Sample Production for {month_name} {filter_year}',  # Dynamic title with filter_month
        title_font=dict(size=20),
        margin=dict(l=70, r=80, t=90, b=80),  # Increase left margin to accommodate labels
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(
            # title='Value',
            title_font=dict(size=12),
            tickvals=[0, max(x_data)],  # Define tick values for the x-axis
        ),
        # yaxis=dict(
        #     title='Category',
        #     title_font=dict(size=15)
        # ),
        bargap=0.2,  # Adjust the gap between bars
        height=360,
        template="plotly_dark" if theme == "dark" else "plotly_white",
    )
    
   

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True
})
    return JsonResponse({'plot_div': plot_div})

@login_required
def chartFiveWeeks(request):
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend

    sample_type_counts = """
        COUNT(CASE WHEN type_sample = 'CKS' THEN 1 END) +
        COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_GC' THEN 1 END) AS gc,
        COUNT(CASE WHEN type_sample = 'PDS' THEN 1 END) +
        COUNT(CASE WHEN type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) +
        COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS qa,
        COUNT(CASE WHEN type_sample = 'HOS' THEN 1 END) AS hos,
        COUNT(CASE WHEN type_sample = 'ROS' THEN 1 END) AS ros
    """

    if db_vendor == 'mysql':
        query = f"""
            SELECT
                CONCAT('Week ', WEEK(tgl_produksi)) AS minggu,
                DATE_SUB(tgl_produksi, INTERVAL WEEKDAY(tgl_produksi) DAY) AS start_date,
                DATE_ADD(DATE_SUB(tgl_produksi, INTERVAL WEEKDAY(tgl_produksi) DAY), INTERVAL 6 DAY) AS end_date,
                {sample_type_counts}
            FROM sample_type_count
            WHERE tgl_produksi >= CURDATE() - INTERVAL 4 WEEK
            GROUP BY 
                YEAR(tgl_produksi),
                WEEK(tgl_produksi),
                start_date,
                end_date
            ORDER BY minggu;
        """

    elif db_vendor in ['mssql', 'microsoft']:
        query = f"""
            SELECT
                'Week ' + CAST(DATEPART(WEEK, tgl_produksi) AS VARCHAR) AS minggu,
                DATEADD(DAY, -DATEPART(WEEKDAY, tgl_produksi) + 1, tgl_produksi) AS start_date,
                DATEADD(DAY, -DATEPART(WEEKDAY, tgl_produksi) + 7, tgl_produksi) AS end_date,
                {sample_type_counts}
            FROM sample_type_count
            WHERE tgl_produksi >= DATEADD(WEEK, -4, GETDATE())
            GROUP BY 
                DATEPART(YEAR, tgl_produksi),
                DATEPART(WEEK, tgl_produksi),
                DATEADD(DAY, -DATEPART(WEEKDAY, tgl_produksi) + 1, tgl_produksi),
                DATEADD(DAY, -DATEPART(WEEKDAY, tgl_produksi) + 7, tgl_produksi)
            ORDER BY minggu;
        """

    elif db_vendor == 'postgresql':
        query = f"""
            SELECT
                'Week ' || EXTRACT(WEEK FROM tgl_produksi)::int AS minggu,
                tgl_produksi - INTERVAL '1 day' * EXTRACT(DOW FROM tgl_produksi) AS start_date,
                tgl_produksi - INTERVAL '1 day' * EXTRACT(DOW FROM tgl_produksi) + INTERVAL '6 day' AS end_date,
                {sample_type_counts}
            FROM sample_type_count
            WHERE tgl_produksi >= CURRENT_DATE - INTERVAL '28 days'
            GROUP BY 
                EXTRACT(YEAR FROM tgl_produksi),
                EXTRACT(WEEK FROM tgl_produksi),
                start_date,
                end_date
            ORDER BY minggu;
        """

    else:
        raise ValueError("Unsupported database vendor.")

    df = pd.read_sql_query(query, connections['kqms_db'])

    # print( df['minggu'].tolist())

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
    gc  = df['GC'].tolist()
    qa  = df['QA'].tolist()
    hos = df['HOS'].tolist()
    ros = df['ROS'].tolist()
    x   = df['minggu'].tolist()
    

    fig = go.Figure()

    # Warna untuk masing-masing trace
    colors = {
        'GC': '#8fd7b8',
        'QA': '#fade91',
        'HOS': '#FFA07A',
        'ROS': '#bcc3c9'
    }
    
    # Tambahkan trace dengan warna khusus
    fig.add_trace(go.Bar(
        x=x,
        y=gc,
        name="GC",
        text=gc,
        marker=dict(color=colors['GC']),
    ))

    fig.add_trace(go.Bar(
        x=x,
        y=qa,
        name="QA",
        text=qa,
        marker=dict(color=colors['QA']),
    ))

    fig.add_trace(go.Bar(
        x=x,
        y=hos,
        name="HOS",
        text=hos,
        marker=dict(color=colors['HOS']),
    ))

    fig.add_trace(go.Bar(
        x=x,
        y=ros,
        name="ROS",
        text=ros,
        marker=dict(color=colors['ROS']),
    ))
     
    fig.update_layout(
        title=f'Sample production for last 5 week',  
        title_font=dict(size=20),
        margin=dict(l=70, r=80, t=90, b=80),
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation="h"),
        xaxis=dict(
            # title='Value',
            title_font=dict(size=12),
            # tickvals=[0, max(x_data)],  # Define tick values for the x-axis
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
def chartTypeByWeek(request):
    params     = []
    start_date = request.GET.get('startDate')
    end_date   = request.GET.get('endDate')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend

    query = """
        SELECT
                COUNT(CASE WHEN type_sample = 'CKS' THEN 1 END) +
                COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_GC' THEN 1 END) AS "GC",
                COUNT(CASE WHEN type_sample = 'PDS' THEN 1 END) +
                COUNT(CASE WHEN type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) +
                COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS "QA",
                COUNT(CASE WHEN type_sample = 'HOS' THEN 1 END) AS "HOS",
                COUNT(CASE WHEN type_sample = 'ROS' THEN 1 END) AS "ROS"
            FROM sample_type_count
            WHERE tgl_produksi BETWEEN %s AND %s   
    """

    # Define the parameters for the query
    params = [start_date, end_date]

    # Execute the query with parameters
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
            # width=320,
            height=360,
            template="plotly_dark" if theme == "dark" else "plotly_white",
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    # Load data
    gc  = df['GC'][0]
    qa  = df['QA'][0]
    hos = df['HOS'][0]
    ros = df['ROS'][0]

    x_data = [ros, hos, qa, gc]
    y_data = ['ROS', 'HOS', 'QA', 'GC']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=x_data,
        y=y_data,
        orientation='h',
        text=x_data, 
        texttemplate='%{text:.0f}'
    ))

    fig.update_layout(
        title=f'Data : {start_date} to {end_date}',
        title_font=dict(size=14),
        margin=dict(l=40, r=25, t=90, b=40), 
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        
        xaxis=dict(
            title_font=dict(size=12),
            tickvals=[0, max(x_data)],
        ),
        bargap=0.2, 
        height=360,
        template="plotly_dark" if theme == "dark" else "plotly_white",
    )
    
    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True})
    return JsonResponse({'plot_div': plot_div})

@login_required
def donutTypeByWeek(request):
    params     = []
    start_date = request.GET.get('startDate')
    end_date   = request.GET.get('endDate')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend

    query = """
            SELECT
                COUNT(CASE WHEN type_sample = 'CKS' THEN 1 END) +
                COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_GC' THEN 1 END) AS "GC",
                COUNT(CASE WHEN type_sample = 'PDS' THEN 1 END) +
                COUNT(CASE WHEN type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) +
                COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS "QA",
                COUNT(CASE WHEN type_sample = 'HOS' THEN 1 END) AS "HOS",
                COUNT(CASE WHEN type_sample = 'ROS' THEN 1 END) AS "ROS"
            FROM sample_type_count
            WHERE tgl_produksi BETWEEN %s AND %s                                          
        """
    # Define the parameters for the query
    params = [start_date, end_date]
    # df = pd.read_sql_query(query, connection)
    # Execute the query with parameters
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
            # width=320,
            height=360,
            template="plotly_dark" if theme == "dark" else "plotly_white",
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    # Load data
    gc  = df['GC'][0]
    qa  = df['QA'][0]
    hos = df['HOS'][0]
    ros = df['ROS'][0]

    values  = [ros, hos, qa, gc]
    labels = ['ROS', 'HOS', 'QA', 'GC']
    
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        # text=x_data, 
        # texttemplate='%{text:.0f}'
        labels=labels, 
        values=values, 
        hole=.5
    ))

    fig.update_layout(
        title=f'Data : {start_date} to {end_date}',
        title_font=dict(size=14),
        margin=dict(l=40, r=25, t=90, b=40), 
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
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
def chartGcByWeek(request):
    params     = []
    start_date = request.GET.get('startDate')
    end_date   = request.GET.get('endDate')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend

    query = """
            SELECT
                tgl_produksi,
                COUNT(CASE WHEN type_sample = 'CKS' THEN 1 END)  AS CKS,
                COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_GC' THEN 1 END) AS SPC
            FROM sample_type_count
            WHERE tgl_produksi BETWEEN %s AND %s 
            GROUP BY  tgl_produksi
            ORDER BY  tgl_produksi ASC;                                      
    """
    params = [start_date, end_date]
    # df = pd.read_sql_query(query, connection)
    df = pd.read_sql_query(query, connections['kqms_db'],params=params)

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
            # width=320,
            height=360,
            template="plotly_dark" if theme == "dark" else "plotly_white",
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    # Load data
    CKS  = df['CKS'].tolist()
    SPC  = df['SPC'].tolist()
    x    = df['tgl_produksi'].tolist()
    
    fig = go.Figure()
    # Warna untuk masing-masing trace
    colors = {
        'SPC'    : '#ffa51e',
        'CKS'    : '#bae118',
        'Others' : '#d68000',
    }
    fig.add_trace(go.Bar(
        x=x,
        y=SPC,
        text=SPC, 
        name="SPC",
        texttemplate='%{text:.0f}',
        marker=dict(color=colors['CKS']),
    ))

    fig.add_trace(go.Bar(
        x=x,
        y=CKS,
        text=CKS, 
        name="CKS",
        texttemplate='%{text:.0f}',
        marker=dict(color=colors['SPC']),
    ))

    fig.update_layout(
        title=f'Data GC : {start_date} to {end_date}',
        title_font=dict(size=14),
        margin=dict(l=40, r=25, t=50, b=30), 
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        # legend=dict(orientation="h"),
        barmode='stack',
        xaxis=dict(
            title_font=dict(size=12),
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
def chartQaByWeek(request):
    params     = []
    start_date = request.GET.get('startDate')
    end_date   = request.GET.get('endDate')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend

    query = """
            SELECT
                tgl_produksi,
                COUNT(CASE WHEN type_sample = 'PDS' THEN 1 END) AS PDS,
                COUNT(CASE WHEN type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) AS QAQC,
                COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS SPC_QA
            FROM sample_type_count
            WHERE tgl_produksi BETWEEN %s AND %s     
            GROUP BY  tgl_produksi
            ORDER BY  tgl_produksi ASC;                                      
    """

    params = [start_date, end_date]
    # df = pd.read_sql_query(query, connection)
    df = pd.read_sql_query(query, connections['kqms_db'],params=params)

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
            # width=320,
            height=360,
            template="plotly_dark" if theme == "dark" else "plotly_white",
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    # Load data
    PDS     = df['PDS'].tolist()
    QAQC    = df['QAQC'].tolist()
    SPC_QA  = df['SPC_QA'].tolist()
    x       = df['tgl_produksi'].tolist()
    
    fig = go.Figure()

     # Warna untuk masing-masing trace
    colors = {
        'PDS' : '#92cd08',
        'QAQC': '#edda0c',
        'SPC' : '#d68000',
    }
    
    fig.add_trace(go.Bar(
        x=x,
        y=PDS,
        text=PDS, 
        name="Production",
        texttemplate='%{text:.0f}',
        marker=dict(color=colors['PDS']),
    ))

    fig.add_trace(go.Bar(
        x=x,
        y=QAQC,
        text=QAQC, 
        name="QAQC",
        texttemplate='%{text:.0f}',
        marker=dict(color=colors['QAQC']),
    ))


    fig.add_trace(go.Bar(
        x=x,
        y=SPC_QA,
        text=SPC_QA, 
        name="Special Check",
        texttemplate='%{text:.0f}',
        marker=dict(color=colors['SPC']),
    ))

  
   

    fig.update_layout(
        title=f'Data QAQC : {start_date} to {end_date}',
        title_font=dict(size=14),
        margin=dict(l=40, r=25, t=90, b=40), 
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
          barmode='stack',
        xaxis=dict(
            title_font=dict(size=12),
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
def chartSaleByWeek(request):
    params     = []
    start_date = request.GET.get('startDate')
    end_date   = request.GET.get('endDate')
    theme = request.GET.get("theme", "light")  # ← tangkap theme dari frontend

    query = """
            SELECT
                tgl_produksi,
                COUNT(CASE WHEN type_sample = 'HOS' THEN 1 END) AS HOS,
                COUNT(CASE WHEN type_sample = 'ROS' THEN 1 END) AS ROS
            FROM sample_type_count
            WHERE tgl_produksi BETWEEN %s AND %s    
            GROUP BY  tgl_produksi
            ORDER BY  tgl_produksi ASC;                                      
    """

    params = [start_date, end_date]
    # df = pd.read_sql_query(query, connection)
    df = pd.read_sql_query(query, connections['kqms_db'],params=params)

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
            # width=320,
            height=360,
            template="plotly_dark" if theme == "dark" else "plotly_white",
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
    # Load data
    HOS  = df['HOS'].tolist()
    ROS  = df['ROS'].tolist()
    x    = df['tgl_produksi'].tolist()
    
    fig = go.Figure()

     # Warna untuk masing-masing trace
    colors = {
        'ROS': '#95b4be',
        'HOS': '#bea895'
    }
    
    fig.add_trace(go.Bar(
        x=x,
        y=ROS,
        text=ROS, 
        name="ROS",
        texttemplate='%{text:.0f}',
        marker=dict(color=colors['ROS']),
    ))

    fig.add_trace(go.Bar(
        x=x,
        y=HOS,
        text=HOS, 
        name="HOS",
        texttemplate='%{text:.0f}',
        marker=dict(color=colors['HOS']),
    ))


    fig.update_layout(
        title=f'Data Sale : {start_date} to {end_date}',
        title_font=dict(size=14),
        margin=dict(l=40, r=25, t=90, b=40), 
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
          barmode='stack',
        xaxis=dict(
            title_font=dict(size=12),
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
def getSampleOrdersByWeeks(request):
    params     = []
    start_date = request.GET.get('startDate')
    end_date   = request.GET.get('endDate')

    sql_query = """
        SELECT
            tgl_produksi,
            COUNT(CASE WHEN type_sample = 'CKS' THEN 1 END) AS CKS,
            COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_GC' THEN 1 END) AS SPC,
            COUNT(CASE WHEN type_sample = 'PDS' THEN 1 END) AS PDS,
            COUNT(CASE WHEN type_sample = 'QAQC' AND sample_method IN ('CRM', 'DUP_PDS') THEN 1 END) AS QAQC,
            COUNT(CASE WHEN type_sample = 'SPC' AND sample_method = 'SPC_QA' THEN 1 END) AS SPC_QA,
            COUNT(CASE WHEN type_sample = 'HOS' THEN 1 END) AS HOS,
            COUNT(CASE WHEN type_sample = 'ROS' THEN 1 END) AS ROS
        FROM sample_type_count
    """

    if start_date and end_date:
        sql_query += " WHERE tgl_produksi BETWEEN %s AND %s"
        params.extend([start_date, end_date])

    sql_query += """
        GROUP BY tgl_produksi
        ORDER BY tgl_produksi ASC
    """

    # Execute the query with parameters
    with connections['kqms_db'].cursor() as cursor:
        cursor.execute(sql_query,params)
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



