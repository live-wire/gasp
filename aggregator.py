import xarray as xr
import datetime
from influx import InfluxClient
from grid import Grid
import statistics
import math
import numpy as np
from multiprocessing import Pool
import threading

dataset = "HELSINKI_100x100m_3mo.nc4"
xds = xr.open_dataset(dataset)

times = []
for i, item in enumerate(xds.time.values):
    if i%6 == 0:
        times.append(str(item))

dimensions = set()
for k in xds.dims:
    dimensions.add(str(k))

tsd = InfluxClient()

variables = list(map(lambda x: str(x), xds.variables))
variables = list(filter(lambda x: x not in dimensions, variables))
done = 0

g = Grid(xds.lat.values, xds.lon.values)


def gridLatLongs(lats, longs):
    ret = []
    for la in lats:
        for lo in longs:
            ret.append((la,lo))
            break # Just take the first value from the combination # Instead if mean computation
        break
    return ret

def processCell(t):
    global done
    if done%100 == 0:
        pr = (len(times)-done)*100//len(times)
        print("Pushed till:%s, Remaining: %d percent"%(done, pr))
    llats = g.llats
    llongs = g.llongs
    for i in range(len(llats)):
        for j in range(len(llongs)):
            lls = gridLatLongs(llats[i], llongs[j])
            cell = "cell_%d_%d"%(i,j)
            fieldSet = getFieldSet(t, lls, statistics.mean)
            polygon = str(g.grid[cell]['polygon']).replace(" ", "")
            polygon = polygon.strip("[)(\[\]]")
            polygon = polygon.replace("),(", "__")
            polygon = polygon.replace(",", "_")
            r = "vwa,grid=%s,polygon=%s %s %d"%(cell, polygon, fieldSet, t4influx(t))
            # print(r)
            tsd.send(r)
    done += 1

def t4influx(s):
    s = s[:-3]
    t = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
    x = int(t.timestamp())
    while x<1e18:
        x = x*10
    return x

def getFieldSet(t, lls, reducer=statistics.mean):
    d = dict()
    for v in variables:
        d[v] = []

    for lat, lon in lls:
        for v in variables:
            dlocal = dict(lat=lat, lon=lon, time=t)
            valueObj = xds.loc[dlocal].get(v).values
            # print(v, type(valueObj), valueObj)
            if isinstance(valueObj, np.ndarray): 
                val = valueObj.item()
            else:
                val = valueObj
            val = 0.0 if math.isnan(val) else val
            d[v].append(val)
            
    fields = ""
    for v in variables:
        s = "%s=%f"%(v, reducer(d[v]))
        s = s.replace(" ", "_") # Just to be sure
        fields = fields + ("" if not len(fields) else ",") + s
    return fields

p = Pool(4)

print(p.map(processCell, times))

