import sqlite3
import itertools
import pytz
from datetime import datetime

from chisp1_sos import app

from pyoos.collectors.wqp.wqp_rest import WqpRest
from pyoos.cdm.features.station import Station as pStation
from pyoos.cdm.features.point import Point
from shapely.geometry import Point as sPoint
from pyoos.cdm.utils.member import Member

def get_station_feature(station_id, provider=None, **kwargs):

    if provider is None or provider == "all":
        s,p = get_pwqmn(station_id)
        if s is None:
            return get_wqp(station_id, **kwargs)
        return s,p
    elif provider == "pwqmn":
        return get_pwqmn(station_id, **kwargs)
    elif provider == "wqp":
        return get_wqp(station_id, **kwargs)
                
def get_pwqmn(station_id, **kwargs):
    conn = sqlite3.connect(app.config.get('DATABASE'))
    with conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM stations WHERE STATION='%s'" % station_id)
        row = cur.fetchone()
        if row is not None:
            # Serve out OME 
            s = pStation()
            s.uid = row["STATION"]
            s.name = row["NAME"]
            s.description = row["LOCATION"]
            s.location = sPoint(row["Longitude"], row["Latitude"], 0)
            s.set_property("country","CA")
            s.set_property("organization_name","Ontario Ministry of the Environment")
            s.set_property("organization_id","ENE")

            filters = []
            starting = kwargs.get("starting", None)
            ending = kwargs.get("ending", None)
            obs = kwargs.get("observedProperties", None)
            if starting is not None:
                filters.append("AND DATE > %s" % starting.strftime("%Y-%m-%dT%H:%M:%S"))
            if ending is not None:
                filters.append("AND DATE < %s" % ending.strftime("%Y-%m-%dT%H:%M:%S"))
            if obs is not None:
                obs = map(lambda x: "'%s'" % x, obs)
                filters.append("AND PARM in (%s)" % ",".join(obs))

            cur.execute("SELECT * FROM data WHERE STATION='%s' %s ORDER BY DATE ASC" % (station_id, " ".join(filters)))
            rows = cur.fetchall()

            for d,members in itertools.groupby(rows, key=lambda s:s[3]):
                p = Point()
                p.time = datetime.strptime(d, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc)

                for m in members:
                    p.add_member(Member(value=m["RESULT"], unit=m["UNITS"], name=m["PARM"], description=m["PARM_DESCRIPTION"], standard=None, method_id=m["METHOD"], method_name=m["METHOD"]))

                s.add_element(p)

            s.calculate_bounds()
            publisher = {"name": "Ontario Ministry of the Environment", "url" : "http://www.ene.gov.on.ca/environment/en/resources/collection/data_downloads/index.htm#PWQMN"}
            return s, publisher
    return None, None

def get_wqp(station_id, **kwargs):
    wq = WqpRest()

    params = {
        "siteid" : station_id
    }

    obs_props = kwargs.get("observedProperties", None)
    if obs_props is not None:
        params["characteristicName"] = ";".join(obs_props)

    st = kwargs.get("starting", None)
    et = kwargs.get("ending", None)
    if st is not None:
        wq.start_time = st
    if et is not None:
        wq.end_time = et
    
    s = wq.get_station(**params)
    if s is not None:
        s.calculate_bounds()
        publisher = {"name": "Water Quality Monitoring Portal", "url" : "http://waterqualitydata.us"}
        return s, publisher
    return None, None