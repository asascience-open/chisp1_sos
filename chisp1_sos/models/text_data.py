import csv
import sqlite3
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO       

from chisp1_sos import app

from pyoos.collectors.wqp.wqp_rest import WqpRest

def get_text_data(station_id, responseFormat, provider=None, **kwargs):

    mt = None
    delimiter = None

    if responseFormat == "text/csv":
        mt = 'csv'
        delimiter = ','
    elif responseFormat == "text/tsv":
        mt = 'tsv'
        delimiter = '\t'

    if provider is None or provider == "all":
        raw = get_pwqmn(station_id, delimiter=delimiter, **kwargs)
        if raw is None:
            return get_wqp(station_id, mimeType=mt, **kwargs)
        return raw
    elif provider == "pwqmn":
        return get_pwqmn(station_id, delimiter=delimiter, **kwargs)
    elif provider == "wqp":
        return get_wqp(station_id, mimeType=mt, **kwargs)
                
def get_pwqmn(station_id, delimiter, **kwargs):
    conn = sqlite3.connect(app.config.get('DATABASE'))
    with conn:
        #conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT * from stations WHERE stations.STATION='%s'" % station_id)

        if cur.fetchone() is None:
            return None

        filters = []
        starting = kwargs.get("starting", None)
        ending = kwargs.get("ending", None)
        obs = kwargs.get("observedProperties", None)
        if starting is not None:
            filters.append("AND data.DATE > '%s'" % starting.strftime("%Y-%m-%dT%H:%M:%S"))
        if ending is not None:
            filters.append("AND data.DATE < '%s'" % ending.strftime("%Y-%m-%dT%H:%M:%S"))
        if obs is not None:
            obs = map(lambda x: "'%s'" % x, obs)
            obs_str = ",".join(obs)
            filters.append("AND (data.PARM_DESCRIPTION in (%s) OR data.PARM in (%s))" % (obs_str,obs_str))

        
        query = "SELECT * FROM data INNER JOIN stations ON data.STATION == stations.STATION WHERE stations.STATION='%s' %s ORDER BY DATE ASC" % (station_id, " ".join(filters))
        app.logger.debug(query)
        cur.execute(query)

        buff = StringIO()
        writer = csv.writer(buff, delimiter=delimiter)
        writer.writerow([col[0] for col in cur.description])
        filter(None, (writer.writerow(row) for row in cur))
        return buff.getvalue()

    return None

def get_wqp(station_id, mimeType, **kwargs):
    wq = WqpRest()

    params = {
        "siteid"   : station_id,
        "mimeType" : mimeType
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
    
    return wq.get_raw_results_data(**params)