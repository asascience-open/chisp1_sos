from flask import render_template
from chisp1_sos.models.offering import Wqp,Pwqmn,Network

class GetCapabilities(object):
    def __init__(self, request):
        self.request = request

    def response(self):

        pwqmn = Pwqmn()
        wqp = Wqp()
        network = Network([pwqmn, wqp])

        offerings = [network, pwqmn, wqp]

        return render_template("getcapabilities.xml", offerings=offerings)

