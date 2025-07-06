from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connections,DatabaseError
import logging
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio
pio.templates
from scipy.stats import linregress
from datetime import datetime, timedelta
from scipy.stats import linregress
logger = logging.getLogger(__name__)


@login_required
def scatter_plot_mral_roa(request):
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday())
    
    context = {
        'start_date': last_monday.strftime('%Y-%m-%d'),
        'end_date'  : today.strftime('%Y-%m-%d'),
    }

    # form = DateFilterForm(request.GET or None)
    return render(request, 'admin-mgoqa/report-qa/scatter-mral-roa.html',context)


@login_required
def scatterplotlyNi(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    theme      = request.GET.get('theme','light')
    
    if start_date and end_date:
        query = f"""
        SELECT
            ni_mral,
            ni_roa
        FROM 
            mral_roa_analyse
        WHERE tgl_deliver BETWEEN '{start_date}' AND '{end_date}'
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
                    # plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white',
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
        except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return JsonResponse({'error': str(e)}, status=500)
            
        # Menghitung nilai maksimum dan minimum
        ni_max      = df['ni_mral'].max()
        ni_roa_max  = df['ni_roa'].max()
        center_ni   = max(ni_max, ni_roa_max)
        upper_ni    = round(center_ni + (center_ni * 0.1), 3)
        lower_ni    = round(center_ni - (center_ni * 0.1), 3)
        
        # Drop rows with NaN values
        df = df.dropna()

        # Menghitung regresi linear antara kolom 'ni' dan 'ni_ori'
        slope, intercept, r_value, p_value, std_err = linregress(df['ni_mral'], df['ni_roa'])

        # Menghitung nilai R^2
        r_squared = float(r_value) ** 2
        # print("Nilai R^2:", r_squared)

        # Membuat scatter plot
        fig = go.Figure()
        
        # Menambahkan garis untuk Upper Line
        fig.add_trace(go.Scattergl(
            x=[0, center_ni],
            y=[0, upper_ni],
            # mode='lines',
             #type='scatter',
             name='Upper',
            line=dict(color='#ff7c7c')
        ))

        # Menambahkan garis untuk Centre Line
        fig.add_trace(go.Scattergl(
            x=[0, center_ni],
            y=[0, center_ni],
             #type='scatter',
             name='Centre',
             line=dict(color='#ffe16c')
        ))

        # Menambahkan garis untuk Lower Line
        fig.add_trace(go.Scattergl(
            x=[0, center_ni],
            y=[0, lower_ni],
            #type='scatter',
            name='Lower',
            line=dict(
                color='#88b1b8'
                )
        ))
        values = df['ni_mral']

      # Menambahkan scatter plot untuk kolom ni
        fig.add_trace(go.Scattergl(
            x=df['ni_mral'],
            y=df['ni_roa'],
            mode='markers',
            marker=dict(
                color=values,
                colorbar=dict(title=""),
                colorscale="Viridis",
                size=8, 
                symbol="diamond",
                line=dict(width=0.2, 
                # color='white'
                )
                ),
            #type='scatter',
            name='Ni',
        ))

        fig.update_layout(
            xaxis=dict(
                type='linear',
                range=[0, 3.0],
                title='MRAL',
                tickmode='linear',
                tick0=0.0,
                dtick= 0.7,
                tickformat='.2f',
                showgrid=False, 
                
            ),
            yaxis=dict(
                type='linear',
                range=[0, 3.0],
                title='ROA',
                tickmode='linear',
                tick0=0.0,
                dtick= 0.7,
                tickformat='.2f',
                showgrid=True,
                gridcolor='rgba(0,0,0,0.07)'  # Warna grid pada sumbu y
            ),
            title='Plot Ni MRAL vs ROA',
            
            hovermode='closest',
            # plot_bgcolor='rgba(201,201,201,0.08)',  # Mengatur background plot 

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
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(0,0,0,0)',  # Mengatur background plot menjadi transparan
            annotations=[
                {
                    "text": "No data available",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                     "font": {"size": 16}
                }
            ],
            font      = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template  = 'plotly_dark' if theme == 'dark' else 'plotly_white',
            
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})

@login_required
def scatterplotlyCo(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    theme      = request.GET.get('theme','light')
    
    if start_date and end_date:
        query = f"""
        SELECT
            co_mral,
            co_roa
        FROM 
            mral_roa_analyse
        WHERE tgl_deliver BETWEEN '{start_date}' AND '{end_date}'
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
                    # plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white',
                    annotations=[
                        {
                            "text": "No matching data found",
                            "xref": "paper",
                            "yref": "paper",
                            "showarrow": False,
                            "font": {"size": 14}
                        }
                    ],
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
        co_max = df['co_mral'].max()
        co_roa_max = df['co_roa'].max()
        center_co = max(co_max, co_roa_max)
        upper_co = round(center_co + (center_co * 0.1), 3)
        lower_co = round(center_co - (center_co * 0.1), 3)

        # Drop rows with NaN values
        df = df.dropna()
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['co_mral'], df['co_roa'])
        r_squared = float(r_value) ** 2

        # print("Nilai R^2:", r_squared)

        # Membuat scatter plot
        fig = go.Figure()
        
        # Menambahkan garis untuk Upper Line
        fig.add_trace(go.Scattergl(
            x=[0, center_co],
            y=[0, upper_co],
            # mode='lines',
            #  #type='scatter',
            name='Upper',
            line=dict(color='#ff7c7c')
        ))

        # Menambahkan garis untuk Centre Line
        fig.add_trace(go.Scattergl(
            x=[0, center_co],
            y=[0, center_co],
            # mode='lines',
            # #type='scatter',
            name='Centre',
           line=dict(color='#ffe16c')
        ))

        # Menambahkan garis untuk Lower Line
        fig.add_trace(go.Scattergl(
            x=[0, center_co],
            y=[0, lower_co],
            # mode='lines',
            # #type='scatter',
            name='Lower',
            line=dict(
                # color='Blue'
                color='#88b1b8'
                )
        ))
        
        values = df['co_mral']
       # Menambahkan scatter plot untuk kolom co
        fig.add_trace(go.Scattergl(
            x=df['co_mral'],
            y=df['co_roa'],
            mode='markers',
            # marker= dict(size= 8 ),
            marker=dict(
                # color= 'rgba(17, 157, 255,0.5)',
                color=values,
                colorbar=dict(
                    title=""
                ),
                colorscale="Viridis",
                size=8, 
                symbol="diamond",
                line=dict(width=0.2, 
                # color='DarkSlateGrey'
                )
                ),
            # #type='scatter',
            name='Co',
        ))

        fig.update_layout(
            xaxis=dict(
                type='linear',
                range=[0, 0.28],
                title='MRAL',
                tickmode='linear',
                tick0=0.00,
                dtick= 0.08,
                tickformat='.2f',
                showgrid=False,  # Menampilkan grid pada sumbu x
                # gridcolor='rgba(0,0,0,0.1)'  # Warna grid pada sumbu y
                
            ),
            yaxis=dict(
                type='linear',
                range=[0, 0.28],
                title='ROA',
                tickmode='linear',
                tick0=0.0,
                dtick= 0.08,
                tickformat='.2f',
                showgrid=True,  # Menampilkan grid pada sumbu x
                gridcolor='rgba(0,0,0,0.07)'  # Warna grid pada sumbu y
            ),
            title='Plot Co MRAL vs ROA',
            hovermode='closest',
            legend= dict(
                # y= 0.5,
                yref= 'paper',
                font= dict(
                family= 'Arial, sans-serif',
                # size= 20,
                color= 'grey',
                ),
                # orientation="h",
                # yanchor="bottom",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            font      = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template  = 'plotly_dark' if theme == 'dark' else 'plotly_white',
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
            plot_bgcolor='rgba(0,0,0,0)',  # Mengatur background plot menjadi transparan
            annotations=[
                {
                    "text": "No data available",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                     "font": {"size": 16}
                }
            ],
            font      = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template  = 'plotly_dark' if theme == 'dark' else 'plotly_white',
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})

@login_required
def scatterplotlyFe(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    theme      = request.GET.get('theme','light')
    
    if start_date and end_date:
        query = f"""
          SELECT
            fe_mral,
            fe_roa
        FROM 
            mral_roa_analyse
        WHERE 
            tgl_deliver BETWEEN '{start_date}' AND '{end_date}'
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
                    # plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white',
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
        except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        
        # Menghitung nilai maksimum dan minimum
        fe_max      = df['fe_mral'].max()
        fe_roa_max  = df['fe_roa'].max()
        center_fe   = max(fe_max, fe_roa_max)
        upper_fe    = round(center_fe + (center_fe * 0.1), 3)
        lower_fe    = round(center_fe - (center_fe * 0.1), 3)

        # Drop rows with NaN values
        df = df.dropna()
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['fe_mral'], df['fe_roa'])
        r_squared = float(r_value) ** 2

        # Membuat scatter plot
        fig = go.Figure()
        
        # Menambahkan garis untuk Upper Line
        fig.add_trace(go.Scattergl(
            x=[0, center_fe],
            y=[0, upper_fe],
            # mode='lines',
             #type='scatter',
            name='Upper',
            line=dict(color='#ff7c7c')
        ))

        # Menambahkan garis untuk Centre Line
        fig.add_trace(go.Scattergl(
            x=[0, center_fe],
            y=[0, center_fe],
            # mode='lines',
             #type='scatter',
            name='Centre',
           line=dict(color='#ffe16c')
        ))

        # Menambahkan garis untuk Lower Line
        fig.add_trace(go.Scattergl(
            x=[0, center_fe],
            y=[0, lower_fe],
            # mode='lines',
            #type='scatter',
            name='Lower',
            line=dict(
                # color='Blue'
                color='#88b1b8'
                )
        ))

        values = df['fe_mral']
      # Menambahkan scatter plot untuk kolom co
        fig.add_trace(go.Scattergl(
            x=df['fe_mral'],
            y=df['fe_roa'],
            mode='markers',
            # marker= dict(size= 8 ),
            marker=dict(
                # color= 'rgba(17, 157, 255,0.5)',
                color=values,
                colorbar=dict(
                    title=""
                ),
                colorscale="Viridis",
                size=8, 
                symbol="diamond",
                line=dict(width=0.2, 
                # color='white'
                )),
            #type='scatter',
            name='Fe',
        ))

        fig.update_layout(
            xaxis=dict(
                type='linear',
                range=[0, 65],
                title='MRAL',
                tickmode='linear',
                tick0=0.0,
                dtick= 7,
                tickformat='.0f',
                showgrid=False,  # Menampilkan grid pada sumbu x
                # gridcolor='rgba(0,0,0,0.1)'  # Warna grid pada sumbu y
                
            ),
            yaxis=dict(
                type='linear',
                range=[0, 65],
                title='ROA',
                tickmode='linear',
                tick0=0.0,
                dtick= 11,
                tickformat='.0f',
                showgrid=True,  # Menampilkan grid pada sumbu x
                gridcolor='rgba(0,0,0,0.07)'  # Warna grid pada sumbu y
            ),
            title='Plot Fe MRAL vs ROA',
            hovermode='closest',
            # plot_bgcolor='rgba(201,201,201,0.08)',  # Mengatur background plot menjadi transparan
            legend= dict(
                # y= 0.5,
                yref= 'paper',
                font= dict(
                family= 'Arial, sans-serif',
                # size= 20,
                color= 'grey',
                ),
                # orientation="h",
                # yanchor="bottom",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            font      = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
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
            plot_bgcolor='rgba(0,0,0,0)',  # Mengatur background plot menjadi transparan
            annotations=[
                {
                    "text": "No data available",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                     "font": {"size": 16}
                }
            ],
            font      = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template  = 'plotly_dark' if theme == 'dark' else 'plotly_white',
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
@login_required    
def scatterplotlyMgo(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    theme      = request.GET.get('theme', 'light')  # Default to 'light'
    
    if start_date and end_date:
        query = f"""
         SELECT
            mgo_mral,
            mgo_roa
        FROM 
            mral_roa_analyse
        WHERE 
            tgl_deliver BETWEEN '{start_date}' AND '{end_date}'
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
                    plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'plotly_white',
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
        except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        
        # Menghitung nilai maksimum dan minimum
        mgo_max     = df['mgo_mral'].max()
        mgo_roa_max = df['mgo_roa'].max()
        center_mgo  = max(mgo_max, mgo_roa_max)
        upper_mgo   = round(center_mgo + (center_mgo * 0.1), 3)
        lower_mgo   = round(center_mgo - (center_mgo * 0.1), 3)

        # Drop rows with NaN values
        df = df.dropna()
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['mgo_mral'], df['mgo_roa'])
        r_squared = float(r_value) ** 2

        # Membuat scatter plot
        fig = go.Figure()
        
        # Menambahkan garis untuk Upper Line
        fig.add_trace(go.Scattergl(
            x=[0, center_mgo],
            y=[0, upper_mgo],
            # mode='lines',
             #type='scatter',
            name='Upper',
            line=dict(color='#ff7c7c')
        ))

        # Menambahkan garis untuk Centre Line
        fig.add_trace(go.Scattergl(
            x=[0, center_mgo],
            y=[0, center_mgo],
            # mode='lines',
             #type='scatter',
            name='Centre',
           line=dict(color='#ffe16c')
        ))

        # Menambahkan garis untuk Lower Line
        fig.add_trace(go.Scattergl(
            x=[0, center_mgo],
            y=[0, lower_mgo],
            # mode='lines',
            #type='scatter',
            name='Lower',
            line=dict(
                # color='Blue'
                color='#88b1b8'
                )
        ))
        values = df['mgo_mral']
      # Menambahkan scatter plot untuk kolom co
        fig.add_trace(go.Scattergl(
            x=df['mgo_mral'],
            y=df['mgo_roa'],
            mode='markers',
            # marker= dict(size= 8 ),
            marker=dict(
                # color= 'rgba(17, 157, 255,0.5)',
                color=values,
                colorbar=dict(
                    title=""
                ),
                colorscale="Viridis",
                size=8, 
                symbol="diamond",
                line=dict(width=0.2, 
                # color='white'
                )),
            #type='scatter',
            name='MgO',
        ))

        fig.update_layout(
            xaxis=dict(
                type='linear',
                range=[0, 45],
                title='MRAL',
                tickmode='linear',
                tick0=0.0,
                dtick= 7,
                tickformat='.1f',
                showgrid=False,  # Menampilkan grid pada sumbu x
                # gridcolor='rgba(0,0,0,0.1)'  # Warna grid pada sumbu y
                
            ),
            yaxis=dict(
                type='linear',
                range=[0, 45],
                title='ROA',
                tickmode='linear',
                tick0=0.0,
                dtick= 7,
                tickformat='.1f',
                showgrid=True,  # Menampilkan grid pada sumbu x
                gridcolor='rgba(0,0,0,0.07)'  # Warna grid pada sumbu y
            ),
            title='Plot MgO MRAL vs ROA',
            
            hovermode='closest',
            # plot_bgcolor='rgba(201,201,201,0.08)',  # Mengatur background plot menjadi transparan

            legend= dict(
                # y= 0.5,
                yref= 'paper',
                font= dict(
                family= 'Arial, sans-serif',
                # size= 20,
                color= 'grey',
                ),
                # orientation="h",
                # yanchor="bottom",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            font      = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
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
            plot_bgcolor='rgba(0,0,0,0)',  # Mengatur background plot menjadi transparan
            annotations=[
                {
                    "text": "No data available",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                     "font": {"size": 16}
                }
            ],
            font      = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template  = 'plotly_dark' if theme == 'dark' else 'plotly_white',
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})
    
@login_required
def scatterplotlySio2(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    theme      = request.GET.get('theme', 'light')  # Default to 'light'
    
    if start_date and end_date:
        query = f"""
            SELECT
                sio2_mral,
                sio2_roa
            FROM 
                mral_roa_analyse
            WHERE 
                tgl_deliver BETWEEN '{start_date}' AND '{end_date}'
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
                    # plot_bgcolor='#0e1726' if theme == 'dark' else 'rgba(0,0,0,0)',
                    # paper_bgcolor='#FFFFFF' if theme == 'light' else '#0e1726',
                    # font=dict(color='#000000' if theme == 'light' else '#FFFFFF'),
                    template='plotly_dark' if theme == 'dark' else 'simple_white',
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
        except DatabaseError as e:
            logger.error(f"Database query failed: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        
        # Menghitung nilai maksimum dan minimum
        sio2_max = df['sio2_mral'].max()
        sio2_roa_max = df['sio2_roa'].max()
        center_sio2 = max(sio2_max, sio2_roa_max)
        upper_sio2 = round(center_sio2 + (center_sio2 * 0.1), 3)
        lower_sio2 = round(center_sio2 - (center_sio2 * 0.1), 3)

        # Drop rows with NaN values
        df = df.dropna()
        # Menghitung regresi linear dan nilai R^2
        slope, intercept, r_value, p_value, std_err = linregress(df['sio2_mral'], df['sio2_roa'])
        r_squared = float(r_value) ** 2

        # print("Nilai R^2:", r_squared)

        # Membuat scatter plot
        fig = go.Figure()
        
        # Menambahkan garis untuk Upper Line
        fig.add_trace(go.Scattergl(
            x=[0, center_sio2],
            y=[0, upper_sio2],
            # mode='lines',
             #type='scatter',
            name='Upper',
            line=dict(color='#ff7c7c')
        ))

        # Menambahkan garis untuk Centre Line
        fig.add_trace(go.Scattergl(
            x=[0, center_sio2],
            y=[0, center_sio2],
            # mode='lines',
             #type='scatter',
            name='Centre',
           line=dict(color='#ffe16c')
        ))

        # Menambahkan garis untuk Lower Line
        fig.add_trace(go.Scattergl(
            x=[0, center_sio2],
            y=[0, lower_sio2],
            # mode='lines',
            #type='scatter',
            name='Lower',
            line=dict(
                # color='Blue'
                color='#88b1b8'
                )
        ))
        values = df['sio2_mral']
      # Menambahkan scatter plot untuk kolom co
        fig.add_trace(go.Scattergl(
            x=df['sio2_mral'],
            y=df['sio2_roa'],
            mode='markers',
            # marker= dict(size= 8 ),
            marker=dict(
                # color= 'rgba(17, 157, 255,0.5)',
                color=values,
                colorbar=dict(
                    title=""
                ),
                colorscale="Viridis",
                size=8, 
                # opacity=0.8,
                symbol="diamond",
                line=dict(width=0.2, 
                # color='white'
                )),
            #type='scatter',
            name='SiO2',
        ))

        fig.update_layout(
            xaxis=dict(
                type='linear',
                range=[0, 60],
                title='MRAL',
                tickmode='linear',
                tick0=0.0,
                dtick= 7,
                tickformat='.0f',
                showgrid=False,  # Menampilkan grid pada sumbu x
                # gridcolor='rgba(0,0,0,0.1)'  # Warna grid pada sumbu y
                
            ),
            yaxis=dict(
                type='linear',
                range=[0, 60],
                title='ROA',
                tickmode='linear',
                tick0=0.0,
                dtick= 7,
                tickformat='.0f',
                showgrid=True,  # Menampilkan grid pada sumbu x
                gridcolor='rgba(0,0,0,0.07)'  # Warna grid pada sumbu y
            ),
            title='Plot SiO2 MRAL vs ROA',
            
            hovermode='closest',
            # plot_bgcolor='rgba(201,201,201,0.08)',  # Mengatur background plot menjadi transparan

            legend= dict(
                # y= 0.5,
                yref= 'paper',
                font= dict(
                family= 'Arial, sans-serif',
                # size= 20,
                color= 'grey',
                ),
                # orientation="h",
                # yanchor="bottom",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            # plot_bgcolor  ='rgba(201,201,201,0.08)' if theme == 'light' else '#0e1726',
            # paper_bgcolor ='#FFFFFF' if theme == 'light' else '#0e1726',
            font          = dict(color ='#000000' if theme == 'light' else '#FFFFFF'),
            template      = 'plotly_dark' if theme == 'dark' else 'plotly_white',
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
            plot_bgcolor='rgba(0,0,0,0)',  # Mengatur background plot menjadi transparan
            annotations=[
                {
                    "text": "No data available",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                     "font": {"size": 16}
                }
            ],
            
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})


#By Apex Charts  - Assay mral 
def scatterAnalysNi(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    
    if start_date and end_date:
        query = """
        SELECT
            ni_mral,
            ni_roa
        FROM 
            mral_roa_analyse
        WHERE 
             tgl_deliver >= %s AND tgl_deliver <= %s
        """
        params = (start_date, end_date)

        df = pd.read_sql_query(query, connections['kqms_db'], params=params)
        
        # Menghitung nilai maksimum dan minimum
        ni_max      = df['ni_mral'].max()
        ni_roa_max  = df['ni_roa'].max()
        center_ni   = max(ni_max, ni_roa_max)
        upper_ni    = round(center_ni + (center_ni * 0.1), 3)
        lower_ni    = round(center_ni - (center_ni * 0.1), 3)
        
        # Drop rows with NaN values
        df = df.dropna()

        # Check if df is not empty after dropping NaNs
        if not df.empty:
            # Perform linear regression
            slope, intercept, r_value, p_value, std_err = linregress(df['ni_mral'], df['ni_roa'])
            r_squared = float(r_value) ** 2
            
            # Continue with the rest of your code
            center_ni   = max(df['ni_mral'].max(), df['ni_roa'].max())
            upper_ni    = round(center_ni + (center_ni * 0.1), 3)
            lower_ni    = round(center_ni - (center_ni * 0.1), 3)

            # Construct response data
            response_data = {
                'scatter_data'  : df.to_dict('records'),
                'center_ni'     : center_ni,
                'upper_ni'      : upper_ni,
                'lower_ni'      : lower_ni,
                'r_squared'     : round(r_squared, 2)
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'error': 'Invalid date range or no valid data for regression'})
        
@login_required   
def scatterAnalyseCo(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    
    if start_date and end_date:
        query = """
        SELECT
            co_mral,
            co_roa
        FROM 
            mral_roa_analyse
        WHERE 
            tgl_deliver >= %s AND tgl_deliver <= %s
        """
        params = (start_date, end_date)

        df = pd.read_sql_query(query, connections['kqms_db'], params=params)

        # Menghitung nilai maksimum dan minimum
        co_max      = df['co_mral'].max()
        co_roa_max  = df['co_roa'].max()
        center_co   = max(co_max, co_roa_max)
        upper_co    = round(center_co + (center_co * 0.1), 3)
        lower_co    = round(center_co - (center_co * 0.1), 3)
        
        # Drop rows with NaN values
        df = df.dropna()

        # Check if df is not empty after dropping NaNs
        if not df.empty:
        # Menghitung regresi linear dan nilai R^2
            slope, intercept, r_value, p_value, std_err = linregress(df['co_mral'], df['co_roa'])
            r_squared = float(r_value) ** 2

        # Mengirimkan data dan nilai R-squared ke frontend
        response_data = {
            'scatter_data'  : df.to_dict('records'),
            'center_co'     : center_co,
            'upper_co'      : upper_co,
            'lower_co'      : lower_co,
            'r_squared'     : round(r_squared, 2)
        }
        return JsonResponse(response_data)
    else:
       return JsonResponse({'error': 'Invalid date range or no valid data for regression'})  

@login_required
def scatterAnalysFe(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    
    if start_date and end_date:
        query = """
         SELECT
            fe_mral,
            fe_roa
        FROM 
            mral_roa_analyse
        WHERE 
            tgl_deliver >= %s AND tgl_deliver <= %s
        """
        params = (start_date, end_date)
        df = pd.read_sql_query(query, connections['kqms_db'], params=params)
        
        # Menghitung nilai maksimum dan minimum
        fe_max      = df['fe_mral'].max()
        fe_roa_max  = df['fe_roa'].max()
        center_fe   = max(fe_max, fe_roa_max)
        upper_fe    = round(center_fe + (center_fe * 0.1), 3)
        lower_fe    = round(center_fe - (center_fe * 0.1), 3)
         # Drop rows with NaN values
        df = df.dropna()

        # Check if df is not empty after dropping NaNs
        if not df.empty:
            # Menghitung regresi linear dan nilai R^2
            slope, intercept, r_value, p_value, std_err = linregress(df['fe_mral'], df['fe_roa'])
            r_squared = float(r_value) ** 2

        # Mengirimkan data dan nilai R-squared ke frontend
        response_data = {
            'scatter_data': df.to_dict('records'),
            'center_fe'   : center_fe,
            'upper_fe'    : upper_fe,
            'lower_fe'    : lower_fe,
            'r_squared'   : round(r_squared, 2)
        }
        return JsonResponse(response_data)
    else:
       return JsonResponse({'error': 'Invalid date range or no valid data for regression'}) 
     
@login_required
def scatterAnalyseMgo(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')
    
    if start_date and end_date:
        query = """
        SELECT
            mgo_mral,
            mgo_roa
        FROM 
            mral_roa_analyse
        WHERE 
            tgl_deliver >= %s AND tgl_deliver <= %s
        """
        params = (start_date, end_date)

        df = pd.read_sql_query(query, connections['kqms_db'], params=params)
        
        # Menghitung nilai maksimum dan minimum
        mgo_max     = df['mgo_mral'].max()
        mgo_roa_max = df['mgo_roa'].max()
        center_mgo  = max(mgo_max, mgo_roa_max)
        upper_mgo   = round(center_mgo + (center_mgo * 0.1), 3)
        lower_mgo   = round(center_mgo - (center_mgo * 0.1), 3)

         # Drop rows with NaN values
        df = df.dropna()
        # Check if df is not empty after dropping NaNs
        if not df.empty:
        # Menghitung regresi linear dan nilai R^2
            slope, intercept, r_value, p_value, std_err = linregress(df['mgo_mral'], df['mgo_roa'])
            r_squared = float(r_value) ** 2

        # Mengirimkan data dan nilai R-squared ke frontend
        response_data = {
            'scatter_data'  : df.to_dict('records'),
            'center_mgo'    : center_mgo,
            'upper_mgo'     : upper_mgo,
            'lower_mgo'     : lower_mgo,
            'r_squared'     : round(r_squared, 2)
        }
        return JsonResponse(response_data)
    else:
       return JsonResponse({'error': 'Invalid date range or no valid data for regression'})  

@login_required    
def scatterAnalyseSio2(request):
    try:  
        start_date = request.GET.get('start_date')
        end_date   = request.GET.get('end_date')
        
        if start_date and end_date:
            query = """
            SELECT
                sio2_mral,
                sio2_roa
            FROM 
                mral_roa_analyse
            WHERE 
                tgl_deliver >= %s AND tgl_deliver <= %s
            """
            params = (start_date, end_date)
            df = pd.read_sql_query(query, connections['kqms_db'], params=params)
            
            # Menghitung nilai maksimum dan minimum
            sio2_max        = df['sio2_mral'].max()
            sio2_roa_max    = df['sio2_roa'].max()
            center_sio2     = max(sio2_max, sio2_roa_max)
            upper_sio2      = round(center_sio2 + (center_sio2 * 0.1), 3)
            lower_sio2      = round(center_sio2 - (center_sio2 * 0.1), 3)
            
             # Drop rows with NaN values
            df = df.dropna()

            # Check if df is not empty after dropping NaNs
            if not df.empty:
            # Menghitung regresi linear dan nilai R^2
                slope, intercept, r_value, p_value, std_err = linregress(df['sio2_mral'], df['sio2_roa'])
                r_squared = float(r_value) ** 2

            # Mengirimkan data dan nilai R-squared ke frontend
            response_data = {
                'scatter_data'  : df.to_dict('records'),
                'center_sio2'   : center_sio2,
                'upper_sio2'    : upper_sio2,
                'lower_sio2'    : lower_sio2,
                'r_squared'     : round(r_squared, 2)
            }
            return JsonResponse(response_data)
        else:
           return JsonResponse({'error': 'Invalid date range or no valid data for regression'})
        
    except DatabaseError as e:
        logger.error(f"Database query failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
