# Grid Builder
import math
import bisect

class Grid:
	# Each cell in the grid will have 2 coordinates: top left and bottom right
	def __init__(self, lats, longs, tlats=10, tlongs=10):

		# will only contain the begin index of a range of lats/longs
		lats.sort()
		longs.sort()
		self.lats = []
		self.longs = []
		self.grid = {}
		for i in range(tlats):
			for j in range(tlongs):
				cell = "cell_%d_%d"%(i,j)
				self.grid[cell] = {"name": cell, "polygon": []}

		llats = []
		step = int(math.ceil(len(lats)/tlats))
		while len(lats):
			self.lats.append(lats[0])
			llats.append(lats[:step])
			lats = lats[step:]

		llongs = []
		step = int(math.ceil(len(longs)/tlongs))
		while len(longs):
			self.longs.append(longs[0])
			llongs.append(longs[:step])
			longs = longs[step:]

		for i,la in enumerate(llats):
			for j,lo in enumerate(llongs):
				cell = "cell_%d_%d"%(i,j)
				if len(la) and len(lo):
					self.grid[cell]['polygon'].append((float(la[0]), float(lo[0])))
					self.grid[cell]['polygon'].append((float(la[-1]), float(lo[-1])))
		self.llats = llats
		self.llongs = llongs

	def cell(self, lat, lon):
		i = min(len(self.lats)-1, bisect.bisect_left(self.lats, lat))
		j = min(len(self.longs)-1, bisect.bisect_left(self.longs, lon))
		c = "cell_%d_%d"%(i,j)
		return self.grid[c]

if __name__=="__main__":
	g = Grid([1,2,3,4], [3,4,6,2], 2, 2)
	print(g.cell(3.5, 4.5))
	print(g.lats, g.longs)
	print(g.grid)

