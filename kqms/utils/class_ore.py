from kqms.models import OreClass

def to_float(value):
    try:
        return float(value) if value not in [None, "", "null", "None"] else None
    except:
        return None


def get_grade_by_rules(ni, mgo, fe):
    # Convert inputs
    ni  = to_float(ni)
    mgo = to_float(mgo)
    fe  = to_float(fe)

    if ni is None or mgo is None or fe is None:
        return "NULL"

    # Fetch rules
    classes = OreClass.objects.filter(status=True).order_by('id')

    for c in classes:
        ni_ok  = (c.ni_min is None or ni >= c.ni_min) and (c.ni_max is None or ni <= c.ni_max)
        mgo_ok = (c.mgo_min is None or mgo >= c.mgo_min) and (c.mgo_max is None or mgo <= c.mgo_max)
        fe_ok  = (c.fe_min is None or fe >= c.fe_min) and (c.fe_max is None or fe <= c.fe_max)

        if ni_ok and mgo_ok and fe_ok:
            return c.ore_class

    return "???"
