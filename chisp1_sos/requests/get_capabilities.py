from flask import render_template
from chisp1_sos.models.offering import Wqp,Pwqmn,Network

class GetCapabilities(object):

    offerings = {
        "all"   : "network-all",
        "pwqmn" : "network-pwqmn",
        "wqp"   : "network-wqp"
    }

    def __init__(self, request):
        self.request = request

    def response(self):

        pwqmn = Pwqmn(id=GetCapabilities.offerings.get("pwqmn"))
        wqp = Wqp(id=GetCapabilities.offerings.get("wqp"))
        network = Network([pwqmn, wqp], id=GetCapabilities.offerings.get("all"))

        offerings = [network, pwqmn, wqp]

        return render_template("getcapabilities.xml", offerings=offerings)
