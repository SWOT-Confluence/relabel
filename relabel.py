from netCDF4 import Dataset
from numpy.ma import mean
from numpy.ma import median
from pathlib import Path

class Relabel:
	"""Class to relabel variables in a netCDF file."""

	def __init__(self):
		"""Track datasets and group objects."""

		self.orig_dataset = None
		self.swot_dataset = None
		self.sword_dataset = None
		self.swot_reach = None
		self.swot_node = None

	def relabel(self):
		nc_files = self.get_nc_files();
		for nc_file in nc_files:
			self.relabel_variables(nc_file)

	def get_nc_files(self):
		nc_file_path = Path.cwd() / 'input'
		return nc_file_path.glob('*.nc')

	def relabel_variables(self, file):
		"""Takes original netCDF file and creates three: SWOT Reach, SWOT node and SWORD of Science."""
		
		# Define datasets for original, swot, and sword data
		self.define_datasets(file)

		# Create dimensions and coordinate variables
		self.create_dim_coords()

		# Build groups for both SWOT and SWORD
		self.build_groups()

		# Build swot variables (reach and node)
		self.create_reach_vars()
		self.create_xs_vars()

		# Build sword variables
		self.create_sword_vars()

		# Close datasets
		self.orig_dataset.close()
		self.swot_dataset.close()
		self.sword_dataset.close()
	
	def define_datasets(self, file):
		"""Retrieve original dataset and define SWOT and SWORD of Science datasets."""

		# Retrieve original dataset 
		self.orig_dataset = Dataset(file, "r", format="NETCDF4")

		# Define new data set that contains: swot reach and node
		new_file = Path.cwd() / 'output' / 'swot' / self.get_name(file, "SWOT")
		self.swot_dataset = Dataset(new_file, "w", format="NETCDF4")
		self.swot_dataset.title = 'SWOT_' + self.orig_dataset.title

		# Define new data set that contains: sword of science
		new_file = Path.cwd() / 'output' / 'sword' / self.get_name(file, "SWORD")
		self.sword_dataset = Dataset(new_file, "w", format="NETCDF4")
		self.sword_dataset.title = 'SWORD_' + self.orig_dataset.title

	def get_name(self, file, type):
    	
		name = file.name.split("_")
		return type + "_" + name[2] + "_" + name[3]

	def create_dim_coords(self):
		"""Create dimensions and coordinate variables for each dimension."""
		
		# SWOT

		# nt and nx dimensions
		self.swot_dataset.createDimension("nt", 
			self.orig_dataset.dimensions["Time steps"].size)
		self.swot_dataset.createDimension("nx", 
			self.orig_dataset.dimensions["XS_90m"].size)

		# time step coordinate variable
		nt = self.swot_dataset.createVariable("nt", "i4", ("nt",))
		nt.units = "day"
		nt.long_name = "nt"
		nt[:] = self.orig_dataset["Time steps"][:]

		# nx coordinate variable
		nx = self.swot_dataset.createVariable("nx", "i4", ("nx",))
		nx.units = "orthogonals"
		nx.long_name = "nx"
		nx[:] = self.orig_dataset["XS_90m"][:]

		# SWORD
		# TBD

	def build_groups(self):
		"""Create swot reach, node and sword groupings."""

		# SWOT
		self.swot_reach = self.swot_dataset.createGroup("swot_reach")
		self.swot_node = self.swot_dataset.createGroup("swot_node")
		
		# SWORD
		# TBD

	def create_reach_vars(self):
		"""Create reach variables."""

		# slope2
		slope2_v = self.swot_reach.createVariable("slope2", "f8", 
			("nt",), fill_value = -999999999999)
		slope2_v.long_name = "enhanced water surface slope with respect to geoid"
		slope2_v.units = "m/m"
		slope2_v.valid_min = -0.001
		slope2_v.valid_max = 0.1
		slope2_v[:] = self.orig_dataset["Reach_Timeseries/S_1km"][:]

	def create_xs_vars(self):
		"""Create node variables."""

		# width
		width_v = self.swot_node.createVariable("width", "f8", ("nt", 
			"nx",), fill_value= -999999999999)
		width_v.long_name = "node width"
		width_v.units = "m"
		width_v.valid_min = 0.0
		width_v.valid_max = 100000
		width_v[:] = self.orig_dataset["XS_Timseries/W"][:]

		# wse
		wse_v = self.swot_node.createVariable("wse", "f8", ("nt", 
			"nx",), fill_value= -999999999999)
		wse_v.long_name = "water surface elevation with respect to the geoid"
		wse_v.units = "m"
		wse_v.valid_min = -1000
		wse_v.valid_max = 100000
		wse_v[:] = self.orig_dataset["XS_Timseries/H_1km"][:]

		# d_x_area
		dxa_v = self.swot_node.createVariable("d_x_area", "f8", ("nt", 
			"nx"), fill_value = -999999999999)
		dxa_v.long_name = "change in cross-sectional area"
		dxa_v.units = "m^2"
		dxa_v.valid_min = -10000000
		dxa_v.valid_max = 10000000
		dxa_v[:] = self.calculate_dxa(wse_v, width_v)

	def calculate_dxa(self, h, w):
		"""Calculate d_x_area for each cross section and time step from wse
		dataset and width dataset."""

		dH = h - median(h)
		return (median(w) - w) * (dH/2)

	def create_sword_vars(self):
		""" Create SWORD of Science variables."""

		# Q
		q_v = self.orig_dataset["XS_Timseries/Q"][:]

		# Qhat
		qhat_v = self.sword_dataset.createVariable("Qhat", "f8", 
			fill_value = -999999999999)
		qhat_v.long_name = "Qhat"
		qhat_v.units = "m^3/s"
		qhat_v.assignValue(mean(q_v))

if __name__ == "__main__":
	relabel = Relabel()
	relabel.relabel()
	print("Files written.")