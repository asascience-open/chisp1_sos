import sqlite3
import pytz

from lxml import etree
from chisp1_sos import app

from datetime import datetime

from pyoos.collectors.wqp.wqp_rest import WqpRest

from shapely.geometry import box, MultiPoint, Point, MultiPolygon

class Offering(object):
    """
    <sos:ObservationOffering gml:id="network-pwqmn-all">
        <gml:description>All PWQMN stations available</gml:description>
        <gml:name>urn:network:pwqmn</gml:name>
        <gml:srsName>http://www.opengis.net/def/crs/EPSG/0/4326</gml:srsName>
        <gml:boundedBy>
            <gml:Envelope srsName="http://www.opengis.net/def/crs/EPSG/0/4326">
                <gml:lowerCorner>-90 -180</gml:lowerCorner>
                <gml:upperCorner>90 180</gml:upperCorner>
            </gml:Envelope>
        </gml:boundedBy>
        <sos:time>
            <gml:TimePeriod>
                <gml:beginPosition>0001-01-01T00:00:00Z</gml:beginPosition>
                <gml:endPosition indeterminatePosition="now"/>
            </gml:TimePeriod>
        </sos:time>
        <sos:procedure xlink:href="urn:ioos:network:pwqmn:all"/>
        <sos:observedProperty xlink:href="lots"/>
        <sos:featureOfInterest xlink:href="urn:cgi:Feature:CGI:EarthOcean"/>
        <sos:responseFormat>text/xml;subtype="om/1.0.0"</sos:responseFormat>
        <sos:resultModel>om:ObservationCollection</sos:resultModel>
        <sos:responseMode>inline</sos:responseMode>
    </sos:ObservationOffering>
    """
    def __init__(self):
        self.id = None
        self.name = None
        self.description = None
        self.bbox = box(-180,-90,180, 90).bounds
        self.starting = datetime(1,1,1).replace(tzinfo=pytz.utc).replace(microsecond=0)
        self.ending = datetime.now().replace(tzinfo=pytz.utc).replace(microsecond=0)
        self.procedures = []
        self.features = []
        self.observedProperties = []


class Network(Offering):
    def __init__(self, offerings):
        super(Network,self).__init__()
        self.id = "network-all"
        self.name = "urn:network:all"
        self.description = "Network All"
        self.procedures = sorted(list(set([p for ps in offerings for p in ps.procedures])))
        self.observedProperties = sorted(list(set([p for ps in offerings for p in ps.observedProperties])))
        self.features = sorted(list(set([p for ps in offerings for p in ps.features])))
        self.starting = min([ps.starting for ps in offerings]).replace(microsecond=0)
        self.ending = max([ps.ending for ps in offerings]).replace(microsecond=0)
        self.bbox = MultiPolygon([box(ps.bbox[0], ps.bbox[1], ps.bbox[2], ps.bbox[3]) for ps in offerings]).bounds


class Wqp(Offering):
    def __init__(self):
        super(Wqp,self).__init__()
        self.id = "network-wqp-all"
        self.name = "urn:network:wqp"
        self.description = "All WQP stations available"
        self.features = ["urn:cgi:Feature:CGI:EarthOcean"]
        self.procedures = []
         
        doc = etree.parse(WqpRest().characteristics_url)
        self.observedProperties = [d.get("value") for d in doc.findall("//Code")]


class Pwqmn(Offering):
    def __init__(self):
        super(Pwqmn,self).__init__()
        self.id = "network-pwqmn-all"
        self.name = "urn:network:pwqmn"
        self.description = "All PWQMN stations available"
        self.bbox = box(-180,-90,180, 90).bounds

        self.procedures = []
        self.features = ["urn:cgi:Feature:CGI:EarthOcean"]
        self.observedProperties = []

        conn = sqlite3.connect(app.config.get('DATABASE'))
        with conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT Longitude,Latitude,Station from stations ORDER BY Station ASC")

            points = []
            rows = cur.fetchall()
            for row in rows:
                points.append(Point(row["Longitude"], row["Latitude"]))
                self.procedures.append(row["STATION"])
            self.bbox = MultiPoint(points).bounds

            cur.execute("SELECT min(DATE) as MIN, max(DATE) as MAX from data")
            row = cur.fetchone()
            self.starting = datetime.strptime(row["MIN"], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc).replace(microsecond=0)
            self.ending = datetime.strptime(row["MAX"], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc).replace(microsecond=0)

            cur.execute("SELECT DISTINCT PARM_DESCRIPTION from data ORDER BY PARM_DESCRIPTION ASC")
            rows = cur.fetchall()
            self.observedProperties = [o["PARM_DESCRIPTION"] for o in rows]
