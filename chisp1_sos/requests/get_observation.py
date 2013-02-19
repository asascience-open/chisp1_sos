from flask import render_template

from chisp1_sos.models.station import get_station_feature
from chisp1_sos.models.text_csv import get_csv_data

from chisp1_sos.requests.get_capabilities import GetCapabilities

import dateutil.parser as dateparser
from datetime import timedelta
import pytz

from chisp1_sos import app

class GetObservation(object):
    def __init__(self, request):
        self.offering = request.args.get("offering", request.args.get("OFFERING", request.args.get("Offering", None)))
        self.procedure = request.args.get("procedure", request.args.get("PROCEDURE", request.args.get("Procedure", None)))
        self.obs_props = request.args.get("observedproperty", request.args.get("OBSERVEDPROPERTY", request.args.get("observedProperty", None)))
        self.eventtime = request.args.get("eventtime", request.args.get("EVENTTIME", request.args.get("Eventtime", None)))
        self.responseFormat = request.args.get("responseFormat", request.args.get("RESPONSEFORMAT", request.args.get("ResponseFormat", request.args.get("responseformat", None))))

    def response(self):
        if self.offering is None:
            return (render_template("error.xml", parameter="offering", value="Value missing"), "text/xml")
        else:
            possible_offerings = GetCapabilities.offerings.values()
            if not self.offering in possible_offerings:
                return (render_template("error.xml", parameter="offering", value="Invalid value.  Possible values are: %s" % ",".join(possible_offerings)), "text/xml")

        if self.procedure is None:
            return (render_template("error.xml", parameter="procedure", value="This SOS server requires a procedure argument to GetObservation"), "text/xml")
        if self.obs_props is None:
            return (render_template("error.xml", parameter="observedProperty", value="Value missing"), "text/xml")
        else:
            # Remove duplicates and split
            self.obs_props = list(set(self.obs_props.split(",")))
    
        provider = None
        for key, value in GetCapabilities.offerings.iteritems():
            if value == self.offering:
                provider = key
                break

        # Strip out starting and ending parameters
        starting = None
        ending = None
        if self.eventtime is not None and (isinstance(self.eventtime, unicode) or isinstance(self.eventtime, str)):
            if self.eventtime.lower() != "latest":
                starting = dateparser.parse(self.eventtime.split("/")[0])
                ending = dateparser.parse(self.eventtime.split("/")[1])


        if self.responseFormat == "text/csv":
            csv_data = get_csv_data(self.procedure, provider=provider, 
                                                    starting=starting, 
                                                    ending=ending,
                                                    observedProperties=self.obs_props)
            return (csv_data, "text/csv")

        elif self.responseFormat == "text/xml;subtype=\"om/1.0.0\"":
            station, publisher = get_station_feature(self.procedure, provider=provider, 
                                                                     starting=starting, 
                                                                     ending=ending,
                                                                     observedProperties=self.obs_props)
        else:
            return (render_template("error.xml", parameter="responseFormat", value="Invalid value.  Possible values are: 'text/csv' and 'text/xml;subtype=\"om/1.0.0\"'"), "text/xml")

        if station is None:
            return (render_template("error.xml", parameter="procedure", value="Invalid value"), "text/xml")

        min_time = "never"
        max_time = "never"
        # At least one record was found
        if len(station.time_range) > 0:
            min_time = min(station.time_range).astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            max_time = max(station.time_range).astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # If the latest was requested, strip it out now
        if self.eventtime is not None and (isinstance(self.eventtime, unicode) or isinstance(self.eventtime, str)):
            if self.eventtime.lower() == "latest":
                station.elements = station.filter_by_time(starting=max_time, ending=max_time)
                station.calculate_bounds()
               
        rows = []
        for point in station:
            row = [(point.time.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))]
            for ob in self.obs_props:
                m = None
                try:
                    m = point.get_member(name=ob)
                except:
                    row.append("None")
                    #row.append("None")
                    #row.append("None")
                else:
                    row.append(unicode(m.get("value", None)))
                    #row.append(m.get("method_id", None))
                    #row.append(m.get("method_name", None))

            rows.append(",".join(row))

        data_block = "\n".join(rows)

        return (render_template("getobservation.xml", min_time=min_time, max_time=max_time, station=station, data_block=data_block), "text/xml")
