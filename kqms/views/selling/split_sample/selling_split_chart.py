from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections
from django.utils.html import escape
import json,re
import pandas as pd
import plotly.graph_objs as go


# Fungsi untuk sanitasi input
def sanitize_input(value):
    if value is None:
        return None
    return escape(re.sub(r"[;'\"]", "", str(value)))

@login_required
def splitOfficialChartPage(request):
    return render(request, 'admin-selling/official/coa-chart.html')


@login_required
def niChartPlot(request):
    typeFilter   = request.GET.get('materialFilter')
    startDate    = request.GET.get('startDate')
    endDate      = request.GET.get('endDate')
    bulanFilter  = request.GET.get('bulanFilter')
    tahunFilter  = request.GET.get('tahunFilter')
    theme        = request.GET.get("theme", "light")

    # --- SQL Query ---
    sql_query = """
        SELECT 
            TRIM(t1.code_lot) AS code_lot,
            TRIM(t1.barge_code) AS barge_code,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
            COALESCE(SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS ni_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.ni, 0) AS ni_official,
            ABS(COALESCE(SUM(t1.tonnage) - t2.tonnage_official, 0)) AS tonnage_diff,
            COALESCE(((SUM(t1.tonnage * t1.ni) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.ni IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.ni) / NULLIF(t2.ni, 0) * 100, 0) AS ni_diff
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(ni), 0) AS ni,
                type_selling
            FROM sellings_official_view
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        WHERE 1=1
    """

    filters = []
    if startDate and endDate:
        filters.append(f"t1.date_barge_out BETWEEN '{startDate}' AND '{endDate}'")
    if typeFilter:
        filters.append(f"t1.sale_adjust = '{typeFilter}'")
    if bulanFilter and tahunFilter:
        filters.append(f"EXTRACT(MONTH FROM t1.date_barge_out) = {bulanFilter} AND EXTRACT(YEAR FROM t1.date_barge_out) = {tahunFilter}")
    elif tahunFilter:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {tahunFilter}")

    if filters:
        sql_query += " AND " + " AND ".join(filters)

    sql_query += """
        GROUP BY t1.code_lot, t1.barge_code,
                 t2.tonnage_official, t2.ni
        ORDER BY t1.code_lot ASC
    """

    # Ambil data ke DataFrame
    df = pd.read_sql_query(sql_query, connections['kqms_db'])

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(0,0,0,0)', 
            annotations=[{"text": "No matching data found", "xref": "paper", "yref": "paper", "showarrow": False}]
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})

    # --- Buat Chart ---
    x = df["code_lot"].tolist()
    barge_codes      = df["barge_code"].tolist()
    tonnage_split    = df["tonnage_split"].tolist()
    tonnage_official = df["tonnage_official"].tolist()
    ni_internal      = df["ni_split"].tolist()
    ni_official      = df["ni_official"].tolist()
    ni_diff          = df["ni_diff"].tolist()

    # satukan barge_code + tonnage_official ke dalam customdata
    customdata = list(zip(barge_codes,tonnage_split, tonnage_official))

    fig = go.Figure()

    # Bar Split
    fig.add_trace(go.Bar(
        x=x, y=ni_internal, name="Internal",
        marker_color="#1f77b4", 
        text=ni_internal,
        texttemplate='%{text:.2f}',  # ✅ tampilkan 2 desimal
        textposition="inside",
        textfont=dict(size=10),
        # textangle=-45   # ✅ miring ke kiri 45 derajat
        customdata=customdata,
        hovertemplate="<b>Lot:</b> %{x}<br>" +
                  "<b>Barge:</b> %{customdata}<br>" +
                  "<b>Ni Official:</b> %{y:.2f}<extra></extra>"
    ))

    # Bar Official
    fig.add_trace(go.Bar(
        x=x, y=ni_official, name="Official (COA)",
        marker_color="#ff7f0e",
        text=ni_official,
        texttemplate='%{text:.2f}', 
        textposition="inside",
        textfont=dict(size=10, color="white"),  # warna putih biar terbaca
        customdata=barge_codes,
        # customton=tonnage_official,
        hovertemplate="<b>Lot:</b> %{x}<br>" +
                  "<b>Barge:</b> %{customdata[0]}<br>" +
                  "<b>Ton:</b> %{customdata[1]:,.2f}<br>" +  # ambil elemen kedua (tonnage)
                  "<b>Ni Official:</b> %{y:.2f}<extra></extra>"
    ))

    # Line Ni Diff (%)
    fig.add_trace(go.Scatter(
        x=x, y=ni_diff, name="Ni Diff (%)",
        mode="lines+markers+text",
        yaxis="y2",
        marker=dict(color="red"),
        text=[f"{v:.2f}%" for v in ni_diff],
        textposition="top center",
        textfont=dict(size=9),
        customdata=barge_codes,
        hovertemplate="<b>Lot:</b> %{x}<br>" +
                  "<b>Barge:</b> %{customdata[0]}<br>" +
                  "<b>Ton:</b> %{customdata[1]:,.2f}<br>" +  # ambil elemen kedua (tonnage)
                  "<b>Ni Official:</b> %{y:.2f}<extra></extra>"
    ))

    fig.update_layout(
        title="Internal vs Official Comparison (Ni%)",
        title_font=dict(size=15),
        xaxis=dict(
            tickangle=-45,        # miringkan label lot
            showgrid=False,        # tampilkan grid vertikal
            gridcolor="lightgrey",# warna grid
            gridwidth=0.5         # ketebalan grid
        ),
        yaxis=dict(
            showgrid=True,
            zeroline=True, # garis nol
            zerolinewidth=1,
            zerolinecolor="lightgrey"
        ),
        yaxis2=dict(
            title="Ni Diff (%)",
            overlaying="y",
            side="right",
            showgrid=False # grid di sumbu kanan biasanya dimatikan
        ),
        margin=dict(l=40, r=40,), 
        barmode="group",
        height=420,
        showlegend=True,
        legend=dict(
                orientation='h',  
                y=1.0,          
                x=0.5,
                xanchor='center',
                yanchor='bottom',
                traceorder='normal'
                ),
        template="plotly_dark" if theme == "dark" else "plotly_white"
    )

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True})
    return JsonResponse({'plot_div': plot_div})

@login_required
def feChartPlot(request):
    typeFilter   = request.GET.get('materialFilter')
    startDate    = request.GET.get('startDate')
    endDate      = request.GET.get('endDate')
    bulanFilter  = request.GET.get('bulanFilter')
    tahunFilter  = request.GET.get('tahunFilter')
    theme        = request.GET.get("theme", "light")

    # --- SQL Query ---
    sql_query = """
        SELECT 
            TRIM(t1.code_lot) AS code_lot,
            TRIM(t1.barge_code) AS barge_code,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
            COALESCE(SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS fe_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.fe, 0) AS fe_official,
            ABS(COALESCE(SUM(t1.tonnage) - t2.tonnage_official, 0)) AS tonnage_diff,
            COALESCE(((SUM(t1.tonnage * t1.fe) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.fe IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.fe) / NULLIF(t2.fe, 0) * 100, 0) AS fe_diff
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(fe), 0) AS fe,
                type_selling
            FROM sellings_official_view
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        WHERE 1=1
    """

    filters = []
    if startDate and endDate:
        filters.append(f"t1.date_barge_out BETWEEN '{startDate}' AND '{endDate}'")
    if typeFilter:
        filters.append(f"t1.sale_adjust = '{typeFilter}'")
    if bulanFilter and tahunFilter:
        filters.append(f"EXTRACT(MONTH FROM t1.date_barge_out) = {bulanFilter} AND EXTRACT(YEAR FROM t1.date_barge_out) = {tahunFilter}")
    elif tahunFilter:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {tahunFilter}")

    if filters:
        sql_query += " AND " + " AND ".join(filters)

    sql_query += """
        GROUP BY t1.code_lot, t1.barge_code,
                 t2.tonnage_official, t2.fe
        ORDER BY t1.code_lot ASC
    """

    # Ambil data ke DataFrame
    df = pd.read_sql_query(sql_query, connections['kqms_db'])

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(0,0,0,0)', 
            annotations=[{"text": "No matching data found", "xref": "paper", "yref": "paper", "showarrow": False}]
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})

    # --- Buat Chart ---
    x = df["code_lot"].tolist()
    barge_codes = df["barge_code"].tolist()
    fe_internal = df["fe_split"].tolist()
    fe_official = df["fe_official"].tolist()
    fe_diff     = df["fe_diff"].tolist()

    fig = go.Figure()

    # Bar Split
    fig.add_trace(go.Bar(
        x=x, y=fe_internal, name="Internal",
        marker_color="#1f77b4", 
        text=fe_internal,
        texttemplate='%{text:.2f}',  # ✅ tampilkan 2 desimal
        textposition="inside",
        textfont=dict(size=10),
        # textangle=-45   # ✅ miring ke kiri 45 derajat
        customdata=barge_codes,  # ✅ bawa data barge_code
        hovertemplate="<b>Lot:</b> %{x}<br>" +
                  "<b>Barge:</b> %{customdata}<br>" +
                  "<b>Fe:</b> %{y:.2f}<extra></extra>"
    ))

    # Bar Official
    fig.add_trace(go.Bar(
        x=x, y=fe_official, name="Official (COA)",
        marker_color="#ff7f0e",
        text=fe_official,
        texttemplate='%{text:.2f}', 
        textposition="inside",
        textfont=dict(size=10, color="white"),
        customdata=barge_codes,
        hovertemplate="<b>Lot:</b> %{x}<br>" +
              "<b>Barge:</b> %{customdata}<br>" +
              "<b>Fe Official:</b> %{y:.2f}<extra></extra>"
    ))

    # Line Fe Diff (%)
    fig.add_trace(go.Scatter(
        x=x, y=fe_diff, name="Fe Diff (%)",
        mode="lines+markers+text",
        yaxis="y2",
        marker=dict(color="red"),
        text=[f"{v:.2f}%" for v in fe_diff],
        textposition="top center",
        textfont=dict(size=9),
        customdata=barge_codes,
        hovertemplate="<b>Lot:</b> %{x}<br>" +
              "<b>Barge:</b> %{customdata}<br>" +
              "<b>Diff:</b> %{y:.2f}%<extra></extra>"
    ))

    fig.update_layout(
        title="Internal vs Official Comparison (Fe%)",
        title_font=dict(size=15),
        xaxis=dict(
            tickangle=-45,        # miringkan label lot
            showgrid=False,        # tampilkan grid vertikal
            gridcolor="lightgrey",# warna grid
            gridwidth=0.5         # ketebalan grid
        ),
        yaxis=dict(
            showgrid=True,
            # gridcolor="lightgrey",
            zeroline=True, # garis nol
            zerolinewidth=1,
            zerolinecolor="lightgrey"
        ),
        yaxis2=dict(
            title="Fe Diff (%)",
            overlaying="y",
            side="right",
            showgrid=False # grid di sumbu kanan biasanya dimatikan
        ),
        margin=dict(l=40, r=40,), 
        barmode="group",
        height=420,
        showlegend=True,
        legend=dict(
                orientation='h',  
                y=1.0,          
                x=0.5,
                xanchor='center',
                yanchor='bottom',
                traceorder='normal'
                ),
        template="plotly_dark" if theme == "dark" else "plotly_white"
    )

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True})
    return JsonResponse({'plot_div': plot_div})

@login_required
def mgoChartPlot(request):
    typeFilter   = request.GET.get('materialFilter')
    startDate    = request.GET.get('startDate')
    endDate      = request.GET.get('endDate')
    bulanFilter  = request.GET.get('bulanFilter')
    tahunFilter  = request.GET.get('tahunFilter')
    theme        = request.GET.get("theme", "light")

    # --- SQL Query ---
    sql_query = """
        SELECT 
            TRIM(t1.code_lot) AS code_lot,
            TRIM(t1.barge_code) AS barge_code,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
            COALESCE(SUM(t1.tonnage * t1.mgo) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS mgo_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.mgo, 0) AS mgo_official,
            ABS(COALESCE(SUM(t1.tonnage) - t2.tonnage_official, 0)) AS tonnage_diff,
            COALESCE(((SUM(t1.tonnage * t1.mgo) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.mgo IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.mgo) / NULLIF(t2.mgo, 0) * 100, 0) AS mgo_diff
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(mgo), 0) AS mgo,
                type_selling
            FROM sellings_official_view
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        WHERE 1=1
    """

    filters = []
    if startDate and endDate:
        filters.append(f"t1.date_barge_out BETWEEN '{startDate}' AND '{endDate}'")
    if typeFilter:
        filters.append(f"t1.sale_adjust = '{typeFilter}'")
    if bulanFilter and tahunFilter:
        filters.append(f"EXTRACT(MONTH FROM t1.date_barge_out) = {bulanFilter} AND EXTRACT(YEAR FROM t1.date_barge_out) = {tahunFilter}")
    elif tahunFilter:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {tahunFilter}")

    if filters:
        sql_query += " AND " + " AND ".join(filters)

    sql_query += """
        GROUP BY t1.code_lot, t1.barge_code,
                 t2.tonnage_official, t2.mgo
        ORDER BY t1.code_lot ASC
    """

    # Ambil data ke DataFrame
    df = pd.read_sql_query(sql_query, connections['kqms_db'])

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(0,0,0,0)', 
            annotations=[{"text": "No matching data found", "xref": "paper", "yref": "paper", "showarrow": False}]
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})

    # --- Buat Chart ---
    x = df["code_lot"].tolist()
    barge_codes  = df["barge_code"].tolist()
    mgo_internal = df["mgo_split"].tolist()
    mgo_official = df["mgo_official"].tolist()
    mgo_diff     = df["mgo_diff"].tolist()

    fig = go.Figure()

    # Bar Split
    fig.add_trace(go.Bar(
        x=x, y=mgo_internal, name="Internal",
        marker_color="#1f77b4", 
        text=mgo_internal,
        texttemplate='%{text:.2f}',  # ✅ tampilkan 2 desimal
        textposition="inside",
        textfont=dict(size=10),
        customdata=barge_codes,
        hovertemplate="<b>Lot:</b> %{x}<br>" +
              "<b>Barge:</b> %{customdata}<br>" +
              "<b>MgO:</b> %{y:.2f}<extra></extra>"
    ))

    # Bar Official
    fig.add_trace(go.Bar(
        x=x, y=mgo_official, name="Official (COA)",
        marker_color="#ff7f0e",
        text=mgo_official,
        texttemplate='%{text:.2f}', 
        textposition="inside",
        textfont=dict(size=10, color="white"),
        customdata=barge_codes,
        hovertemplate="<b>Lot:</b> %{x}<br>" +
              "<b>Barge:</b> %{customdata}<br>" +
              "<b>MgO Official:</b> %{y:.2f}<extra></extra>"
    ))

    # Line Ni Diff (%)
    fig.add_trace(go.Scatter(
        x=x, y=mgo_diff, name="MgO Diff (%)",
        mode="lines+markers+text",
        yaxis="y2",
        marker=dict(color="red"),
        text=[f"{v:.2f}%" for v in mgo_diff],
        textposition="top center",
        textfont=dict(size=9),
        customdata=barge_codes,
        hovertemplate="<b>Lot:</b> %{x}<br>" +
              "<b>Barge:</b> %{customdata}<br>" +
              "<b>Diff:</b> %{y:.2f}%<extra></extra>"
    ))

    fig.update_layout(
        title="Internal vs Official Comparison (MgO%)",
        title_font=dict(size=15),
        xaxis=dict(
            tickangle=-45,        # miringkan label lot
            showgrid=False,        # tampilkan grid vertikal
            gridcolor="lightgrey",# warna grid
            gridwidth=0.5         # ketebalan grid
        ),
        yaxis=dict(
            showgrid=True,
            # gridcolor="lightgrey",
            zeroline=True, # garis nol
            zerolinewidth=1,
            zerolinecolor="lightgrey"
        ),
        yaxis2=dict(
            title="MgO Diff (%)",
            overlaying="y",
            side="right",
            showgrid=False # grid di sumbu kanan biasanya dimatikan
        ),
        margin=dict(l=40, r=40,), 
        barmode="group",
        height=420,
        showlegend=True,
        legend=dict(
                orientation='h',  
                y=1.0,          
                x=0.5,
                xanchor='center',
                yanchor='bottom',
                traceorder='normal'
                ),
        template="plotly_dark" if theme == "dark" else "plotly_white"
    )

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True})
    return JsonResponse({'plot_div': plot_div})

@login_required
def smChartPlot(request):
    typeFilter   = request.GET.get('materialFilter')
    startDate    = request.GET.get('startDate')
    endDate      = request.GET.get('endDate')
    bulanFilter  = request.GET.get('bulanFilter')
    tahunFilter  = request.GET.get('tahunFilter')
    theme        = request.GET.get("theme", "light")

    # --- SQL Query ---
    sql_query = """
        SELECT 
            TRIM(t1.code_lot) AS code_lot,
            TRIM(t1.barge_code) AS barge_code,
            COALESCE(SUM(t1.tonnage), 0) AS tonnage_split,              
            COALESCE(SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END),0), 0) AS sm_split,
            COALESCE(t2.tonnage_official, 0) AS tonnage_official,
            COALESCE(t2.sm, 0) AS sm_official,
            ABS(COALESCE(SUM(t1.tonnage) - t2.tonnage_official, 0)) AS tonnage_diff,
            COALESCE(((SUM(t1.tonnage * t1.sm) / NULLIF(SUM(CASE WHEN t1.sample_number IS NOT NULL AND t1.sm IS NOT NULL THEN t1.tonnage ELSE 0 END), 0)) - t2.sm) / NULLIF(t2.sm, 0) * 100, 0) AS sm_diff
        FROM details_selling_barge_split t1
        LEFT JOIN (
            SELECT 
                product_code,
                COALESCE(SUM(tonnage), 0) AS tonnage_official,
                COALESCE(SUM(sm), 0) AS sm,
                type_selling
            FROM sellings_official_view
            GROUP BY product_code, type_selling
        ) AS t2 ON t1.code_lot = t2.product_code
        WHERE 1=1
    """

    filters = []
    if startDate and endDate:
        filters.append(f"t1.date_barge_out BETWEEN '{startDate}' AND '{endDate}'")
    if typeFilter:
        filters.append(f"t1.sale_adjust = '{typeFilter}'")
    if bulanFilter and tahunFilter:
        filters.append(f"EXTRACT(MONTH FROM t1.date_barge_out) = {bulanFilter} AND EXTRACT(YEAR FROM t1.date_barge_out) = {tahunFilter}")
    elif tahunFilter:
        filters.append(f"EXTRACT(YEAR FROM t1.date_barge_out) = {tahunFilter}")

    if filters:
        sql_query += " AND " + " AND ".join(filters)

    sql_query += """
        GROUP BY t1.code_lot, t1.barge_code,
                 t2.tonnage_official, t2.sm
        ORDER BY t1.code_lot ASC
    """

    # Ambil data ke DataFrame
    df = pd.read_sql_query(sql_query, connections['kqms_db'])

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='rgba(0,0,0,0)', 
            annotations=[{"text": "No matching data found", "xref": "paper", "yref": "paper", "showarrow": False}]
        )
        plot_div = fig.to_html(full_html=False)
        return JsonResponse({'plot_div': plot_div})

    # --- Buat Chart ---
    x = df["code_lot"].tolist()
    barge_codes = df["barge_code"].tolist()
    sm_internal = df["sm_split"].tolist()
    sm_official = df["sm_official"].tolist()
    sm_diff     = df["sm_diff"].tolist()

    fig = go.Figure()

    # Bar Split
    fig.add_trace(go.Bar(
        x=x, y=sm_internal, name="Internal",
        marker_color="#1f77b4", 
        text=sm_internal,
        texttemplate='%{text:.2f}',  # ✅ tampilkan 2 desimal
        textposition="inside",
        textfont=dict(size=10),
        customdata=barge_codes,
        hovertemplate="<b>Lot:</b> %{x}<br>" +
              "<b>Barge:</b> %{customdata}<br>" +
              "<b>SM:</b> %{y:.2f}<extra></extra>"
    ))

    # Bar Official
    fig.add_trace(go.Bar(
        x=x, y=sm_official, name="Official (COA)",
        marker_color="#ff7f0e",
        text=sm_official,
        texttemplate='%{text:.2f}', 
        textposition="inside",
        textfont=dict(size=10, color="white"),
        customdata=barge_codes,
        hovertemplate="<b>Lot:</b> %{x}<br>" +
              "<b>Barge:</b> %{customdata}<br>" +
              "<b>SM Official:</b> %{y:.2f}<extra></extra>"
    ))

    # Line SM Diff (%)
    fig.add_trace(go.Scatter(
        x=x, y=sm_diff, name="SM Diff (%)",
        mode="lines+markers+text",
        yaxis="y2",
        marker=dict(color="red"),
        text=[f"{v:.2f}%" for v in sm_diff],
        textposition="top center",
        textfont=dict(size=9),
        customdata=barge_codes,
        hovertemplate="<b>Lot:</b> %{x}<br>" +
              "<b>Barge:</b> %{customdata}<br>" +
              "<b>Diff:</b> %{y:.2f}%<extra></extra>"
    ))

    fig.update_layout(
        title="Internal vs Official Comparison (SM%)",
        title_font=dict(size=15),
        xaxis=dict(
            tickangle=-45,        # miringkan label lot
            showgrid=False,        # tampilkan grid vertikal
            gridcolor="lightgrey",# warna grid
            gridwidth=0.5         # ketebalan grid
        ),
        yaxis=dict(
            showgrid=True,
            # gridcolor="lightgrey",
            zeroline=True, # garis nol
            zerolinewidth=1,
            zerolinecolor="lightgrey"
        ),
        yaxis2=dict(
            title="SM Diff (%)",
            overlaying="y",
            side="right",
            showgrid=False # grid di sumbu kanan biasanya dimatikan
        ),
        margin=dict(l=40, r=40,), 
        barmode="group",
        height=420,
        showlegend=True,
        legend=dict(
                orientation='h',  
                y=1.0,          
                x=0.5,
                xanchor='center',
                yanchor='bottom',
                traceorder='normal'
                ),
        template="plotly_dark" if theme == "dark" else "plotly_white"
        )

    plot_div = fig.to_html(full_html=False, config={
    'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'toggleSpikelines'],
    'responsive': True})
    return JsonResponse({'plot_div': plot_div})


