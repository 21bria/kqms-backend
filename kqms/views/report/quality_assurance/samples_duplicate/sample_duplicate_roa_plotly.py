from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connections,DatabaseError
from django.db import connection
import logging
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
pio.templates
from scipy.stats import linregress
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)


@login_required
def scatterPlotRoa(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
    }

    return render(request, 'admin-mgoqa/report-qa/scatter-duplicated-roa.html',context)

# plotly | Graphing Libraries
@login_required
def scatter_plotly_ni_roa(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    theme  = request.GET.get('theme','light')
    
    if start_date and end_date:
        query = f"""
        SELECT
            ni,
            ni_ori
        FROM sample_duplicated_roa
        WHERE ni_ori IS NOT NULL
        AND release_date BETWEEN '{start_date}' AND '{end_date}'
        """
        # df = pd.read_sql_query(query, connection)
        try:
            # Use the correct database connection
            with connections['kqms_db'].cursor() as cursor:
                # Execute the query using Pandas
                df = pd.read_sql_query(query, connections['kqms_db'])
            if df.empty:
                fig = go.Figure()
                fig.update_layout(
                    xaxis={"visible": False},
                    yaxis={"visible": False},
                    font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white',
                    annotations=[
                        {
                            "text": "No matching data found",
                            "xref": "paper",
                            "yref": "paper",
                            "showarrow": False,
                            "font": {"size": 16}
                        }
                    ]
                )
                plot_div = fig.to_html(full_html=False)
                return JsonResponse({'plot_div': plot_div})
        except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return JsonResponse({'error': str(e)}, status=500)
            
        # Menghitung nilai maksimum dan minimum
        ni_max     = df['ni'].max()
        ni_ori_max = df['ni_ori'].max()
        center_ni  = max(ni_max, ni_ori_max)
        upper_ni   = round(center_ni + (center_ni * 0.1), 3)
        lower_ni   = round(center_ni - (center_ni * 0.1), 3)
        
        # Menghitung regresi linear antara kolom 'ni' dan 'ni_ori'
        slope, intercept, r_value, p_value, std_err = linregress(df['ni'], df['ni_ori'])

        # Menghitung nilai R^2
        r_squared = float(r_value) ** 2

        print("Nilai R^2:", r_squared)

        # Membuat scatter plot
        fig = go.Figure()
        
        # Menambahkan garis untuk Upper Line
        fig.add_trace(go.Scatter(
            x=[0, center_ni],
            y=[0, upper_ni],
            # mode='lines',
             type='scatter',
            name='Upper',
            line=dict(color='#ff7c7c')
        ))

        # Menambahkan garis untuk Centre Line
        fig.add_trace(go.Scatter(
            x=[0, center_ni],
            y=[0, center_ni],
            # mode='lines',
            type='scatter',
            name='Centre',
           line=dict(color='#ffe16c')
        ))

        # Menambahkan garis untuk Lower Line
        fig.add_trace(go.Scatter(
            x=[0, center_ni],
            y=[0, lower_ni],
            # mode='lines',
            type='scatter',
            name='Lower',
            line=dict(
                # color='Blue'
                color='#88b1b8'
                )
        ))

        values = df['ni_ori']
      # Menambahkan scatter plot untuk kolom ni
        fig.add_trace(go.Scatter(
            x=df['ni'],
            y=df['ni_ori'],
            mode='markers',
            # marker= dict(size= 8 ),
            marker=dict(
                color=values,
                colorbar=dict(title=""),
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
                range=[0, 2.7],
                title='Duplicated',
                tickmode='linear',
                tick0=0.0,
                dtick= 0.5,
                tickformat='.2f',
                showgrid=False,  # Menampilkan grid pada sumbu x
            ),
            yaxis=dict(
                type='linear',
                range=[0, 2.7],
                title='Original',
                tickmode='linear',
                tick0=0.0,
                dtick= 0.5,
                tickformat='.2f',
                showgrid=True,  # Menampilkan grid pada sumbu x
                gridcolor='rgba(0,0,0,0.07)'  # Warna grid pada sumbu y
            ),
            title='Plot Ni Original vs Duplicate',
            
            hovermode='closest',
            plot_bgcolor='rgba(201,201,201,0.08)',  # Mengatur background plot 

             legend= dict(
                yref    = 'paper',
                font    = dict(
                family  = 'Arial, sans-serif',
                color   = 'grey'),
                yanchor ="top",
                y       =0.99,
                xanchor ="left",
                x       =0.01,
            ),
            font     = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template  = 'plotly_dark' if theme == 'dark' else 'plotly_white',
        )

        # Menambahkan anotasi untuk menampilkan nilai R^2
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.5, y=1.12,
            showarrow=False,
            text=f'R-squared: {r_squared:.2f}',
            font=dict(
                size=12,
                # color="black"
            )
        )

        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    else:
        #return JsonResponse({'plot_div': None})
        # Tampilan awal ketika tidak ada filter yang diterapkan
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white', # Mengatur background plot menjadi transparan
            annotations=[
                {
                    "text": "No data available",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 16}
                }
            ]
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})

@login_required
def scatter_plotly_co_roa(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    theme  = request.GET.get('theme','light')
    
    if start_date and end_date:
        query = f"""
         SELECT
            co,
            co_ori
        FROM sample_duplicated_roa
        WHERE co_ori IS NOT NULL
        AND release_date BETWEEN '{start_date}' AND '{end_date}'
        """
        try:
            # Use the correct database connection
            with connections['kqms_db'].cursor() as cursor:
                # Execute the query using Pandas
                df = pd.read_sql_query(query, connections['kqms_db'])
                if df.empty:
                        fig = go.Figure()
                        fig.update_layout(
                            xaxis={"visible": False},
                            yaxis={"visible": False},
                            font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white',
                            annotations=[
                                {
                                    "text": "No matching data found",
                                    "xref": "paper",
                                    "yref": "paper",
                                    "showarrow": False,
                                    "font": {"size": 16}
                                }
                            ]
                        )
                        plot_div = fig.to_html(full_html=False)
                        return JsonResponse({'plot_div': plot_div})
        except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        
        # Menghitung nilai maksimum dan minimum
        co_max = df['co'].max()
        co_ori_max = df['co_ori'].max()
        center_co = max(co_max, co_ori_max)
        upper_co = round(center_co + (center_co * 0.1), 3)
        lower_co = round(center_co - (center_co * 0.1), 3)
        
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['co'], df['co_ori'])
        r_squared = float(r_value) ** 2

        print("Nilai R^2:", r_squared)

        # Membuat scatter plot
        fig = go.Figure()
        
        # Menambahkan garis untuk Upper Line
        fig.add_trace(go.Scatter(
            x=[0, center_co],
            y=[0, upper_co],
            # mode='lines',
             type='scatter',
            name='Upper',
            line=dict(color='#ff7c7c')
        ))

        # Menambahkan garis untuk Centre Line
        fig.add_trace(go.Scatter(
            x=[0, center_co],
            y=[0, center_co],
            # mode='lines',
             type='scatter',
            name='Centre',
           line=dict(color='#ffe16c')
        ))

        # Menambahkan garis untuk Lower Line
        fig.add_trace(go.Scatter(
            x=[0, center_co],
            y=[0, lower_co],
            # mode='lines',
            type='scatter',
            name='Lower',
            line=dict(
                # color='Blue'
                color='#88b1b8'
                )
        ))

        values = df['co_ori']
      # Menambahkan scatter plot untuk kolom co
        fig.add_trace(go.Scatter(
            x=df['co'],
            y=df['co_ori'],
            mode='markers',
            # marker= dict(size= 8 ),
            marker=dict(
                color=values,
                colorbar=dict(title=""),
                colorscale="Aggrnyl",
                size=9, 
                line=dict(width=0.4, 
                color='white')),
            type='scatter',
            name='Co',
        ))

        fig.update_layout(
            xaxis=dict(
                type='linear',
                range=[0, 0.28],
                title='Duplicated',
                tickmode='linear',
                tick0=0.00,
                dtick= 0.05,
                tickformat='.2f',
                showgrid=False,  # Menampilkan grid pada sumbu x
                # gridcolor='rgba(0,0,0,0.1)'  # Warna grid pada sumbu y
                
            ),
            yaxis=dict(
                type='linear',
                range=[0, 0.28],
                title='Original',
                tickmode='linear',
                tick0=0.00,
                dtick= 0.05,
                tickformat='.2f',
                showgrid=True,  # Menampilkan grid pada sumbu x
                gridcolor='rgba(0,0,0,0.07)'  # Warna grid pada sumbu y
            ),
            title='Plot Co Original vs Duplicate',
            
            hovermode='closest',
            plot_bgcolor='rgba(201,201,201,0.08)',  # Mengatur background plot 

            legend= dict(
                yref= 'paper',
                font= dict(
                family= 'Arial, sans-serif',
                color= 'grey'),
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
        )

        # Menambahkan anotasi untuk menampilkan nilai R^2
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.5, 
            y=1.12,
            showarrow=False,
            text=f'R-squared: {r_squared:.2f}',
            font=dict(
                size=12,
                # color="black"
            )
        )

        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    else:
        #return JsonResponse({'plot_div': None})
        # Tampilan awal ketika tidak ada filter yang diterapkan
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white', # Mengatur background plot menjadi transparan
            annotations=[
                {
                    "text": "No data available",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                     "font": {"size": 16}
                }
            ]
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})

@login_required
def scatter_plotly_fe_roa(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    theme  = request.GET.get('theme','light')
    
    if start_date and end_date:
        query = f"""
         SELECT
            fe,
            fe_ori
        FROM sample_duplicated_roa
        WHERE fe_ori IS NOT NULL
        AND release_date BETWEEN '{start_date}' AND '{end_date}'
        """
        with connections['kqms_db'].cursor() as cursor:
                # Execute the query using Pandas
                df = pd.read_sql_query(query, connections['kqms_db'])

        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white',
                annotations=[
                    {
                        "text": "No matching data found",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 16}
                    }
                ]
            )
            plot_div = fig.to_html(full_html=False)
            return JsonResponse({'plot_div': plot_div})
        
        # Menghitung nilai maksimum dan minimum
        fe_max = df['fe'].max()
        fe_ori_max = df['fe_ori'].max()
        center_fe = max(fe_max, fe_ori_max)
        upper_fe = round(center_fe + (center_fe * 0.1), 3)
        lower_fe = round(center_fe - (center_fe * 0.1), 3)
        
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['fe'], df['fe_ori'])
        r_squared = float(r_value) ** 2

        print("Nilai R^2:", r_squared)

        # Membuat scatter plot
        fig = go.Figure()
        
        # Menambahkan garis untuk Upper Line
        fig.add_trace(go.Scatter(
            x=[0, center_fe],
            y=[0, upper_fe],
            # mode='lines',
            type='scatter',
            name='Upper',
            line=dict(color='#ff7c7c')
        ))

        # Menambahkan garis untuk Centre Line
        fig.add_trace(go.Scatter(
            x=[0, center_fe],
            y=[0, center_fe],
            # mode='lines',
            type='scatter',
            name='Centre',
           line=dict(color='#ffe16c')
        ))

        # Menambahkan garis untuk Lower Line
        fig.add_trace(go.Scatter(
            x=[0, center_fe],
            y=[0, lower_fe],
            # mode='lines',
            type='scatter',
            name='Lower',
            line=dict(
                # color='Blue'
                color='#88b1b8'
                )
        ))
        values=df['fe_ori']
      # Menambahkan scatter plot untuk kolom co
        fig.add_trace(go.Scatter(
            x=df['fe'],
            y=df['fe_ori'],
            mode='markers',
            # marker= dict(size= 8 ),
            marker=dict(
                color=values,
                colorbar=dict(title=""),
                colorscale="Aggrnyl",
                size=9, 
                line=dict(width=0.4, 
                color='white')),
            type='scatter',
            name='Fe',
        ))

        fig.update_layout(
            xaxis=dict(
                type='linear',
                range=[0, 60],
                title='Duplicated',
                tickmode='linear',
                tick0=0.0,
                dtick= 11,
                tickformat='.0f',
                showgrid=False,  # Menampilkan grid pada sumbu x
                # gridcolor='rgba(0,0,0,0.1)'  # Warna grid pada sumbu y
                
            ),
            yaxis=dict(
                type='linear',
                range=[0, 60],
                title='Original',
                tickmode='linear',
                tick0=0.0,
                dtick= 11,
                tickformat='.0f',
                showgrid=True,  # Menampilkan grid pada sumbu x
                gridcolor='rgba(0,0,0,0.07)'  # Warna grid pada sumbu y
            ),
            title='Plot Fe Original vs Duplicate',
            
            hovermode='closest',
            plot_bgcolor='rgba(201,201,201,0.08)',  # Mengatur background plot menjadi transparan

            legend= dict(
                yref= 'paper',
                font= dict(
                family= 'Arial, sans-serif',
                color= 'grey'),
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            font     = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template  = 'plotly_dark' if theme == 'dark' else 'plotly_white',
        )

        # Menambahkan anotasi untuk menampilkan nilai R^2
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.5, y=1.12,
            showarrow=False,
            text=f'R-squared: {r_squared:.2f}',
            font=dict(
                size=12,
                # color="black"
            )
        )

        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    else:
        #return JsonResponse({'plot_div': None})
        # Tampilan awal ketika tidak ada filter yang diterapkan
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white', # Mengatur background plot menjadi transparan
            annotations=[
                {
                    "text": "No data available",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                     "font": {"size": 16}
                }
            ]
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})

@login_required    
def scatter_plotly_mgo_roa(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    theme  = request.GET.get('theme','light')
    
    if start_date and end_date:
        query = f"""
         SELECT
            mgo,
            mgo_ori
        FROM sample_duplicated_roa
        WHERE mgo_ori IS NOT NULL
        AND release_date BETWEEN '{start_date}' AND '{end_date}'
        """
        with connections['kqms_db'].cursor() as cursor:
                # Execute the query using Pandas
                df = pd.read_sql_query(query, connections['kqms_db'])

        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white',
                annotations=[
                    {
                        "text": "No matching data found",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 16}
                    }
                ]
            )
            plot_div = fig.to_html(full_html=False)
            return JsonResponse({'plot_div': plot_div})
        
        # Menghitung nilai maksimum dan minimum
        mgo_max = df['mgo'].max()
        mgo_ori_max = df['mgo_ori'].max()
        center_mgo = max(mgo_max, mgo_ori_max)
        upper_mgo = round(center_mgo + (center_mgo * 0.1), 3)
        lower_mgo = round(center_mgo - (center_mgo * 0.1), 3)
        
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['mgo'], df['mgo_ori'])
        r_squared = float(r_value) ** 2

        print("Nilai R^2:", r_squared)

        # Membuat scatter plot
        fig = go.Figure()
        
        # Menambahkan garis untuk Upper Line
        fig.add_trace(go.Scatter(
            x=[0, center_mgo],
            y=[0, upper_mgo],
            # mode='lines',
             type='scatter',
            name='Upper',
            line=dict(color='#ff7c7c')
        ))

        # Menambahkan garis untuk Centre Line
        fig.add_trace(go.Scatter(
            x=[0, center_mgo],
            y=[0, center_mgo],
            # mode='lines',
             type='scatter',
            name='Centre',
           line=dict(color='#ffe16c')
        ))

        # Menambahkan garis untuk Lower Line
        fig.add_trace(go.Scatter(
            x=[0, center_mgo],
            y=[0, lower_mgo],
            # mode='lines',
            type='scatter',
            name='Lower',
            line=dict(
                # color='Blue'
                color='#88b1b8'
                )
        ))

        values=df['mgo_ori']
      # Menambahkan scatter plot untuk kolom co
        fig.add_trace(go.Scatter(
            x=df['mgo'],
            y=df['mgo_ori'],
            mode='markers',
            # marker= dict(size= 8 ),
            marker=dict(
                color=values,
                colorbar=dict(title=""),
                colorscale="Aggrnyl",
                size=9, 
                line=dict(width=0.4, 
                color='white')),
            type='scatter',
            name='MgO',
        ))

        fig.update_layout(
            xaxis=dict(
                type='linear',
                range=[0, 29],
                title='Duplicated',
                tickmode='linear',
                tick0=0.0,
                dtick= 5,
                tickformat='.1f',
                showgrid=False,  # Menampilkan grid pada sumbu x
                # gridcolor='rgba(0,0,0,0.1)'  # Warna grid pada sumbu y
                
            ),
            yaxis=dict(
                type='linear',
                range=[0, 29],
                title='Original',
                tickmode='linear',
                tick0=0.0,
                dtick= 5,
                tickformat='.1f',
                showgrid=True,  # Menampilkan grid pada sumbu x
                gridcolor='rgba(0,0,0,0.07)'  # Warna grid pada sumbu y
            ),
            title='Plot MgO Original vs Duplicate',
            
            hovermode='closest',
            plot_bgcolor='rgba(201,201,201,0.08)',  # Mengatur background plot menjadi transparan

            legend= dict(
                yref= 'paper',
                font= dict(
                family= 'Arial, sans-serif',
                color= 'grey'),
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            font     = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template  = 'plotly_dark' if theme == 'dark' else 'plotly_white',
        )

        # Menambahkan anotasi untuk menampilkan nilai R^2
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.5, y=1.12,
            showarrow=False,
            text=f'R-squared: {r_squared:.2f}',
            font=dict(
                size=12,
                # color="black"
            )
        )

        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    else:
        #return JsonResponse({'plot_div': None})
        # Tampilan awal ketika tidak ada filter yang diterapkan
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white', # Mengatur background plot menjadi transparan
            annotations=[
                {
                    "text": "No data available",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                     "font": {"size": 16}
                }
            ]
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})

@login_required
def scatter_plotly_sio2_roa(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    theme  = request.GET.get('theme','light')
    
    if start_date and end_date:
        query = f"""
         SELECT
            sio2,
            sio2_ori
        FROM sample_duplicated_roa
        WHERE sio2_ori IS NOT NULL
        AND release_date BETWEEN '{start_date}' AND '{end_date}'
        """
        with connections['kqms_db'].cursor() as cursor:
                # Execute the query using Pandas
                df = pd.read_sql_query(query, connections['kqms_db'])

        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white',
                annotations=[
                    {
                        "text": "No matching data found",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 16}
                    }
                ]
            )
            plot_div = fig.to_html(full_html=False)
            return JsonResponse({'plot_div': plot_div})
        
        # Menghitung nilai maksimum dan minimum
        sio2_max = df['sio2'].max()
        sio2_ori_max = df['sio2_ori'].max()
        center_sio2 = max(sio2_max, sio2_ori_max)
        upper_sio2 = round(center_sio2 + (center_sio2 * 0.1), 3)
        lower_sio2 = round(center_sio2 - (center_sio2 * 0.1), 3)
        
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['sio2'], df['sio2_ori'])
        r_squared = float(r_value) ** 2

        print("Nilai R^2:", r_squared)

        # Membuat scatter plot
        fig = go.Figure()
        
        # Menambahkan garis untuk Upper Line
        fig.add_trace(go.Scatter(
            x=[0, center_sio2],
            y=[0, upper_sio2],
            # mode='lines',
             type='scatter',
            name='Upper',
            line=dict(color='#ff7c7c')
        ))

        # Menambahkan garis untuk Centre Line
        fig.add_trace(go.Scatter(
            x=[0, center_sio2],
            y=[0, center_sio2],
            # mode='lines',
             type='scatter',
            name='Centre',
           line=dict(color='#ffe16c')
        ))

        # Menambahkan garis untuk Lower Line
        fig.add_trace(go.Scatter(
            x=[0, center_sio2],
            y=[0, lower_sio2],
            # mode='lines',
            type='scatter',
            name='Lower',
            line=dict(
                # color='Blue'
                color='#88b1b8'
                )
        ))
        values=df['sio2_ori']
      # Menambahkan scatter plot untuk kolom co
        fig.add_trace(go.Scatter(
            x=df['sio2'],
            y=df['sio2_ori'],
            mode='markers',
            # marker= dict(size= 8 ),
            marker=dict(
                color=values,
                colorbar=dict(title=""),
                colorscale="Aggrnyl",
                size=9, 
                line=dict(width=0.4, 
                color='white')),
            type='scatter',
            name='SiO2',
        ))

        fig.update_layout(
            xaxis=dict(
                type='linear',
                range=[0, 55],
                title='Duplicated',
                tickmode='linear',
                tick0=0.0,
                dtick= 11,
                tickformat='.0f',
                showgrid=False,  # Menampilkan grid pada sumbu x
                # gridcolor='rgba(0,0,0,0.1)'  # Warna grid pada sumbu y
                
            ),
            yaxis=dict(
                type='linear',
                range=[0, 55],
                title='Original',
                tickmode='linear',
                tick0=0.0,
                dtick= 11,
                tickformat='.0f',
                showgrid=True,  # Menampilkan grid pada sumbu x
                gridcolor='rgba(0,0,0,0.07)'  # Warna grid pada sumbu y
            ),
            title='Plot SiO2 Original vs Duplicate',
            
            hovermode='closest',
            plot_bgcolor='rgba(201,201,201,0.08)',  # Mengatur background plot menjadi transparan

             legend= dict(
                yref= 'paper',
                font= dict(
                family= 'Arial, sans-serif',
                color= 'grey'),
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            font     = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template  = 'plotly_dark' if theme == 'dark' else 'plotly_white',
        )

        # Menambahkan anotasi untuk menampilkan nilai R^2
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.5, y=1.12,
            showarrow=False,
            text=f'R-squared: {r_squared:.2f}',
            font=dict(
                size=12,
                # color="black"
            )
        )

        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    else:
        #return JsonResponse({'plot_div': None})
        # Tampilan awal ketika tidak ada filter yang diterapkan
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white', # Mengatur background plot menjadi transparan
            annotations=[
                {
                    "text": "No data available",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                     "font": {"size": 16}
                }
            ]
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})

#By Apex Charts JS Librarie
@login_required
def scatterPlotNi(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    
    if start_date and end_date:
        query = """
        SELECT
            ni,
            ni_ori
        FROM sample_duplicated_roa
        WHERE ni_ori IS NOT NULL
        AND release_date >= %s AND release_date <= %s
        """
        params = (start_date, end_date)

        # df = pd.read_sql_query(query, connection, params=params)
    #    try:
            # Use the correct database connection
        df = pd.read_sql_query(query, connections['kqms_db'], params=params)
        
        # Menghitung nilai maksimum dan minimum
        ni_max = df['ni'].max()
        ni_ori_max = df['ni_ori'].max()
        center_ni = max(ni_max, ni_ori_max)
        upper_ni = round(center_ni + (center_ni * 0.1), 3)
        lower_ni = round(center_ni - (center_ni * 0.1), 3)
        
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['ni'], df['ni_ori'])
        r_squared = float(r_value) ** 2

        # Mengirimkan data dan nilai R-squared ke frontend
        response_data = {
            'scatter_data': df.to_dict('records'),
            'center_ni': center_ni,
            'upper_ni': upper_ni,
            'lower_ni': lower_ni,
            'r_squared': round(r_squared, 2)
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({'error': 'Invalid date range'})

@login_required   
def scatterPlotCo(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    
    if start_date and end_date:
        query = """
        SELECT
            co,
            co_ori
        FROM sample_duplicated_roa
        WHERE co_ori IS NOT NULL
        AND release_date >= %s AND release_date <= %s
        """
        params = (start_date, end_date)

        df = pd.read_sql_query(query, connections['kqms_db'], params=params)

        # Menghitung nilai maksimum dan minimum
        co_max = df['co'].max()
        co_ori_max = df['co_ori'].max()
        center_co = max(co_max, co_ori_max)
        upper_co = round(center_co + (center_co * 0.1), 3)
        lower_co = round(center_co - (center_co * 0.1), 3)
        
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['co'], df['co_ori'])
        r_squared = float(r_value) ** 2

        # Mengirimkan data dan nilai R-squared ke frontend
        response_data = {
            'scatter_data': df.to_dict('records'),
            'center_co': center_co,
            'upper_co': upper_co,
            'lower_co': lower_co,
            'r_squared': round(r_squared, 2)
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({'error': 'Invalid date range'})  

@login_required
def scatterPlotFe(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    
    if start_date and end_date:
        query = """
        SELECT
            fe,
            fe_ori
        FROM sample_duplicated_roa
        WHERE fe_ori IS NOT NULL
        AND release_date >= %s AND release_date <= %s
        """
        params = (start_date, end_date)
        df = pd.read_sql_query(query, connections['kqms_db'], params=params)
        
        # Menghitung nilai maksimum dan minimum
        fe_max = df['fe'].max()
        fe_ori_max = df['fe_ori'].max()
        center_fe = max(fe_max, fe_ori_max)
        upper_fe = round(center_fe + (center_fe * 0.1), 3)
        lower_fe = round(center_fe - (center_fe * 0.1), 3)
        
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['fe'], df['fe_ori'])
        r_squared = float(r_value) ** 2

        # Mengirimkan data dan nilai R-squared ke frontend
        response_data = {
            'scatter_data': df.to_dict('records'),
            'center_fe': center_fe,
            'upper_fe': upper_fe,
            'lower_fe': lower_fe,
            'r_squared': round(r_squared, 2)
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({'error': 'Invalid date range'})  

@login_required
def scatterPlotMgo(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    
    if start_date and end_date:
        query = """
        SELECT
            mgo,
            mgo_ori
        FROM sample_duplicated_roa
        WHERE mgo_ori IS NOT NULL
        AND release_date >= %s AND release_date <= %s
        """
        params = (start_date, end_date)

        df = pd.read_sql_query(query, connections['kqms_db'], params=params)
        
        # Menghitung nilai maksimum dan minimum
        mgo_max = df['mgo'].max()
        mgo_ori_max = df['mgo_ori'].max()
        center_mgo = max(mgo_max, mgo_ori_max)
        upper_mgo = round(center_mgo + (center_mgo * 0.1), 3)
        lower_mgo = round(center_mgo - (center_mgo * 0.1), 3)
        
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['mgo'], df['mgo_ori'])
        r_squared = float(r_value) ** 2

        # Mengirimkan data dan nilai R-squared ke frontend
        response_data = {
            'scatter_data': df.to_dict('records'),
            'center_mgo': center_mgo,
            'upper_mgo': upper_mgo,
            'lower_mgo': lower_mgo,
            'r_squared': round(r_squared, 2)
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({'error': 'Invalid date range'})  

@login_required    
def scatterPlotSio2(request):
    try:  
        start_date = request.GET.get('start_date')
        end_date   = request.GET.get('end_date')
        
        if start_date and end_date:
            query = """
            SELECT
                sio2,
                sio2_ori
            FROM sample_duplicated_roa
            WHERE sio2_ori IS NOT NULL
            AND release_date >= %s AND release_date <= %s
            """
            params = (start_date, end_date)
            df = pd.read_sql_query(query, connections['kqms_db'], params=params)
            
            # Menghitung nilai maksimum dan minimum
            sio2_max = df['sio2'].max()
            sio2_ori_max = df['sio2_ori'].max()
            center_sio2 = max(sio2_max, sio2_ori_max)
            upper_sio2 = round(center_sio2 + (center_sio2 * 0.1), 3)
            lower_sio2 = round(center_sio2 - (center_sio2 * 0.1), 3)
            
            # Menghitung regresi linear dan nilai R^2
            slope, intercept, r_value, p_value, std_err = linregress(df['sio2'], df['sio2_ori'])
            r_squared = float(r_value) ** 2

            # Mengirimkan data dan nilai R-squared ke frontend
            response_data = {
                'scatter_data': df.to_dict('records'),
                'center_sio2': center_sio2,
                'upper_sio2': upper_sio2,
                'lower_sio2': lower_sio2,
                'r_squared': round(r_squared, 2)
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'error': 'Invalid date range'})
        
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)

