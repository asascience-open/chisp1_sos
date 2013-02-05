from flask import render_template

from chisp1_sos.models.station import get_station_feature

class DescribeSensor(object):
    def __init__(self, request):
        self.procedure = request.args.get("procedure", request.args.get("PROCEDURE", request.args.get("Procedure", None)))

    def response(self):
        if self.procedure is None:
            return render_template("error.xml", parameter="procedure", value="Value missing")

        station, publisher = get_station_feature(self.procedure)

        if station is None:
            return render_template("error.xml", parameter="procedure", value="Invalid value")

        return render_template("describesensor.xml", station=station, publisher=publisher)