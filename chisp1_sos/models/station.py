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

def get_station_feature(station_id):

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
            s.location = sPoint(row["Longitude"], row["Latitude"])
            s.set_property("country","CA")
            s.set_property("organization_name","Ontario Ministry of the Environment")
            s.set_property("organization_id","ENE")

            cur.execute("SELECT * FROM data WHERE STATION='%s' ORDER BY DATE ASC" % station_id)
            rows = cur.fetchall()

            for d,members in itertools.groupby(rows, key=lambda s:s[3]):
                p = Point()
                p.time = datetime.strptime(d, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc)

                for m in members:
                    p.add_member(Member(value=m["RESULT"], unit=m["UNITS"], name=m["PARM"], description=m["PARM_DESCRIPTION"], standard=None))

                s.add_element(p)

            s.calculate_bounds()
            publisher = {"name": "Ontario Ministry of the Environment", "url" : "http://www.ene.gov.on.ca/environment/en/resources/collection/data_downloads/index.htm#PWQMN"}
            return s, publisher
        else:
            # Try WQP
            wq = WqpRest()
            s = wq.get_station(siteid=station_id)
            if s is not None:
                s.calculate_bounds()
                publisher = {"name": "Water Quality Monitoring Portal", "url" : "http://waterqualitydata.us"}
                return s, publisher
        
    return None,None
