
# reports/services.py
from django.db import connections
from ....utils.db_utils import get_db_vendor
db_vendor = get_db_vendor('kqms_db')

def fetch_production_quality_year(year: int):
    query = """
        WITH bulan AS (
            SELECT TO_CHAR(gs::date, 'YYYY-MM') AS dt,
                   TO_CHAR(gs::date, 'FMMonth') AS bulan_label
            FROM generate_series(
                make_date(%s, 1, 1),
                make_date(%s, 12, 31),
                interval '1 month'
            ) gs
        ),
        actual AS (
            SELECT 
                TO_CHAR(op.tgl_production, 'YYYY-MM') AS dt,
                SUM(op.tonnage) AS prod_total,
                SUM(CASE WHEN m.nama_material = 'LIM' THEN op.tonnage ELSE 0 END) AS prod_lim,
                SUM(CASE WHEN m.nama_material = 'SAP' THEN op.tonnage ELSE 0 END) AS prod_sap
            FROM ore_productions op
            LEFT JOIN materials m ON m.id = op.id_material
            WHERE EXTRACT(YEAR FROM op.tgl_production) = %s
            GROUP BY TO_CHAR(op.tgl_production, 'YYYY-MM')
        )
        SELECT 
            b.dt,
            b.bulan_label,
            COALESCE(a.prod_total,0) AS prod_total,
            COALESCE(a.prod_lim,0)   AS prod_lim,
            COALESCE(a.prod_sap,0)   AS prod_sap
        FROM bulan b
        LEFT JOIN actual a ON b.dt = a.dt
        ORDER BY b.dt;
    """
    with connections['kqms_db'].cursor() as cur:
        cur.execute(query, [year, year, year])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    summary = {
        "total": sum(r["prod_total"] or 0 for r in rows),
        "lim":   sum(r["prod_lim"] or 0 for r in rows),
        "sap":   sum(r["prod_sap"] or 0 for r in rows),
    }
    return {"rows": rows, "summary": summary}

def fetch_production_grade_year(year: int):
    query = """
     WITH month_series AS (
        SELECT 
            date_trunc('month', gs)::date AS dt,
            TO_CHAR(gs, 'YYYY-MM') AS dt_key,
            TO_CHAR(gs, 'FMMonth') AS dt_label
        FROM generate_series(
            make_date(%s, 1, 1),
            make_date(%s, 12, 31),
            interval '1 month'
        ) gs
    ),
        prod AS (
            SELECT
                date_trunc('month', tgl_production)::date AS prod_month,
                TRIM(nama_material) AS nama_material,
                SUM(tonnage)::numeric AS total_ore,
                SUM(
                    CASE WHEN roa_ni IS NOT NULL AND sample_number IS NOT NULL
                    THEN tonnage ELSE 0 END
                )::numeric AS released,
                SUM(tonnage * roa_ni) AS sum_ton_ni,
                SUM(tonnage * roa_co) AS sum_ton_co,
                SUM(tonnage * roa_fe) AS sum_ton_fe,
                SUM(tonnage * roa_mgo) AS sum_ton_mgo,
                SUM(tonnage * roa_sio2) AS sum_ton_sio2,
                SUM(
                    CASE WHEN sample_number IS NOT NULL AND roa_ni IS NOT NULL
                    THEN tonnage ELSE 0 END
                )::numeric AS denom_grade
            FROM details_roa
            WHERE direct_sale = 'No'
            AND EXTRACT(YEAR FROM tgl_production) = %s
            GROUP BY 1, 2
        )
        SELECT
            ms.dt,
            TO_CHAR(ms.dt, 'Mon') AS bulan_label,
            p.nama_material,
            COALESCE(p.total_ore, 0) AS total_ore,
            COALESCE(p.released, 0) AS released_ore,

            -- NI
            to_char(
                CASE WHEN p.denom_grade > 0
                    THEN p.sum_ton_ni / p.denom_grade
                    ELSE 0 END,
                'FM999990.00'
            ) AS ni,

            -- CO
            to_char(
                CASE WHEN p.denom_grade > 0
                    THEN p.sum_ton_co / p.denom_grade
                    ELSE 0 END,
                'FM999990.00'
            ) AS co,

            -- FE
            to_char(
                CASE WHEN p.denom_grade > 0
                    THEN p.sum_ton_fe / p.denom_grade
                    ELSE 0 END,
                'FM999990.00'
            ) AS fe,

            -- MGO
            to_char(
                CASE WHEN p.denom_grade > 0
                    THEN p.sum_ton_mgo / p.denom_grade
                    ELSE 0 END,
                'FM999990.00'
            ) AS mgo,

            -- SIO2
            to_char(
                CASE WHEN p.denom_grade > 0
                    THEN p.sum_ton_sio2 / p.denom_grade
                    ELSE 0 END,
                'FM999990.00'
            ) AS sio2,

            -- SM
            to_char(
                CASE WHEN p.denom_grade > 0
                    AND (p.sum_ton_mgo / p.denom_grade) > 0
                    THEN (p.sum_ton_sio2 / p.denom_grade) /
                        ((p.sum_ton_mgo / p.denom_grade) + 0.000001)
                    ELSE 0 END,
                'FM999990.00'
            ) AS sm
        FROM month_series ms
        LEFT JOIN prod p ON ms.dt = p.prod_month
        ORDER BY ms.dt, p.nama_material;
    """

    with connections["kqms_db"].cursor() as cur:
        cur.execute(query, [year, year, year])
        grade_rows = [
            {
                "dt_key": r[0],
                "dt": r[1],
                "nama_material": r[2],
                "total_ore": float(r[3] or 0),
                "released_ore": float(r[4] or 0),
                "ni": r[5],
                "co": r[6],
                "fe": r[7],
                "mgo": r[8],
                "sio2": r[9],
                "sm": r[10],
            }
            for r in cur.fetchall()
        ]
    
    # === Summary per year
    summary = {
        "total": sum(r["total_ore"] for r in grade_rows),
        "lim":   sum(r["total_ore"] for r in grade_rows if r["nama_material"] == "LIM"),
        "sap":   sum(r["total_ore"] for r in grade_rows if r["nama_material"] == "SAP"),
    }

    return {"rows": grade_rows, "summary": summary}

def fetch_selling_year(year: int):
    query = """
       WITH bulan AS (
            SELECT 
                TO_CHAR(gs::date, 'YYYY-MM') AS dt,
                TO_CHAR(gs::date, 'FMMonth') AS bulan_label
            FROM generate_series(
                make_date(%s, 1, 1),
                make_date(%s, 12, 31),
                interval '1 month'
            ) gs
        ),
        actual AS (
            SELECT
                TO_CHAR(date_barge_out, 'YYYY-MM') AS dt,
                SUM(CASE WHEN sale_adjust = 'HPAL' THEN tonnage ELSE 0 END)::numeric AS lim,
                SUM(CASE WHEN sale_adjust = 'RKEF' THEN tonnage ELSE 0 END)::numeric AS sap,
                SUM(tonnage)::numeric AS total
            FROM ore_sellings_barging
            WHERE EXTRACT(YEAR FROM date_barge_out) = %s
            AND status_barging = 'Complete'
            GROUP BY TO_CHAR(date_barge_out, 'YYYY-MM')
        ),
        plan AS (
            SELECT
                TO_CHAR(plan_date, 'YYYY-MM') AS dt,
                SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END)::numeric AS lim,
                SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END)::numeric AS sap,
                SUM(tonnage_plan)::numeric AS total
            FROM ore_sellings_plan_barging
            WHERE EXTRACT(YEAR FROM plan_date) = %s
            GROUP BY TO_CHAR(plan_date, 'YYYY-MM')
        )
        SELECT 
            b.dt,
            COALESCE(a.lim,0)   AS actual_lim,
            COALESCE(a.sap,0)   AS actual_sap,
            COALESCE(a.total,0) AS actual_total,
            COALESCE(p.lim,0)   AS plan_lim,
            COALESCE(p.sap,0)   AS plan_sap,
            COALESCE(p.total,0) AS plan_total
        FROM bulan b
        LEFT JOIN actual a ON b.dt = a.dt
        LEFT JOIN plan p   ON b.dt = p.dt
        ORDER BY b.dt;
    """
    with connections['kqms_db'].cursor() as cur:
        cur.execute(query, [year, year, year, year])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    summary = {
        "actual_total": sum(r["actual_total"] or 0 for r in rows),
        "plan_total"  : sum(r["plan_total"] or 0 for r in rows),
        "lim_actual"  : sum(r["actual_lim"] or 0 for r in rows),
        "sap_actual"  : sum(r["actual_sap"] or 0 for r in rows),
        "lim_plan"    : sum(r["plan_lim"] or 0 for r in rows),
        "sap_plan"    : sum(r["plan_sap"] or 0 for r in rows),
    }
    return {"rows": rows, "summary": summary}

def fetch_barging_year(year: int):
    query = """
      WITH bulan AS (
            SELECT 
                TO_CHAR(gs::date, 'YYYY-MM') AS bulan_key,
                TO_CHAR(gs::date, 'FMMonth') AS bulan_label
            FROM generate_series(
                make_date(%s, 1, 1),   -- awal tahun
                make_date(%s, 12, 31), -- akhir tahun
                interval '1 month'
            ) gs
        ),
        detail AS (
            SELECT
                TO_CHAR(s.date_hauling, 'YYYY-MM') AS bulan_key,
                mb.barge_code,
                ROUND(SUM(s.tonnage)::numeric, 2) AS total,
                ROUND(SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)::numeric, 2) AS lim,
                ROUND(SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)::numeric, 2) AS sap
            FROM ore_sellings_barging s
            LEFT JOIN master_barge mb ON mb.id = s.barge_code
            LEFT JOIN materials m ON m.id = s.id_material
            WHERE EXTRACT(YEAR FROM s.date_hauling) = %s
            AND s.status_barging = 'Complete'
            GROUP BY TO_CHAR(s.date_hauling, 'YYYY-MM'), mb.barge_code
        ),
        plan AS (
            SELECT
                TO_CHAR(p.plan_date, 'YYYY-MM') AS bulan_key,
                ROUND(SUM(p.tonnage_plan)::numeric, 2) AS total_plan,
                ROUND(SUM(CASE WHEN p.type_ore = 'LIM' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS lim_plan,
                ROUND(SUM(CASE WHEN p.type_ore = 'SAP' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS sap_plan
            FROM ore_sellings_plan_barging p
            WHERE EXTRACT(YEAR FROM p.plan_date) = %s
            GROUP BY TO_CHAR(p.plan_date, 'YYYY-MM')
        )
        SELECT
            b.bulan_key  AS label,
            b.bulan_label AS bulan_label,
            ROUND(COALESCE(SUM(d.total), 0), 2)  AS actual_total,
            ROUND(COALESCE(SUM(d.lim), 0), 2)    AS actual_lim,
            ROUND(COALESCE(SUM(d.sap), 0), 2)    AS actual_sap,
            ROUND(COALESCE(p.total_plan, 0), 2)  AS plan_total,
            ROUND(COALESCE(p.lim_plan, 0), 2)    AS plan_lim,
            ROUND(COALESCE(p.sap_plan, 0), 2)    AS plan_sap,
            COALESCE(
                json_agg(
                    json_build_object(
                        'barge_code', d.barge_code,
                        'total', ROUND(d.total, 2),
                        'lim',   ROUND(d.lim, 2),
                        'sap',   ROUND(d.sap, 2)
                    )
                    ORDER BY d.barge_code
                ) FILTER (WHERE d.barge_code IS NOT NULL),
                '[]'
            ) AS summary_by_barge
        FROM bulan b
        LEFT JOIN detail d ON b.bulan_key = d.bulan_key
        LEFT JOIN plan p   ON b.bulan_key = p.bulan_key
        GROUP BY b.bulan_key, b.bulan_label, p.total_plan, p.lim_plan, p.sap_plan
        ORDER BY b.bulan_key;
    """
    with connections['kqms_db'].cursor() as cur:
        cur.execute(query, [year, year, year, year])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    summary = {
        "actual_total": sum(r["actual_total"] or 0 for r in rows),
        "plan_total"  : sum(r["plan_total"] or 0 for r in rows),
        "lim_actual"  : sum(r["actual_lim"] or 0 for r in rows),
        "sap_actual"  : sum(r["actual_sap"] or 0 for r in rows),
        "lim_plan"    : sum(r["plan_lim"] or 0 for r in rows),
        "sap_plan"    : sum(r["plan_sap"] or 0 for r in rows),
    }
    return {"rows": rows, "summary": summary}

def fetch_production_mining_year(year: int):
    query = """
        WITH bulan AS (
            SELECT TO_CHAR(gs::date, 'YYYY-MM') AS dt,
                   TO_CHAR(gs::date, 'FMMonth') AS bulan_label
            FROM generate_series(
                make_date(%s, 1, 1),
                make_date(%s, 12, 31),
                interval '1 month'
            ) gs
        ),
        prod AS (
            SELECT 
                TO_CHAR(date_production, 'YYYY-MM') AS dt,
                SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END)::numeric AS lim,
                SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END)::numeric AS sap,
                SUM(CASE WHEN nama_material = 'Waste' THEN tonnage ELSE 0 END)::numeric AS waste,
                SUM(CASE WHEN nama_material = 'Quarry' THEN tonnage ELSE 0 END)::numeric AS quarry,
                SUM(CASE WHEN nama_material = 'Top Soil' THEN tonnage ELSE 0 END)::numeric AS topsoil,
                SUM(CASE WHEN nama_material = 'OB' THEN tonnage ELSE 0 END)::numeric AS ob,
                SUM(CASE WHEN nama_material = 'Ballast' THEN tonnage ELSE 0 END)::numeric AS ballast,
                SUM(CASE WHEN nama_material = 'Biomass' THEN tonnage ELSE 0 END)::numeric AS biomass,
                SUM(tonnage)::numeric AS total
            FROM mine_productions
            WHERE EXTRACT(YEAR FROM date_production) = %s
            GROUP BY TO_CHAR(date_production, 'YYYY-MM')
        ),
        plan AS (
            SELECT
                TO_CHAR(date_plan, 'YYYY-MM') AS dt,
                SUM(
                    COALESCE(lim,0) + COALESCE(sap,0) + COALESCE(quarry,0) + 
                    COALESCE(topsoil,0) + COALESCE(ob,0) + COALESCE(ballast,0) +
                    COALESCE(biomass,0) + COALESCE(waste,0)
                )::numeric AS plan_total
            FROM plan_productions
            WHERE EXTRACT(YEAR FROM date_plan) = %s
            GROUP BY TO_CHAR(date_plan, 'YYYY-MM')
        )
        SELECT 
            b.dt,
            b.bulan_label,
            COALESCE(p.lim,0) AS lim,
            COALESCE(p.sap,0) AS sap,
            COALESCE(p.waste,0) AS waste,
            COALESCE(p.quarry,0) AS quarry,
            COALESCE(p.topsoil,0) AS topsoil,
            COALESCE(p.ob,0) AS ob,
            COALESCE(p.ballast,0) AS ballast,
            COALESCE(p.biomass,0) AS biomass,
            COALESCE(p.total,0) AS actual_total,
            COALESCE(pl.plan_total,0) AS plan_total
        FROM bulan b
        LEFT JOIN prod p ON b.dt = p.dt
        LEFT JOIN plan pl ON b.dt = pl.dt
        ORDER BY b.dt;
    """
    with connections['kqms_db'].cursor() as cur:  
        cur.execute(query, [year, year, year, year])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    summary = {
        "total":   sum(r["actual_total"] or 0 for r in rows),
        "plan":    sum(r["plan_total"] or 0 for r in rows),
        "lim":     sum(r["lim"] or 0 for r in rows),
        "sap":     sum(r["sap"] or 0 for r in rows),
        "waste":   sum(r["waste"] or 0 for r in rows),
        "quarry":  sum(r["quarry"] or 0 for r in rows),
        "topsoil": sum(r["topsoil"] or 0 for r in rows),
        "ob":      sum(r["ob"] or 0 for r in rows),
        "ballast": sum(r["ballast"] or 0 for r in rows),
        "biomass": sum(r["biomass"] or 0 for r in rows),
    }

    return {"rows": rows, "summary": summary}

def fetch_inventory_balance_year(year: int):
    query = """
      WITH bulan AS (
        SELECT
            TO_CHAR(gs::date, 'YYYY-MM') AS dt,
            TO_CHAR(gs::date, 'FMMonth') AS bulan_label
        FROM generate_series(
            make_date(%s, 1, 1),
            make_date(%s, 12, 1),
            interval '1 month'
        ) gs
    ),
    incoming AS (
        SELECT
            TO_CHAR(tgl_production, 'YYYY-MM') AS dt,

            -- RAW incoming
            SUM(tonnage) AS total_in,

            -- incoming untuk stock (exclude Finished)
            SUM(
                CASE
                    WHEN status_dome = 'Finished' THEN 0
                    ELSE tonnage
                END
            ) AS in_stock
        FROM ore_productions
        WHERE EXTRACT(YEAR FROM tgl_production) = %s
        GROUP BY TO_CHAR(tgl_production, 'YYYY-MM')
    ),
    outgoing AS (
        SELECT
            TO_CHAR(date_hauling, 'YYYY-MM') AS dt,

            -- RAW outgoing
            SUM(tonnage) AS total_out,

            -- outgoing untuk stock (exclude Finished)
            SUM(
                CASE
                    WHEN sale_dome = 'Finished' THEN 0
                    ELSE tonnage
                END
            ) AS out_stock
        FROM ore_sellings_barging
        WHERE EXTRACT(YEAR FROM date_hauling) = %s
        AND status_barging = 'Complete'
        GROUP BY TO_CHAR(date_hauling, 'YYYY-MM')
    ),

    saldo_awal AS (
        SELECT
            COALESCE((
                SELECT SUM(
                    CASE
                        WHEN status_dome = 'Finished' THEN 0
                        ELSE tonnage
                    END
                )
                FROM ore_productions
                WHERE tgl_production < make_date(%s, 1, 1)
            ), 0)
            -
            COALESCE((
                SELECT SUM(
                    CASE
                        WHEN sale_dome = 'Finished' THEN 0
                        ELSE tonnage
                    END
                )
                FROM ore_sellings_barging
                WHERE date_hauling < make_date(%s, 1, 1)
                AND status_barging = 'Complete'
            ), 0) AS opening_balance
    )
    SELECT
        b.dt,
        b.bulan_label,
        -- RAW movement (laporan)
        COALESCE(i.total_in, 0)  AS total_in,
        COALESCE(o.total_out, 0) AS total_out,
        -- saldo awal tahun
        sa.opening_balance,
        -- running stock bulanan
        sa.opening_balance
        + SUM(
                COALESCE(i.in_stock, 0)
            - COALESCE(o.out_stock, 0)
            ) OVER (
                ORDER BY b.dt
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS running_balance
    FROM bulan b
    LEFT JOIN incoming i ON b.dt = i.dt
    LEFT JOIN outgoing o ON b.dt = o.dt
    CROSS JOIN saldo_awal sa
    ORDER BY b.dt;
    """
    with connections['kqms_db'].cursor() as cur:
        cur.execute(query, [year, year, year, year, year, year])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    summary = {
        "opening_balance" : rows[0]["opening_balance"] if rows else 0,
        "total_in": sum(r["total_in"] or 0 for r in rows),
        "total_out": sum(r["total_out"] or 0 for r in rows),
        "closing_balance": rows[-1]["running_balance"] if rows else 0
    }

    return {"rows": rows, "summary": summary}

def fetch_inventory_dome_year(year: int):
    query = """
      WITH prod AS (
        SELECT
            TRIM(stockpile) AS stockpile,
            TRIM(pile_id) AS pile_id,
            TRIM(nama_material) AS nama_material,
            SUM(tonnage) AS total_ore,
            SUM(
                CASE
                    WHEN roa_ni IS NOT NULL AND sample_number IS NOT NULL THEN tonnage
                    ELSE 0
                END
            ) AS released,
            ROUND(COALESCE(SUM(tonnage * roa_ni) / NULLIF(SUM(
                CASE WHEN sample_number IS NOT NULL AND roa_ni IS NOT NULL THEN tonnage END
            ),0),0)::numeric,2) AS ni,
            ROUND(COALESCE(SUM(tonnage * roa_co) / NULLIF(SUM(
                CASE WHEN sample_number IS NOT NULL AND roa_co IS NOT NULL THEN tonnage END
            ),0),0)::numeric,2) AS co,
            ROUND(COALESCE(SUM(tonnage * roa_fe) / NULLIF(SUM(
                CASE WHEN sample_number IS NOT NULL AND roa_fe IS NOT NULL THEN tonnage END
            ),0),0)::numeric,2) AS fe,
            ROUND(COALESCE(SUM(tonnage * roa_mgo) / NULLIF(SUM(
                CASE WHEN sample_number IS NOT NULL AND roa_mgo IS NOT NULL THEN tonnage END
            ),0),0)::numeric,2) AS mgo,
            ROUND(COALESCE(SUM(tonnage * roa_sio2) / NULLIF(SUM(
                CASE WHEN sample_number IS NOT NULL AND roa_sio2 IS NOT NULL THEN tonnage END
            ),0),0)::numeric,2) AS sio2,
            ROUND(
                COALESCE(
                    (SUM(tonnage * roa_sio2) / NULLIF(SUM(
                        CASE WHEN sample_number IS NOT NULL AND roa_sio2 IS NOT NULL THEN tonnage END
                    ),0)) / 
                    (SUM(tonnage * roa_mgo) / NULLIF(SUM(
                        CASE WHEN sample_number IS NOT NULL AND roa_mgo IS NOT NULL THEN tonnage END
                    ),0) + 0.000001),
                    0
                )::numeric,2
            ) AS sm
        FROM details_roa
        WHERE 
          status_dome != 'Finished' AND 
          direct_sale = 'No'
          AND EXTRACT(YEAR FROM tgl_production) <= %s
        GROUP BY stockpile, pile_id, nama_material
    ),
    sell AS (
        SELECT
            TRIM(stockpile) AS stockpile,
            TRIM(dome)      AS pile_id,
            TRIM(material)  AS nama_material,
            SUM(tonnage)    AS tonnage
        FROM details_selling_barging
        WHERE EXTRACT(YEAR FROM date_barge_out) <= %s
        AND status_barging = 'Complete'
        GROUP BY stockpile, dome, material
    )
    SELECT 
        p.stockpile,
        p.pile_id,
        p.nama_material,
        p.total_ore,
        p.released,
        COALESCE(ROUND(SUM(
            CASE
                WHEN p.nama_material = 'LIM' AND s.nama_material = 'SAP' THEN s.tonnage
                WHEN p.nama_material = 'SAP' AND s.nama_material = 'LIM' THEN s.tonnage
                WHEN p.nama_material = s.nama_material THEN s.tonnage
                ELSE 0
            END
        )::numeric, 2), 0) AS total_selling,
        ROUND((
            p.total_ore - COALESCE(SUM(
                CASE
                    WHEN p.nama_material = 'LIM' AND s.nama_material = 'SAP' THEN s.tonnage
                    WHEN p.nama_material = 'SAP' AND s.nama_material = 'LIM' THEN s.tonnage
                    WHEN p.nama_material = s.nama_material THEN s.tonnage
                    ELSE 0
                END
            ),0)
        )::numeric, 2) AS balance,
        p.ni, p.co, p.fe, p.mgo, p.sio2, p.sm
    FROM prod p
    LEFT JOIN sell s 
      ON p.stockpile = s.stockpile 
     AND p.pile_id   = s.pile_id
    GROUP BY p.stockpile, p.pile_id, p.nama_material, 
             p.total_ore, p.released, 
             p.ni, p.co, p.fe, p.mgo, p.sio2, p.sm
    ORDER BY p.nama_material, p.stockpile;
    """
    with connections['kqms_db'].cursor() as cur:
        cur.execute(query, [year, year])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    return {"rows": rows}

def fetch_summary_to_year(year: int):
    with connections['kqms_db'].cursor() as cur:
        # === Mining (agregat sampai end_date) ===
        cur.execute("""
            WITH mining AS (
                SELECT 
                    SUM(CASE WHEN nama_material = 'LIM' THEN tonnage ELSE 0 END)::numeric AS lim,
                    SUM(CASE WHEN nama_material = 'SAP' THEN tonnage ELSE 0 END)::numeric AS sap,
                    SUM(CASE WHEN nama_material = 'Waste' THEN tonnage ELSE 0 END)::numeric AS waste,
                    SUM(CASE WHEN nama_material = 'Quarry' THEN tonnage ELSE 0 END)::numeric AS quarry,
                    SUM(CASE WHEN nama_material = 'Top Soil' THEN tonnage ELSE 0 END)::numeric AS topsoil,
                    SUM(CASE WHEN nama_material = 'OB' THEN tonnage ELSE 0 END)::numeric AS ob,
                    SUM(CASE WHEN nama_material = 'Ballast' THEN tonnage ELSE 0 END)::numeric AS ballast,
                    SUM(CASE WHEN nama_material = 'Biomass' THEN tonnage ELSE 0 END)::numeric AS biomass,
                    SUM(tonnage)::numeric AS total
                FROM mine_productions
                WHERE EXTRACT(YEAR FROM date_production) = %s
            ),
            plan AS (
                SELECT
                    SUM(
                        COALESCE(lim,0) + COALESCE(sap,0) + COALESCE(quarry,0) + 
                        COALESCE(topsoil,0) + COALESCE(ob,0) + COALESCE(ballast,0) +
                        COALESCE(biomass,0) + COALESCE(waste,0)
                    )::numeric AS plan_total
                FROM plan_productions
                WHERE EXTRACT(YEAR FROM date_plan) = %s
            )
            SELECT 
                COALESCE(m.lim,0)      AS lim_total,
                COALESCE(m.sap,0)      AS sap_total,
                COALESCE(m.waste,0)    AS waste_total,
                COALESCE(m.quarry,0)   AS quarry_total,
                COALESCE(m.topsoil,0)  AS topsoil_total,
                COALESCE(m.ob,0)       AS ob_total,
                COALESCE(m.ballast,0)  AS ballast_total,
                COALESCE(m.biomass,0)  AS biomass_total,
                COALESCE(m.total,0)    AS actual_total,
                COALESCE(p.plan_total,0) AS plan_total
            FROM mining m
            CROSS JOIN plan p
        """, [year, year])

        mining_row = cur.fetchone()
        mining = {
            "lim_total"     : mining_row[0],
            "sap_total"     : mining_row[1],
            "waste_total"   : mining_row[2],
            "quarry_total"  : mining_row[3],
            "topsoil_total" : mining_row[4],
            "ob_total"      : mining_row[5],
            "ballast_total" : mining_row[6],
            "biomass_total" : mining_row[7],
            "actual_total"  : mining_row[8],
            "plan_total"    : mining_row[9]
        }

       # === Quality (summary sampai end_date) ===
        cur.execute("""
            SELECT
            SUM(op.tonnage) AS prod_total,
            SUM(CASE WHEN m.nama_material = 'LIM' THEN op.tonnage ELSE 0 END) AS prod_lim,
            SUM(CASE WHEN m.nama_material = 'SAP' THEN op.tonnage ELSE 0 END) AS prod_sap
            FROM ore_productions op
            LEFT JOIN materials m ON m.id = op.id_material
            WHERE EXTRACT(YEAR FROM op.tgl_production) = %s
        """, [year])
        q_total, q_lim, q_sap = cur.fetchone()
        quality = {
            "total": q_total or 0,
            "lim": q_lim or 0,
            "sap": q_sap or 0
        }

       # === Selling (summary sampai end_date) ===
        cur.execute("""
            WITH actual AS (
                SELECT
                    SUM(CASE WHEN sale_adjust='HPAL' THEN s.tonnage ELSE 0 END) AS lim,
                    SUM(CASE WHEN sale_adjust='RKEF' THEN s.tonnage ELSE 0 END) AS sap,
                    SUM(s.tonnage) AS total
                FROM ore_sellings_barging s
                WHERE EXTRACT(YEAR FROM s.date_barge_out) = %s
                AND s.status_barging = 'Complete'
            ),
            plan AS (
                SELECT
                    SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim,
                    SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap,
                    SUM(tonnage_plan) AS total
                FROM ore_sellings_plan_barging p
                WHERE EXTRACT(YEAR FROM p.plan_date) = %s
            )
            SELECT
                COALESCE(a.lim,0)      AS actual_lim,
                COALESCE(a.sap,0)      AS actual_sap,
                COALESCE(a.total,0)    AS actual_total,
                COALESCE(p.lim,0)      AS plan_lim,
                COALESCE(p.sap,0)      AS plan_sap,
                COALESCE(p.total,0)    AS plan_total
            FROM actual a, plan p
        """, [year, year])

        s_lim_actual, s_sap_actual, s_total_actual, s_lim_plan, s_sap_plan, s_total_plan = cur.fetchone()

        selling = {
            "actual": s_total_actual or 0,
            "plan": s_total_plan or 0,
            "lim_actual": s_lim_actual or 0,
            "sap_actual": s_sap_actual or 0,
            "lim_plan": s_lim_plan or 0,
            "sap_plan": s_sap_plan or 0
        }

        # === Inventory ===
        cur.execute("""
            WITH incoming AS (
                SELECT
                    -- incoming tahun berjalan (untuk stock)
                    SUM(
                        CASE
                            WHEN status_dome = 'Finished' THEN 0
                            ELSE tonnage
                        END
                    ) AS in_stock,
                    -- total incoming asli (raw)
                    SUM(tonnage) AS total_in
                FROM ore_productions
                WHERE EXTRACT(YEAR FROM tgl_production) = %s
            ),
            outgoing AS (
                SELECT
                    -- outgoing tahun berjalan (untuk stock)
                    SUM(
                        CASE
                            WHEN sale_dome = 'Finished' THEN 0
                            ELSE tonnage
                        END
                    ) AS out_stock,
                    -- total outgoing asli (raw)
                    SUM(tonnage) AS total_out
                FROM ore_sellings_barging
                WHERE EXTRACT(YEAR FROM date_barge_out) = %s
                AND status_barging = 'Complete'
            ),
            saldo_awal AS (
                SELECT
                    COALESCE((
                        SELECT SUM(
                            CASE
                                WHEN status_dome = 'Finished' THEN 0
                                ELSE tonnage
                            END
                        )
                        FROM ore_productions
                        WHERE EXTRACT(YEAR FROM tgl_production) < %s
                    ), 0)
                    -
                    COALESCE((
                        SELECT SUM(
                            CASE
                                WHEN sale_dome = 'Finished' THEN 0
                                ELSE tonnage
                            END
                        )
                        FROM ore_sellings_barging
                        WHERE EXTRACT(YEAR FROM date_barge_out) < %s
                        AND status_barging = 'Complete'
                    ), 0) AS opening_balance
            )
            SELECT
                -- STOCK AKHIR TAHUN
                sa.opening_balance
                + COALESCE(i.in_stock, 0)
                - COALESCE(o.out_stock, 0) AS current_stock,
                -- MOVEMENT TAHUN BERJALAN (RAW)
                COALESCE(i.total_in, 0) AS total_in,
                COALESCE(o.total_out, 0) AS total_out
            FROM saldo_awal sa
            CROSS JOIN incoming i
            CROSS JOIN outgoing o;
                    
        """, [year, year, year, year])

        current_stock, inv_in, inv_out = cur.fetchone()

        inventory = {
            "current_stock" : current_stock or 0,
            "in"            : inv_in or 0,
            "out"           : inv_out or 0,
        }

    return {
        "mining"    : mining,
        "quality"   : quality,
        "selling"   : selling,
        "inventory" : inventory
    }

def fetch_fueling_year(year: int):
    with connections['kqms_db'].cursor() as cur:
        # Fuel by Date (Year)
        cur.execute("""
            WITH bulan AS (
                SELECT
                    TO_CHAR(gs::date, 'YYYY-MM') AS dt,
                    TO_CHAR(gs::date, 'FMMonth') AS bulan_label
                FROM generate_series(
                    make_date(%s, 1, 1),
                    make_date(%s, 12, 31),
                    interval '1 month'
                ) gs
            ),
            actual AS (
                SELECT
                    TO_CHAR(date, 'YYYY-MM') AS dt,
                    SUM(volume) AS total
                FROM mine_units_fuel_consumption
                WHERE EXTRACT(YEAR FROM date) = %s
                GROUP BY TO_CHAR(date, 'YYYY-MM')
            )
            SELECT
                b.dt as date,
                b.bulan_label,
                COALESCE(a.total, 0) AS volume
            FROM bulan b
            LEFT JOIN actual a ON b.dt = a.dt
            ORDER BY b.dt;
        """, [year, year, year])

        daily_rows = [
            dict(zip([c[0] for c in cur.description], r))
            for r in cur.fetchall()
        ]

        daily_total = sum(r["volume"] or 0 for r in daily_rows)

        # Fuel by Category
        cur.execute("""
            SELECT
                COALESCE(TRIM(t3.category), 'Unknown') AS category,
                ROUND(SUM(t1.volume)::NUMERIC, 2) AS volume
            FROM mine_units_fuel_consumption t1
            LEFT JOIN mine_units t2
                ON t2.unit_code::text = t1.unit::text
            LEFT JOIN units_categories t3
                ON t3.id = t2.id_category
            WHERE EXTRACT(YEAR FROM t1.date) = %s        
            GROUP BY t3.category
            ORDER BY t3.category;
        """, [year])

        category_rows = [
            dict(zip([c[0] for c in cur.description], r))
            for r in cur.fetchall()
        ]
        category_total = sum(r["volume"] or 0 for r in category_rows)

    return {
        "daily": {
            "series": daily_rows,
            "total" : daily_total
        },
        "category": {
            "series": category_rows,
            "total" : category_total
        }
    }