
# reports/services.py
from django.db import connections
from ....utils.db_utils import get_db_vendor
db_vendor = get_db_vendor('kqms_db')

def g(row, key):
    return row.get(key, 0) or 0

def fetch_production_quality(ds: str, de: str):
    query = """
        SELECT op.tgl_production::date AS dt,
               SUM(op.tonnage) AS prod_total,
               SUM(CASE WHEN m.nama_material = 'LIM' THEN op.tonnage ELSE 0 END) AS prod_lim,
               SUM(CASE WHEN m.nama_material = 'SAP' THEN op.tonnage ELSE 0 END) AS prod_sap
        FROM ore_productions op
        LEFT JOIN materials m ON m.id = op.id_material
        WHERE op.tgl_production BETWEEN %s AND %s
        GROUP BY op.tgl_production::date
        ORDER BY op.tgl_production::date
    """
    with connections['kqms_db'].cursor() as cur:  # 🔥 pastikan pakai alias DB yang benar
        cur.execute(query, [ds, de])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    summary = {
        "total" :sum(r["prod_total"] or 0 for r in rows),
        "lim"   :sum(r["prod_lim"] or 0 for r in rows),
        "sap"   :sum(r["prod_sap"] or 0 for r in rows),
    }
    return {"rows": rows, "summary": summary}

def fetch_production_grade(ds: str, de: str):
    query = """
      WITH day_series AS (
            SELECT generate_series(%s::date, %s::date, interval '1 day')::date AS dt
        ),
        prod AS (
            SELECT
                DATE(tgl_production) AS prod_date,
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
            AND tgl_production BETWEEN %s AND %s
            GROUP BY DATE(tgl_production), TRIM(nama_material)
        )
        SELECT
            ds.dt,
            p.nama_material,
            COALESCE(p.total_ore, 0) AS total_ore,
            COALESCE(p.released, 0) AS released_ore,

            -- NI
            to_char(
                CASE WHEN p.denom_grade > 0
                    THEN p.sum_ton_ni / p.denom_grade
                    ELSE 0 END,
                'FM999999990.00'
            ) AS ni,

            -- CO
            to_char(
                CASE WHEN p.denom_grade > 0
                    THEN p.sum_ton_co / p.denom_grade
                    ELSE 0 END,
                'FM999999990.00'
            ) AS co,

            -- FE
            to_char(
                CASE WHEN p.denom_grade > 0
                    THEN p.sum_ton_fe / p.denom_grade
                    ELSE 0 END,
                'FM999999990.00'
            ) AS fe,

            -- MGO
            to_char(
                CASE WHEN p.denom_grade > 0
                    THEN p.sum_ton_mgo / p.denom_grade
                    ELSE 0 END,
                'FM999999990.00'
            ) AS mgo,

            -- SIO2
            to_char(
                CASE WHEN p.denom_grade > 0
                    THEN p.sum_ton_sio2 / p.denom_grade
                    ELSE 0 END,
                'FM999999990.00'
            ) AS sio2,

            -- SM
            to_char(
                CASE WHEN p.denom_grade > 0
                    AND (p.sum_ton_mgo / p.denom_grade) > 0
                    THEN (p.sum_ton_sio2 / p.denom_grade) /
                        ((p.sum_ton_mgo / p.denom_grade) + 0.000001)
                    ELSE 0 END,
                'FM999999990.00'
            ) AS sm
        FROM day_series ds
        LEFT JOIN prod p ON ds.dt = p.prod_date
        ORDER BY ds.dt, p.nama_material;
    """

    with connections["kqms_db"].cursor() as cur:
        cur.execute(query, [ds, de, ds, de])
        grade_rows = [
            {
                "dt": r[0],
                "nama_material": r[1],
                "total_ore": float(r[2] or 0),
                "released_ore": float(r[3] or 0),
                "ni": r[4],
                "co": r[5],
                "fe": r[6],
                "mgo": r[7],
                "sio2": r[8],
                "sm": r[9],
            }
            for r in cur.fetchall()
        ]
    return {"rows": grade_rows}


def fetch_selling(ds: str, de: str):
    query = """
        WITH day_series AS (
            SELECT generate_series(%s::date, %s::date, interval '1 day')::date AS dt
        ),
        actual AS (
            SELECT
                date_barge_out::date AS dt,
                SUM(CASE WHEN sale_adjust='HPAL' THEN s.tonnage ELSE 0 END) AS lim,
                SUM(CASE WHEN sale_adjust='RKEF' THEN s.tonnage ELSE 0 END) AS sap,
                SUM(s.tonnage) AS total
            FROM ore_sellings_barging s
            WHERE date_barge_out BETWEEN %s AND %s
            AND s.status_barging = 'Complete'
            GROUP BY date_barge_out::date
        ),
        plan AS (
            SELECT
                plan_date::date AS dt,
                SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim,
                SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap,
                SUM(tonnage_plan) AS total
            FROM ore_sellings_plan_barging
            WHERE plan_date BETWEEN %s AND %s
            GROUP BY plan_date::date
        )
        SELECT
            ds.dt,
            COALESCE(a.lim,0) AS actual_lim,
            COALESCE(a.sap,0) AS actual_sap,
            COALESCE(a.total,0) AS actual_total,
            COALESCE(p.lim,0) AS plan_lim,
            COALESCE(p.sap,0) AS plan_sap,
            COALESCE(p.total,0) AS plan_total
        FROM day_series ds
        LEFT JOIN actual a ON ds.dt = a.dt
        LEFT JOIN plan p ON ds.dt = p.dt
        ORDER BY ds.dt;
    """
    with connections['kqms_db'].cursor() as cur:
        cur.execute(query, [ds, de, ds, de, ds, de])
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

def fetch_barging(ds: str, de: str):
    query = """
               WITH tanggal AS (
                        SELECT generate_series(%s::date, %s::date, interval '1 day') AS date
                    ),
                    detail AS (
                        SELECT
                            s.date_hauling::date AS date,
                            mb.barge_code,
                            ROUND(SUM(s.tonnage)::numeric, 2) AS total,
                            ROUND(SUM(CASE WHEN m.nama_material = 'LIM' THEN s.tonnage ELSE 0 END)::numeric, 2) AS lim,
                            ROUND(SUM(CASE WHEN m.nama_material = 'SAP' THEN s.tonnage ELSE 0 END)::numeric, 2) AS sap
                        FROM ore_sellings_barging s
                        LEFT JOIN master_barge mb ON mb.id = s.barge_code
                        LEFT JOIN materials m ON m.id = s.id_material
                        WHERE s.date_hauling BETWEEN %s AND %s
                        --AND s.status_barging = 'Complete'
                        GROUP BY s.date_hauling::date, mb.barge_code
                    ),
                    plan AS (
                        SELECT
                            p.plan_date::date AS date,
                            ROUND(SUM(p.tonnage_plan)::numeric, 2) AS total_plan,
                            ROUND(SUM(CASE WHEN p.type_ore = 'LIM' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS lim_plan,
                            ROUND(SUM(CASE WHEN p.type_ore = 'SAP' THEN p.tonnage_plan ELSE 0 END)::numeric, 2) AS sap_plan
                        FROM ore_sellings_plan_barging p
                        WHERE p.plan_date BETWEEN %s AND %s
                        GROUP BY p.plan_date::date
                    )
                    SELECT
                        TO_CHAR(t.date, 'YY-MM-DD') AS label,
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
                    FROM tanggal t
                    LEFT JOIN detail d ON t.date = d.date
                    LEFT JOIN plan p   ON t.date = p.date
                    GROUP BY t.date, p.total_plan, p.lim_plan, p.sap_plan
                    ORDER BY t.date;
    """
    with connections['kqms_db'].cursor() as cur:
        cur.execute(query, [ds, de, ds, de, ds, de])
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

def fetch_production_mining(ds: str, de: str):
    query = """
        WITH day_series AS (
            SELECT generate_series(%s::date, %s::date, interval '1 day')::date AS dt
        ),
        prod AS (
            SELECT 
                DATE(date_production) AS prod_date,
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
            WHERE date_production BETWEEN %s AND %s
            GROUP BY DATE(date_production)
        ),
        plan AS (
            SELECT
                DATE(date_plan) AS plan_date,
                SUM(
                    COALESCE(lim,0) + COALESCE(sap,0) + COALESCE(quarry,0) + 
                    COALESCE(topsoil,0) + COALESCE(ob,0) + COALESCE(ballast,0) +
                    COALESCE(biomass,0) + COALESCE(waste,0)
                )::numeric AS plan_total
            FROM plan_productions
            WHERE date_plan BETWEEN %s AND %s
            GROUP BY DATE(date_plan)
        )
        SELECT 
            ds.dt,
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
        FROM day_series ds
        LEFT JOIN prod p ON ds.dt = p.prod_date
        LEFT JOIN plan pl ON ds.dt = pl.plan_date
        ORDER BY ds.dt;
    """
    with connections['kqms_db'].cursor() as cur:  
        cur.execute(query, [ds, de, ds, de,ds, de])  # butuh 4 param karena plan & prod pakai ds,de
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    summary = {
        "total"     : sum(r["actual_total"] or 0 for r in rows),
        "plan"      : sum(r["plan_total"] or 0 for r in rows),
        "lim"       : sum(r["lim"] or 0 for r in rows),
        "sap"       : sum(r["sap"] or 0 for r in rows),
        "waste"     : sum(r["waste"] or 0 for r in rows),
        "quarry"    : sum(r["quarry"] or 0 for r in rows),
        "topsoil"   : sum(r["topsoil"] or 0 for r in rows),
        "ob"        : sum(r["ob"] or 0 for r in rows),
        "ballast"   : sum(r["ballast"] or 0 for r in rows),
        "biomass"   : sum(r["biomass"] or 0 for r in rows),
    }

    return {"rows": rows, "summary": summary}

def fetch_inventory_balance(ds: str, de: str):
    query = """
        WITH tanggal AS (
            SELECT generate_series(%s::date, %s::date, interval '1 day')::date AS dt
        ),
        incoming AS (
            SELECT
                tgl_production::date AS dt,
                SUM(tonnage) AS total_in
            FROM ore_productions
            WHERE tgl_production BETWEEN %s AND %s
            GROUP BY tgl_production::date
        ),
        outgoing AS (
            SELECT
                date_hauling::date AS dt,
                SUM(tonnage) AS total_out
            FROM ore_sellings_barging
            WHERE 
            date_hauling >= %s AND date_barge_out <= %s
            AND status_barging = 'Complete'
            GROUP BY date_hauling::date
        ),
        saldo_awal AS (
            SELECT
                COALESCE((SELECT SUM(tonnage) FROM ore_productions WHERE tgl_production < %s), 0)
                - COALESCE((SELECT SUM(tonnage) FROM ore_sellings_barging WHERE date_hauling < %s AND status_barging = 'Complete'), 0) 
                AS value
        )
        SELECT
            t.dt,
            COALESCE(i.total_in, 0) AS total_in,
            COALESCE(o.total_out, 0) AS total_out,
            (SELECT value FROM saldo_awal) AS opening_balance,
            (SELECT value FROM saldo_awal)
              + SUM(COALESCE(i.total_in, 0) - COALESCE(o.total_out, 0)) 
                OVER (ORDER BY t.dt ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) 
              AS running_balance
        FROM tanggal t
        LEFT JOIN incoming i ON t.dt = i.dt
        LEFT JOIN outgoing o ON t.dt = o.dt
        ORDER BY t.dt;
    """
    with connections['kqms_db'].cursor() as cur:
        # 8 parameter: (ds,de) untuk tanggal series, (ds,de) untuk incoming, (ds,de) untuk outgoing, (ds,de) untuk saldo_awal
        cur.execute(query, [ds,de, ds, de,ds, de,ds, ds])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    summary = {
        "opening_balance" : rows[0]["opening_balance"] if rows else 0,
        "total_in"  : sum(r["total_in"] or 0 for r in rows),
        "total_out" : sum(r["total_out"] or 0 for r in rows),
        "closing_balance": rows[-1]["running_balance"] if rows else 0
    }

    return {"rows": rows, "summary": summary}

def fetch_inventory_dome(de: str):
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
            ) AS sm,
          direct_sale  
        FROM details_roa
        WHERE
        -- status_dome != 'Finished' AND 
        -- direct_sale = 'No' AND 
        tgl_production <= %s
        GROUP BY stockpile, pile_id, nama_material, direct_sale
    ),
    sell AS (
        SELECT
            TRIM(stockpile) AS stockpile,
            TRIM(dome)      AS pile_id,
            TRIM(material)  AS nama_material,
            SUM(tonnage)    AS tonnage
        FROM details_selling_barging
        WHERE date_barge_out <= %s
        AND status_barging = 'Complete'
        GROUP BY stockpile, dome, material
    )
    SELECT 
        p.stockpile,
        p.pile_id,
        p.nama_material,
        p.total_ore,
        p.released,
        -- ✅ total_selling dengan CASE biar akurat cross-material
        COALESCE(ROUND(SUM(
            CASE
                WHEN p.nama_material = 'LIM' AND s.nama_material = 'SAP' THEN s.tonnage
                WHEN p.nama_material = 'SAP' AND s.nama_material = 'LIM' THEN s.tonnage
                WHEN p.nama_material = s.nama_material THEN s.tonnage
                ELSE 0
            END
        )::numeric, 2), 0) AS total_selling,
        -- ✅ balance = total_ore - total_selling
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
            p.total_ore, 
            p.released, 
            p.ni, p.co, p.fe, p.mgo, p.sio2, p.sm
    ORDER BY p.nama_material, p.stockpile;
    """
    with connections['kqms_db'].cursor() as cur:
        cur.execute(query, [de, de])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    return {"rows": rows}

def fetch_summary_to_date(end_date):
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
                WHERE date_production <= %s
            ),
            plan AS (
                SELECT
                    SUM(
                        COALESCE(lim,0) + COALESCE(sap,0) + COALESCE(quarry,0) + 
                        COALESCE(topsoil,0) + COALESCE(ob,0) + COALESCE(ballast,0) +
                        COALESCE(biomass,0) + COALESCE(waste,0)
                    )::numeric AS plan_total
                FROM plan_productions
                WHERE date_plan <= %s
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
        """, [end_date, end_date])

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

        # hitung setelah mining dict siap
        mining["ore"] = mining["lim_total"] + mining["sap_total"]
        mining["non_ore"] = (
            mining["waste_total"] + mining["quarry_total"] + mining["topsoil_total"] +
            mining["ob_total"] + mining["ballast_total"] + mining["biomass_total"]
        )

       # === Quality (summary sampai end_date) ===
        cur.execute("""
            SELECT
            SUM(op.tonnage) AS prod_total,
            SUM(CASE WHEN m.nama_material = 'LIM' THEN op.tonnage ELSE 0 END) AS prod_lim,
            SUM(CASE WHEN m.nama_material = 'SAP' THEN op.tonnage ELSE 0 END) AS prod_sap
            FROM ore_productions op
            LEFT JOIN materials m ON m.id = op.id_material
            WHERE op.tgl_production <= %s
        """, [end_date])
        q_total, q_lim, q_sap = cur.fetchone()
        quality = {
            "total" : q_total or 0,
            "lim"   : q_lim or 0,
            "sap"   : q_sap or 0
        }

       # === Selling (summary sampai end_date) ===
        cur.execute("""
            WITH actual AS (
                SELECT
                    SUM(CASE WHEN sale_adjust='HPAL' THEN s.tonnage ELSE 0 END) AS lim,
                    SUM(CASE WHEN sale_adjust='RKEF' THEN s.tonnage ELSE 0 END) AS sap,
                    SUM(s.tonnage) AS total
                FROM ore_sellings_barging s
                WHERE s.date_barge_out <= %s
                 AND s.status_barging = 'Complete'   
            ),
            plan AS (
                SELECT
                    SUM(CASE WHEN type_ore = 'LIM' THEN tonnage_plan ELSE 0 END) AS lim,
                    SUM(CASE WHEN type_ore = 'SAP' THEN tonnage_plan ELSE 0 END) AS sap,
                    SUM(tonnage_plan) AS total
                FROM ore_sellings_plan_barging p
                WHERE p.plan_date <= %s
            )
            SELECT
                COALESCE(a.lim,0)      AS actual_lim,
                COALESCE(a.sap,0)      AS actual_sap,
                COALESCE(a.total,0)    AS actual_total,
                COALESCE(p.lim,0)      AS plan_lim,
                COALESCE(p.sap,0)      AS plan_sap,
                COALESCE(p.total,0)    AS plan_total
            FROM actual a, plan p
        """, [end_date, end_date])

        s_lim_actual, s_sap_actual, s_total_actual, s_lim_plan, s_sap_plan, s_total_plan = cur.fetchone()

        selling = {
            "actual"    : s_total_actual or 0,
            "plan"      : s_total_plan or 0,
            "lim_actual": s_lim_actual or 0,
            "sap_actual": s_sap_actual or 0,
            "lim_plan"  : s_lim_plan or 0,
            "sap_plan"  : s_sap_plan or 0
        }

        # === Inventory ===
        cur.execute("""
            WITH incoming AS (
                SELECT SUM(tonnage) AS total_in
                FROM ore_productions
                WHERE tgl_production <= %s
            ),
            outgoing AS (
                SELECT SUM(tonnage) AS total_out
                FROM ore_sellings_barging
                WHERE date_barge_out <= %s
                AND status_barging = 'Complete'
            ),
            saldo_awal AS (
                SELECT
                    COALESCE((SELECT SUM(tonnage) FROM ore_productions WHERE tgl_production <= %s), 0)
                    - COALESCE((SELECT SUM(tonnage) FROM ore_sellings_barging WHERE date_barge_out <= %s AND status_barging = 'Complete'), 0)
                    AS current_stock
            )
            SELECT
                (SELECT current_stock FROM saldo_awal) AS current_stock,
                COALESCE((SELECT total_in FROM incoming), 0) AS total_in,
                COALESCE((SELECT total_out FROM outgoing), 0) AS total_out
                    
        """, [end_date, end_date, end_date, end_date])

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
