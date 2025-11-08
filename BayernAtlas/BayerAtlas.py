import utm
import math
from BayernAtlas.utils import download_file
# from .utils import download_file
import numpy as np
from landlab import RasterModelGrid
import zipfile
import os
from CoordinateConversion.utils import latlon_to_utm

class BayernAtlas:
    def __init__(self, min_lat, min_long, max_lat, max_long):
        self.min_lat = min_lat
        self.min_long = min_long
        self.max_lat = max_lat
        self.max_long = max_long

    def unpack_zip(self, zip_file, extract_to):
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

    def get_utm32_coordinates(self):
        u_min_x, u_min_y = latlon_to_utm((self.min_lat, self.min_long))
        u_max_x, u_max_y = latlon_to_utm((self.max_lat, self.max_long))
        utm32_min_x = math.floor(u_min_x/1000)
        utm32_max_x = math.floor(u_max_x/1000)
        utm32_min_y = math.floor(u_min_y/1000)
        utm32_max_y = math.floor(u_max_y/1000) 

        return utm32_min_x, utm32_max_x, utm32_min_y, utm32_max_y

    def fetch_data(self):
        utm32_min_x, utm32_max_x, utm32_min_y, utm32_max_y = self.get_utm32_coordinates()

        output_directory = "./downloads"

        for lat in range(utm32_min_x, utm32_max_x + 1):
            for long in range(utm32_min_y, utm32_max_y + 1):
                filename = str(lat) + "_" + str(long) + ".zip"
                url = "https://download1.bayernwolke.de/a/dgm/dgm1xyz/" + filename
                download_file(url, output_directory, filename)

    def compute_raster_model_grid(self):
        utm32_min_x, utm32_max_x, utm32_min_y, utm32_max_y = self.get_utm32_coordinates()
        dtm_files = []
        for lat in range(utm32_min_x, utm32_max_x + 1):
            for long in range(utm32_min_y, utm32_max_y + 1):
                archive_file = str(lat) + "_" + str(long) + ".zip"
                self.unpack_zip("./data/" + archive_file, "./data")
                filename = str(lat) + "_" + str(long) + ".txt"
                dtm_files.append("./data/" + filename)
        # Initialize variables to store combined data
        combined_x = []
        combined_y = []
        combined_elev = []

        # Read data from each text file and combine it
        for dtm_file in dtm_files:
            x, y, elev = np.loadtxt(dtm_file, unpack=True)
            combined_x.extend(x)
            combined_y.extend(y)
            combined_elev.extend(elev)

        # Create a grid using Landlab with the combined data
        spacing = np.mean(np.diff(combined_x))  # Assuming uniform spacing
        spacing = 1 # I think we already know the spacing here, but we might double chack this
        grid = RasterModelGrid(shape=(len(np.unique(combined_y)), len(np.unique(combined_x))), xy_spacing=spacing)

        # Sort the combined data by x and y coordinates
        sorted_indices = np.lexsort((combined_x, -np.array(combined_y)))
        combined_x = np.array(combined_x)[sorted_indices]
        combined_y = np.array(combined_y)[sorted_indices]
        combined_elev = np.array(combined_elev)[sorted_indices]
        grid.at_node["topographic__elevation"] = np.array(combined_elev).reshape(grid.shape)
        
        # try:
        #     #TODO: This is now hardcoded for Straubing. It definitely needs to be fixed
        #     outlets = grid.set_watershed_boundary_condition_outlet_id(grid.at_node["topographic__elevation"], 3475998, nodata_value=-9999.0, return_outlet_id=True)
        # except Exception as error:
        #     print("an error has occurred")

        #delete all txt files in dtm_files to save disc space
        for file in dtm_files:
            os.remove(file)

        return grid
            