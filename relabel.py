from netCDF4 import Dataset
from numpy.ma import mean
from numpy.ma import median
from pathlib import Path

class Relabel:
	"""Class to relabel variables in a netCDF file."""

	def __init__(self):
		"""Track group and dimension objects."""

		self.xs_group = None
		self.reach_group = None

	def relabel(self):
		nc_files = self.get_nc_files();
		for nc_file in nc_files:
			self.relabel_variables(nc_file)

	def get_nc_files(self):
		nc_file_path = Path.cwd() / 'input'
		return nc_file_path.glob('*.nc')

	def relabel_variables(self, file):
		"""Takes an netCDF file and relabels groups and W, H_90m, S_90m variables."""
		
		# Define original dataset and new dataset
		orig_dataset = Dataset(file, "r", format="NETCDF4")
		out_file = Path.cwd() / 'output' / file.name
		new_dataset = Dataset(out_file, "w", format="NETCDF4")

		# Create cross section and reach groups
		self.xs_group = new_dataset.createGroup("XS_Time_Series")
		self.reach_group = new_dataset.createGroup("Reach_Time_Series")

		# Set new dataset title
		new_dataset.title = orig_dataset.title

		# Create dimensions
		self.create_dimensions(orig_dataset, new_dataset)
		
		# Create root group variables
		self.create_root_vars(orig_dataset, new_dataset)
		
		# Create xs group variables
		self.create_xs_vars(orig_dataset)

		# Create reach group variables
		self.create_reach_vars(orig_dataset)

	def create_dimensions(self, orig_dataset, new_dataset):
		"""Create dimensions from original dataset in new dataset."""

		new_dataset.createDimension("XS_90m", orig_dataset.dimensions["XS_90m"].size)
		new_dataset.createDimension("Time_Steps", orig_dataset.dimensions["Time steps"].size)
		new_dataset.createDimension("Stageloc_1km", orig_dataset.dimensions["Stageloc_1km"].size)
		new_dataset.createDimension("Reach", orig_dataset.dimensions["Reach"].size)
		new_dataset.createDimension("nchar", orig_dataset.dimensions["nchar"].size)

	def create_root_vars(self, orig_dataset, new_dataset):
		"""Create root group level coordinate variables."""

		# XS_90m
		xs_90m_v = new_dataset.createVariable("XS_90m", "i4", ("XS_90m",))
		xs_90m_v.units = "orthogonals"
		xs_90m_v.long_name = "XS_90m"
		xs_90m_v[:] = orig_dataset["XS_90m"][:]		

		# Time_Steps
		time_steps_v = new_dataset.createVariable("Time_Steps", "i4", ("Time_Steps",))
		time_steps_v.units = "day"
		time_steps_v.long_name = "Time Steps"
		time_steps_v[:] = orig_dataset["Time steps"][:]		

		# Stageloc_1km
		stageloc_1km_v = new_dataset.createVariable("Stageloc_1km", "i4", ("Stageloc_1km",))
		stageloc_1km_v.units = "orthogonals"
		stageloc_1km_v.long_name = "Stageloc_1km"
		stageloc_1km_v[:] = orig_dataset["Stageloc_1km"][:]		

		# Reach
		reach_v = new_dataset.createVariable("Reach", "i4", ("Reach",))
		reach_v.units = "RiverReaches"
		reach_v.long_name = "Reach"
		reach_v[:] = orig_dataset["Reach"][:]		

	def create_xs_vars(self, orig_dataset):
		"""Create XS Time Series group level variables."""

		# width
		width_v = self.xs_group.createVariable("width", "f8", ("Time_Steps", 
			"XS_90m",), fill_value= -999999999999)
		width_v.long_name = "node width"
		width_v.units = "m"
		width_v.valid_min = 0.0
		width_v.valid_max = 100000
		width_v[:] = orig_dataset["XS_Timseries/W"][:]

		# wse
		wse_v = self.xs_group.createVariable("wse", "f8", ("Time_Steps", 
			"XS_90m",), fill_value= -999999999999)
		wse_v.long_name = "water surface elevation with respect to the geoid"
		wse_v.units = "m"
		wse_v.valid_min = -1000
		wse_v.valid_max = 100000
		wse_v[:] = orig_dataset["XS_Timseries/H_90m"][:]

		# H_1km
		h_1km_v = self.xs_group.createVariable("H_1km", "f8", ("Time_Steps", 
			"Stageloc_1km"), fill_value = 99999.0)
		h_1km_v.long_name = "water surface elevation 1km"
		h_1km_v.units = "m"
		h_1km_v[:] = orig_dataset["XS_Timseries/H_1km"][:]

		# Q
		q_v = self.xs_group.createVariable("Q", "f8", ("Time_Steps", 
			"Stageloc_1km"), fill_value = 99999.0)
		q_v.long_name = "discharge"
		q_v.units = "cubic meters per second"
		q_v[:] = orig_dataset["XS_Timseries/Q"][:]

		# Qhat
		qhat_v = self.xs_group.createVariable("Qhat", "f8", ("Time_Steps"), 
			fill_value = 99999.0)
		qhat_v.long_name = "Qhat"
		qhat_v.units = "??"
		qhat_v[:] = mean(q_v[:], axis=1)

		# d_x_area
		dxa_v = self.xs_group.createVariable("d_x_area", "f8", ("Time_Steps", 
			"XS_90m"), fill_value = -999999999999)
		dxa_v.long_name = "change in cross-sectional area"
		dxa_v.units = "m^2"
		dxa_v.valid_min = -10000000
		dxa_v.valid_max = 10000000
		dxa_v[:] = self.calculate_dxa(h_1km_v, width_v)

	def calculate_dxa(self, h, w):
		"""Calculate d_x_area for each cross section and time step from H_1km
		dataset and width dataset."""

		dH = h - median(h)
		return (median(w) - w) * (dH/2)

	def create_reach_vars(self, orig_dataset):
		"""Create Reach Time Series group variables."""

		# Q
		q_v = self.reach_group.createVariable("Q", "f8", ("Time_Steps", 
			"Reach",), fill_value = 99999.0)
		q_v.long_name = "mean discharge"
		q_v.units = "curbic meter per second"
		q_v[:] = orig_dataset["Reach_Timseries/Q"][:]

		# slope2
		slope2_v = self.reach_group.createVariable("slope2", "f8", 
			("Time_Steps", "Reach"), fill_value = -999999999999)
		slope2_v.long_name = "enhanced water surface slope with respect to geoid"
		slope2_v.units = "m/m"
		slope2_v[:] = orig_dataset["Reach_Timeseries/S_90m"][:]
		
		# S_1km
		s_1km_v = self.reach_group.createVariable("S_1km", "f8", ("Time_Steps", 
			"Reach"), fill_value = 99999.0)
		s_1km_v.long_name = "Slope_1km"
		s_1km_v.units = "m/m"
		s_1km_v[:] = orig_dataset["Reach_Timeseries/S_1km"][:]

		# GridID
		gridid_v = self.reach_group.createVariable("GridID", "S1", ("Reach", "nchar"))
		gridid_v[:] = orig_dataset["Reach_Timeseries/GridID"][:]

		# HydroID
		hydroid_v = self.reach_group.createVariable("HydroID", "f8", ("Reach", 
			"Reach"), fill_value = 99999.0)
		hydroid_v.long_name = "HydroID"
		hydroid_v.units = "dimensionless"
		hydroid_v[:] = orig_dataset["Reach_Timeseries/HydroID"][:]

		# NextDownID
		ndid_v = self.reach_group.createVariable("NextDownID", "f8", ("Reach", 
			"Reach"), fill_value = 99999.0)
		ndid_v.long_name = "NextDownID"
		ndid_v.units = "dimensionless"
		ndid_v[:] = orig_dataset["Reach_Timeseries/NextDownID"][:]

if __name__ == "__main__":
	relabel = Relabel()
	relabel.relabel()