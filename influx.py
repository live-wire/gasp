
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from batcher import Batcher

class InfluxClient:
	def __init__(self, 
		url = "http://localhost:8086",
		token = "IpLnoNkWhqmnSLO2ieeqmHejYrrokycO5Be8HRgM6UI1S_CO-Py2_opA2E1z6iCzJrv5U_gHGVHh5JMCFsgwjQ=="
		):

		# You can generate a Token from the "Tokens Tab" in the UI @ localhost:9999

		self.org = "vwa"
		self.bucket = "vwa"

		self.client = InfluxDBClient(url=url, token=token)
		self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
		self.b = Batcher(500, 5, self._send)
		self.q = self.client.query_api()

	def send(self, line):
		self.b.send(line)

	def sendSequence(self, sequence):
		self._send(sequence)

	def _send(self, sequence):
		try:
			self.write_api.write(self.bucket, self.org, sequence)
			print("%d items sent!"%len(sequence))
		except Exception as e:
			print("%d items not sent!"%len(sequence), e)

if __name__ == "__main__":
	tsd = InfluxClient()
	tsd.send("mem,host=host1 used_percent=24.43234543")
	tsd.send("mem,host=host1 used_percent=24.43234543")
	tsd.b.bgthread.join()

