# Server for the GaspUI
from typing import Optional
from fastapi import FastAPI, HTTPException
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from grid import Grid
from influx import InfluxClient
import xarray as xr
import json
import datetime
import numpy as np

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/", StaticFiles(directory="dashboard"), name="dashboard")

class ServerState:
	def __init__(self):
		dataset = "HELSINKI_100x100m_3mo.nc4"
		xds = xr.open_dataset(dataset)
		self.oldestTimestamp = xds.time.values.min()
		self.newestTimestamp = xds.time.values.max()
		self.diffdays = self.indays(self.newestTimestamp - self.oldestTimestamp)
		self.timestampfmt = '%Y-%m-%dT%H:%M:%S.%f'
		self.timerange = lambda t: (t-np.timedelta64(2, 'h'), t+np.timedelta64(8, 'h'))
		self.ranges = json.load(open("ranges.json", "r"))
		self.g = Grid(xds.lat.values, xds.lon.values)
		self.influx = InfluxClient()

	def getHistoricDates(self, t: np.datetime64):
		diff = t.astype('datetime64[s]') - self.newestTimestamp.astype('datetime64[s]')
		if diff >= np.timedelta64(0, 's'):
			days = self.indays(diff)
			days = days%self.diffdays
			t = self.oldestTimestamp + np.timedelta64(days + 1, 'D')
		return t

	def indays(self, diff: np.timedelta64):
		diff = diff.astype('timedelta64[D]')
		days = diff / np.timedelta64(1, 'D')
		return int(days)

	def query(self, t: np.datetime64, field):
		startstop = self.timerange(self.getHistoricDates(t))
		fieldPresent = '|> filter(fn: (r) => r["_field"] == "%s")'%field if field else ""
		query = """
		from(bucket: "vwa")
		  |> range(start: %s, stop: %s)
		  |> filter(fn: (r) => r["_measurement"] == "vwa")
		  %s
		"""%(str(startstop[0])+"Z", str(startstop[1])+"Z", fieldPresent)
		# print(query)
		tables = ss.influx.q.query(query, org="vwa")
		ret = {"grid": {}, "timestamps": []}
		temp = []
		for t in tables:
			for row in t:
				f = row["_field"]
				c = row["grid"]
				val = row["_value"]
				tm = row["_time"]
				if c not in ret["grid"]:
					ret["grid"][c] = {}
				if f not in ret["grid"][c]:
					ret["grid"][c][f] = []
				ret["grid"][c][f].append(val)
				temp.append(np.datetime64(tm.strftime(ss.timestampfmt)))
				if len(temp) == 20 and not len(ret["timestamps"]):
					ret["timestamps"] = temp[:]
		return ret
				
				
			


ss = ServerState()


@app.get("/api/get")
async def get_all_cells(timestamp: Optional[str] = None, field: str = None):
	"""
	- **timestamp**: timestamp is the current/provided timestamp. '%Y-%m-%dT%H:%M:%S'
	- **field**: Must be one of fmi_no, fmi_no2, fmi_pm10p0, fmi_pm2p5, fmi_rel_humid, 
	fmi_so2, fmi_temp_2m, fmi_windspeed_10m, megasense_aqi, megasense_co, megasense_no2, 
	megasense_o3, megasense_pm10p0, megasense_pm2p5
	"""
	if field is not None and field not in ss.ranges.keys():
		raise HTTPException(status_code=500, detail="Field should be one of %s"%str(ss.ranges.keys()))

	if timestamp is None:
		t = np.datetime64('now')
	else:
		try:
			t = np.datetime64(timestamp)
		except:
			raise HTTPException(status_code=500, detail="Timestamp should be of format %s"%ss.timestampfmt)
	ret = ss.query(t, field)
	ret["timestamps"] = list(map(lambda x: str(x), ret["timestamps"]))
	return ret


# Using precomputed ranges for UI
# We don't need to compute ranges each time a request is made.
# See xplore.ipynb for how the ranges were computed.
@app.get("/api/ranges")
async def get_ranges():
	return ss.ranges

@app.get("/api/grid")
async def get_grid():
	return ss.g.grid


if __name__ == "__main__":
	uvicorn.run(app, host="0.0.0.0", port=80)