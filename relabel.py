from netCDF4 import Dataset
from numpy.ma import mean
from numpy.ma import median
from pathlib import Path

class Relabel:
	"""Class to relabel variables in a netCDF file."""

	def __init__(self):
		"""Track datasets and group objects."""

		self.orig_dataset = None
		self.swot_dataset_reach = None
		self.swot_dataset_node = None
		self.sword_dataset = None

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

		# Build swot datasets
		self.build_swot_reach()
		self.build_swot_node()

		# Build sword dataset
		self.build_sword()
	
	def define_datasets(self, file):
		"""Retrieve original dataset and define SWOT and SWORD of Science datasets."""

		# Retrieve original dataset 
		self.orig_dataset = Dataset(file, "r", format="NETCDF4")

		# Define podaac/SWOT dataset reach
		swot_file = Path.cwd() / 'swot_reach' / file.name
		self.swot_dataset_reach = Dataset(swot_file, "w", format="NETCDF4")

		# Define podaac/SWOT dataset node
		swot_file = Path.cwd() / 'swot_node' / file.name
		self.swot_dataset_node = Dataset(swot_file, "w", format="NETCDF4")

		# Define SWORD of Science dataset
		sword_file = Path.cwd() / 'sword' / file.name
		self.sword_dataset = Dataset(sword_file, "w", format="NETCDF4")

	def build_swot_reach(self):
		"""Build SWOT NetCDF reach files from original dataset."""

		# Set title
		self.swot_dataset_reach.title = self.orig_dataset.title

		# Create dimensions
		self.swot_dataset_reach.createDimension("nt", 
			self.orig_dataset.dimensions["Time steps"].size)
		self.swot_dataset_reach.createDimension("nx", 
			self.orig_dataset.dimensions["Reach"].size)
		
		# Create reach variable(s)
		self.create_reach_vars()

	def create_reach_vars(self):
		"""Create reach variable(s)."""

		# slope2
		slope2_v = self.swot_dataset_reach.createVariable("slope2", "f8", 
			("nt", "nx"), fill_value = -999999999999)
		slope2_v.long_name = "enhanced water surface slope with respect to geoid"
		slope2_v.units = "m/m"
		slope2_v.valid_min = -0.001
		slope2_v.valid_max = 0.1
		slope2_v[:] = self.orig_dataset["Reach_Timeseries/S_90m"][:]

	def build_swot_node(self):
		"""Build SWOT NetCDF node files from original dataset."""

		# Set new dataset title
		self.swot_dataset_node.title = self.orig_dataset.title

		# Create dimensions
		self.swot_dataset_node.createDimension("nt", 
			self.orig_dataset.dimensions["Time steps"].size)
		self.swot_dataset_node.createDimension("nx", 
			self.orig_dataset.dimensions["XS_90m"].size)
		
		# Create xs variables
		self.create_xs_vars()

	def create_xs_vars(self):
		"""Create coordinate and Node group level variables."""

		# width
		width_v = self.swot_dataset_node.createVariable("width", "f8", ("nt", 
			"nx",), fill_value= -999999999999)
		width_v.long_name = "node width"
		width_v.units = "m"
		width_v.valid_min = 0.0
		width_v.valid_max = 100000
		width_v[:] = self.orig_dataset["XS_Timseries/W"][:]

		# wse
		wse_v = self.swot_dataset_node.createVariable("wse", "f8", ("nt", 
			"nx",), fill_value= -999999999999)
		wse_v.long_name = "water surface elevation with respect to the geoid"
		wse_v.units = "m"
		wse_v.valid_min = -1000
		wse_v.valid_max = 100000
		wse_v[:] = self.orig_dataset["XS_Timseries/H_1km"][:]

		# d_x_area
		dxa_v = self.swot_dataset_node.createVariable("d_x_area", "f8", ("nt", 
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

	def build_sword(self):
		"""Build NetCDF to represent data in SWORD of Science."""
		
		# Set new dataset title
		self.sword_dataset.title = self.orig_dataset.title

		# Create dimensions
		self.sword_dataset.createDimension("nt", 
			self.orig_dataset.dimensions["Time steps"].size)		
		
		# Create sword variables
		self.create_sword_vars()

	def create_sword_vars(self):
		""" Create SWORD of Science variables."""

		# Q
		q_v = self.orig_dataset["XS_Timseries/Q"][:]

		# Qhat
		qhat_v = self.sword_dataset.createVariable("Qhat", "f8", ("nt"), 
			fill_value = -999999999999)
		qhat_v.long_name = "Qhat"
		qhat_v.units = "m^3/s"
		qhat_v[:] = mean(q_v[:], axis=1)

if __name__ == "__main__":
	relabel = Relabel()
	relabel.relabel()
	print("Files written.")