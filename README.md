# Gasp
`Venturewithair 2020`
---

# Deliverables
- Analytics dashboard built with InfluxDB and Chronograph.
- Gasp UI with effluent concentrations per region in the city.

## Grid Explained
- The given dataset (`Helsinki_100x100m_3mo.nc4`) has 164 unique latitudes and 127 unique longitudes. That gives a total of `164 * 127 = 20828` points to track in this range for each time step. 
- We grouped these points into `100 points` by grouping latitudes and longitudes into 10 groups each. This number configurable (See `grid.py`).
- This reduces the size of the dataset considerably to be able to process and  visualize trends. 
- Finally, regions are defined as `cell_0_0`, `cell_0_1` ... `cell_9_9`. Each of them has a rectangular bounding box for simplicity. This can easily be extended to contain a polygon of different shapes for marking certain regions in the city.

## Scripts
- `influx.py` - InfluxDB client implementation
- `batcher.py` - For batching requests before sending to influx (used by `influx.py`)
- `grid.py` - Breaks down lat long range to a grid (as explained above).
- `aggregator.py` - Actually aggregates and sends data to the time series database(influx).

