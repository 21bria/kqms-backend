
# reports/services.py
from django.db import connections
from ....utils.db_utils import get_db_vendor
db_vendor = get_db_vendor('kqms_db')

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

def fetch_selling_quality(ds: str, de: str):
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
        "total": sum(r["actual_total"] or 0 for r in rows),
        "plan":  sum(r["plan_total"] or 0 for r in rows),
        "lim":   sum(r["lim"] or 0 for r in rows),
        "sap":   sum(r["sap"] or 0 for r in rows),
        "waste": sum(r["waste"] or 0 for r in rows),
        "quarry":sum(r["quarry"] or 0 for r in rows),
        "topsoil":sum(r["topsoil"] or 0 for r in rows),
        "ob":    sum(r["ob"] or 0 for r in rows),
        "ballast":sum(r["ballast"] or 0 for r in rows),
        "biomass":sum(r["biomass"] or 0 for r in rows),
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
                date_barge_out::date AS dt,
                SUM(tonnage) AS total_out
            FROM ore_sellings_barging
            WHERE date_barge_out BETWEEN %s AND %s
            GROUP BY date_barge_out::date
        ),
        saldo_awal AS (
            SELECT
                COALESCE((SELECT SUM(tonnage) FROM ore_productions WHERE tgl_production < %s), 0)
                - COALESCE((SELECT SUM(tonnage) FROM ore_sellings_barging WHERE date_barge_out < %s), 0) 
                AS value
        )
        SELECT
            t.dt,
            COALESCE(i.total_in, 0) AS total_in,
            COALESCE(o.total_out, 0) AS total_out,
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
        cur.execute(query, [ds, de, ds, de, ds, de, ds, ds])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    summary = {
        "total_in": sum(r["total_in"] or 0 for r in rows),
        "total_out": sum(r["total_out"] or 0 for r in rows),
        "closing_balance": rows[-1]["running_balance"] if rows else 0
    }

    return {"rows": rows, "summary": summary}

def fetch_inventory_dome(de: str):
    query = """
      WITH prod AS (
        SELECT
            TRIM(stockpile) AS stockpile,
            TRIM(pile_id)   AS pile_id,
            TRIM(nama_material) AS nama_material,
            SUM(tonnage)    AS total_ore,
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
        WHERE status_dome != 'Finished'
        AND direct_sale = 'No'
        AND tgl_production <= %s
        GROUP BY stockpile, pile_id, nama_material
    ),
    sell AS (
        SELECT
            TRIM(stockpile) AS stockpile,
            TRIM(dome)      AS pile_id,
            TRIM(material)  AS nama_material,
            SUM(tonnage)    AS tonnage
        FROM details_selling_barging
        WHERE date_barge_out <= %s
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
            p.total_ore, p.released, 
            p.ni, p.co, p.fe, p.mgo, p.sio2, p.sm
    ORDER BY p.nama_material, p.stockpile;
    """
    with connections['kqms_db'].cursor() as cur:
        cur.execute(query, [de, de])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    return {"rows": rows}
