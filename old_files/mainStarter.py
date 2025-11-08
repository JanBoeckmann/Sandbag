###############################################################
### Main Skript for creating the Starting Graph   
###
################################################################

#############
#### PACKAGES 
#############

from utils.general_operations import load_json, save_graph_and_positions
from utils.grid_graph import create_square_grid_graph_with_ids
from utils.visualization_graph import visualize_square_grid_graph_with_ids
from shapely.geometry import Polygon
from DataReader.data_reader import DataReader
import networkx as nx
from ElevationModifier.elevation_modifier import ElevationModifier
from CoordinateConversion.utils import utm_to_latlon
from utils.grid_graph_diag import create_square_grid_graph_with_ids_diag

###########################
#### INPUT DATA PREPARATION  
###########################

#buildings_data = load_json("./data/Auloh_building_sub.json")                               ## -> necessary for subgraph
buildings_data = load_json("./data/Auloh_buildings.json")
rivers_data = load_json("./data/30a 1h_buildings.json")
river_polygons = [Polygon(river["basin_outline"]) for river in rivers_data["basins"]]

### NECESSARY FOR THE ELEVATION DATA 
# Path to building data
#buildings_path = "./data/Auloh_building_sub.json"                                          ## -> necessary for subgraph
buildings_path = "./data/Auloh_buildings.json"
data_reader = DataReader(buildings_path)

#print(data_reader.get_min_max_coordinates())
#print(data_reader.grid)
left_upper_x, left_upper_y = data_reader.get_upper_left_coordinate()

# Increase elevation of buildings by 5m
for building in data_reader.buildings['buildings']:
    building_outline = building['building_outline']
    building_outline_utm = []
    for bo in building_outline:
        utm_coords = utm_to_latlon((bo[0], bo[1]))
        building_outline_utm.append(utm_coords)
    elevation_modifier = ElevationModifier(data_reader.grid, left_upper_x=left_upper_x, left_upper_y=left_upper_y)
    grid = elevation_modifier.modify_elevation_from_polygon(increase_by=5, polygon_outline=building_outline_utm)
###

all_points = [point for building in buildings_data["buildings"] for point in building["building_outline"]] + \
             [point for basin in rivers_data["basins"] for point in basin["basin_outline"]]
bounding_box = (min(p[0] for p in all_points), min(p[1] for p in all_points),
                max(p[0] for p in all_points), max(p[1] for p in all_points))

resolution = 0.00001

#grid = data_reader.grid                                                # ->  can be used if we do not want to use the modified grid 


###########################################
#### FUNCTION CALL TO CREATE THE GRID GRAPH 
###########################################

# OLD
#G, node_positions, overlap_vector = create_square_grid_graph_with_ids(bounding_box, resolution, buildings_data, river_polygons)#, elevation_csv_path)

#G, node_positions, overlap_vector = create_square_grid_graph_with_ids(buildings_path, bounding_box, resolution, buildings_data, river_polygons, grid=grid)
G, node_positions, overlap_vector = create_square_grid_graph_with_ids_diag(buildings_path, bounding_box, resolution, buildings_data, river_polygons, grid=grid)

################################
#### SAVING OF THE CREATED GRAPH
################################

#save_graph_and_positions(G, node_positions, "C:/Users/lenas/OneDrive/Masterarbeit/Graphen/StartingGraph_SUB.pkl")
#save_graph_and_positions(G, node_positions, "C:/Users/lenas/OneDrive/Masterarbeit/Graphen/StartingGraph_sub_neu1.pkl")
#save_graph_and_positions(G, node_positions, "C:/Users/lenas/OneDrive/Masterarbeit/Graphen/StartingGraph_SUB.pkl")
#print(nx.get_node_attributes(G, "elevation"))
#save_graph_and_positions(G, node_positions, "C:/Users/lenas/OneDrive/Masterarbeit/Graphen/StartingGraph_2.pkl")
save_graph_and_positions(G, node_positions, "C:/Users/lenas/OneDrive/Masterarbeit/Graphen/StartingGraph_diag.pkl")

#######################################
#### VISUALIZATION OF THE CREATED GRAPH 
#######################################

visualize_square_grid_graph_with_ids(G, node_positions)
#print("Overlap Vector:", overlap_vector)
