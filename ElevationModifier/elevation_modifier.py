from shapely.geometry import Polygon, Point
import numpy as np

class ElevationModifier:
    def __init__(self, raster_model_grid, grid_parameter="topographic__elevation"):
        self.raster_model_grid = raster_model_grid
        self.grid_parameter = grid_parameter

    def modify_elevation_from_polygon(self, increase_by, polygon_outline, flat_top=True):
        # Create a shapely Polygon object from the provided list of coordinates
        polygon = Polygon(polygon_outline)
        # Get the bounding box of the polygon
        min_x, min_y, max_x, max_y = polygon.bounds
        # Get all integer coordinates plus 0.5 within the bounding box
        coords = [(x, y) for x in range(int(np.floor(min_x)), int(np.ceil(max_x) + 1)) for y in range(int(np.floor(min_y)), int(np.ceil(max_y) + 1))]
        left_upper_x, left_upper_y = self.raster_model_grid.left_upper_edge_utm
        shape = self.raster_model_grid.shape
        # Iterate over all coordinates and check if they are within the polygon and if so, increase the elevation
        node_ids_to_increase = set()
        for coord in coords:
            one_meter_square = Point(coord[0] + 0.5, coord[1] + 0.5)
            if polygon.contains(one_meter_square):
                # Get the index of the cell containing the coordinate
                coord_as_cell = (coord[0] - left_upper_x, left_upper_y - coord[1])
                # Increase the elevation of the cell by the specified amount
                # print(coord_as_cell)
                node_id = self.raster_model_grid.grid_coords_to_node_id(int(coord_as_cell[1]), int(coord_as_cell[0]))
                node_ids_to_increase.add(node_id)

        if flat_top and node_ids_to_increase:
            minimum_height = min([self.raster_model_grid.at_node[self.grid_parameter][node_id] for node_id in node_ids_to_increase])
            for node_id in node_ids_to_increase:
                self.raster_model_grid.at_node[self.grid_parameter][node_id] = minimum_height + increase_by
        else:
            for node_id in node_ids_to_increase:
                self.raster_model_grid.at_node[self.grid_parameter][node_id] += increase_by
        return self.raster_model_grid