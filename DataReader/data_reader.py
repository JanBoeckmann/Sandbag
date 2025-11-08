from BayernAtlas.BayerAtlas import BayernAtlas
import json

class DataReader:
    def __init__(self, buildings_data_path):
        self.buildings_data_path = buildings_data_path
        self.buildings = self.read_buildings_data()
        self.grid = self.get_raster_model_grid()
        self.data = None

    def read_buildings_data(self):
        with open(self.buildings_data_path, 'r') as file:
            buildings = json.load(file)
        return buildings
    
    def get_min_max_coordinates(self):
        min_lat = float('inf')
        max_lat = float('-inf')
        min_long = float('inf')
        max_long = float('-inf')

        for building in self.buildings['buildings']:
            for coordinate in building['building_outline']:
                lat, long = coordinate
                if lat < min_lat:
                    min_lat = lat
                if lat > max_lat:
                    max_lat = lat
                if long < min_long:
                    min_long = long
                if long > max_long:
                    max_long = long

        return min_lat, max_lat, min_long, max_long

    def get_upper_left_coordinate(self):
        min_lat, max_lat, min_long, max_long = self.get_min_max_coordinates()
        bayern_atlas = BayernAtlas(min_lat=min_lat, min_long=min_long, max_lat=max_lat, max_long=max_long)
        utm32_min_lat, _, _, utm32_max_long = bayern_atlas.get_utm32_coordinates()
        left_upper_x = utm32_min_lat * 1000 + 0.5
        left_upper_y = utm32_max_long * 1000 + 999.5
        return left_upper_x, left_upper_y

    def get_raster_model_grid(self):
        min_lat, max_lat, min_long, max_long = self.get_min_max_coordinates()
        bavaria = BayernAtlas(min_lat, min_long, max_lat, max_long)
        grid = bavaria.compute_raster_model_grid()
        return grid