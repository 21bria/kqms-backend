
# reports/services.py
from django.db import connections
from ....utils.db_utils import get_db_vendor
db_vendor = get_db_vendor('kqms_db')

def export_production_mining(ds: str, de: str):
    query = """
        SELECT *
        FROM mine_productions
        WHERE date_production BETWEEN %s AND %s
        ORDER BY date_production::date
    """
    with connections['kqms_db'].cursor() as cur:  
        cur.execute(query, [ds, de])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    return {"rows": rows}

def export_production_quality(ds: str, de: str):
    query = """
        SELECT *
        FROM ore_production op
        WHERE op.tgl_production BETWEEN %s AND %s
        ORDER BY op.tgl_production::date
    """
    with connections['kqms_db'].cursor() as cur: 
        cur.execute(query, [ds, de])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    return {"rows": rows}

def export_selling_quality(ds: str, de: str):
    query = """
        SELECT *
        FROM details_selling_barging
        WHERE date_barge_in >= %s
          AND date_barge_out <= %s
          AND status_barging = 'Complete'
        ORDER BY date_barge_out::date
    """
    with connections['kqms_db'].cursor() as cur:
        cur.execute(query, [ds, de])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    return {"rows": rows}

def export_inventory_dome(de: str):
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
        WHERE 
        --status_dome != 'Finished' AND direct_sale = 'No' AND 
        tgl_production <= %s
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
            p.total_ore, p.released, 
            p.ni, p.co, p.fe, p.mgo, p.sio2, p.sm
    ORDER BY p.nama_material, p.stockpile;
    """
    with connections['kqms_db'].cursor() as cur:
        cur.execute(query, [de, de])
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    return {"rows": rows}
