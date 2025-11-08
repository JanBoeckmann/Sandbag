#from utils.grid_graph_diag import create_square_grid_graph_ortools
from utils.general_operations import load_json
from shapely.geometry import Polygon
from DataReader.data_reader import DataReader
import matplotlib.pyplot as plt
from ElevationModifier.elevation_modifier import ElevationModifier
import numpy as np
from CoordinateConversion.utils import utm_to_latlon, latlon_to_utm
from RelevantGridGetter.relevant_grid_getter import RelevantGridGetter
from MinCutInstance.min_cut_intsance import MinCutInstance
from landlab import RasterModelGrid
import time
from utils.compute_min_cut_solution import compute_min_cut_solution
from IntegerProgram.integer_program import IntegerProgram

buildings_path = "./data/Auloh_buildings.json"
data_reader = DataReader(buildings_path)
rivers_data = load_json("./data/30a 1h_buildings.json")
river_polygons = [Polygon(river["basin_outline"]) for river in rivers_data["basins"]]
grid = data_reader.get_raster_model_grid()
river_water_level = 380
water_level_increase = 2.5
scaling_factor = 1e6

grid.add_zeros("river", at="node")
grid.add_zeros("building_ids", at="node")

left_upper_x, left_upper_y = data_reader.get_upper_left_coordinate()

grid.left_upper_edge_utm = (left_upper_x, left_upper_y)

elevation_modifier = ElevationModifier(grid, grid_parameter="river")

for river_polygon in river_polygons:
    river_outline = river_polygon.exterior.coords
    river_outline_utm = []
    for ro in river_outline:
        utm_coords = latlon_to_utm((ro[0], ro[1]))
        river_outline_utm.append(utm_coords)
    grid = elevation_modifier.modify_elevation_from_polygon(increase_by=1, polygon_outline=river_outline_utm, flat_top=False)

elevation_modifier = ElevationModifier(grid, grid_parameter="building_ids")
for building in data_reader.buildings['buildings']:
    building_outline = building['building_outline']
    building_outline_utm = []
    for bo in building_outline:
        utm_coords = latlon_to_utm((bo[0], bo[1]))
        building_outline_utm.append(utm_coords)
    grid = elevation_modifier.modify_elevation_from_polygon(increase_by=building['building_id'] - 20000, polygon_outline=building_outline_utm, flat_top=True)

relevant_grid_getter = RelevantGridGetter(grid)
grid = relevant_grid_getter.get_border_of_river()
grid = relevant_grid_getter.get_relevant_nodes(river_height=river_water_level, elevation_threshold=water_level_increase)

use_small_for_testing = False

if use_small_for_testing:

    # Define bounds
    x_min, x_max = 260, 300
    y_min, y_max = 390, 400

    # Node coordinates
    x = grid.x_of_node
    y = grid.y_of_node

    # Compute number of rows and columns in grid
    nrows, ncols = grid.shape

    # Reshape x and y to 2D arrays
    x_grid = x.reshape(nrows, ncols)
    y_grid = y.reshape(nrows, ncols)

    # Find rows and columns within bounds
    rows_in_bounds = np.where((y_grid[:,0] >= y_min) & (y_grid[:,0] <= y_max))[0]
    cols_in_bounds = np.where((x_grid[0,:] >= x_min) & (x_grid[0,:] <= x_max))[0]

    # Slice the grid arrays
    sub_nrows = len(rows_in_bounds)
    sub_ncols = len(cols_in_bounds)

    # Create new RasterModelGrid
    subgrid = RasterModelGrid((sub_nrows, sub_ncols), xy_spacing=(grid.dx, grid.dy))

    # Copy data from original grid (for example, topography)
    if 'topographic__elevation' in grid.at_node:
        subgrid.add_field('node', 'topographic__elevation',
                        grid.at_node['topographic__elevation'].reshape(nrows, ncols)[
                            rows_in_bounds.min():rows_in_bounds.max()+1,
                            cols_in_bounds.min():cols_in_bounds.max()+1
                        ].flatten()
                        )
    if 'river' in grid.at_node:
        subgrid.add_field('node', 'river',
                        grid.at_node['river'].reshape(nrows, ncols)[
                            rows_in_bounds.min():rows_in_bounds.max()+1,
                            cols_in_bounds.min():cols_in_bounds.max()+1
                        ].flatten()
                        )
    if 'building_ids' in grid.at_node:
        subgrid.add_field('node', 'building_ids',
                        grid.at_node['building_ids'].reshape(nrows, ncols)[
                            rows_in_bounds.min():rows_in_bounds.max()+1,
                            cols_in_bounds.min():cols_in_bounds.max()+1
                        ].flatten()
                        )
    if 'border_of_river' in grid.at_node:
        subgrid.add_field('node', 'border_of_river',
                        grid.at_node['border_of_river'].reshape(nrows, ncols)[
                            rows_in_bounds.min():rows_in_bounds.max()+1,
                            cols_in_bounds.min():cols_in_bounds.max()+1
                        ].flatten()
                        )
    if 'relevant' in grid.at_node:
        subgrid.add_field('node', 'relevant',
                        grid.at_node['relevant'].reshape(nrows, ncols)[
                            rows_in_bounds.min():rows_in_bounds.max()+1,
                            cols_in_bounds.min():cols_in_bounds.max()+1
                        ].flatten()
                        )
        
    grid = subgrid

dichotomic_search = False
if dichotomic_search:
    solutions = {}

    solution_0 = compute_min_cut_solution(grid, building_weight=10, scaling_factor=scaling_factor, river_water_level=river_water_level, water_level_increase=water_level_increase)
    solutions[0] = solution_0
    solution_100 = compute_min_cut_solution(grid, building_weight=100, scaling_factor=scaling_factor, river_water_level=river_water_level, water_level_increase=water_level_increase)
    solutions[100] = solution_100

    lambda_start = (solution_100['sandbags_needed']-solution_0['sandbags_needed']) / (len(solution_0['flooded_buildings']) - len(solution_100['flooded_buildings']))
    print("Lambda start:", lambda_start)

    queue = {lambda_start}

    while len(queue) > 0:
        lam = queue.pop()
        if lam in solutions:
            continue
        print("Computing solution for lambda =", lam)
        solution_lam = compute_min_cut_solution(grid, building_weight=lam, scaling_factor=scaling_factor, river_water_level=river_water_level, water_level_increase=water_level_increase)
        solutions[lam] = solution_lam

        # Check if we need to add new lambdas to the queue
        flooded_lam = len(solution_lam['flooded_buildings'])
        print(solutions.keys())
        print(lam)
        lower_solution_lam = max([l for l in solutions.keys() if l < lam])
        higher_solution_lam = min([l for l in solutions.keys() if l > lam])
        flooded_lower = len(solutions[lower_solution_lam]['flooded_buildings'])
        flooded_higher = len(solutions[higher_solution_lam]['flooded_buildings'])
        solution_lower = solutions[lower_solution_lam]
        solution_higher = solutions[higher_solution_lam]

        if flooded_lam != flooded_lower and flooded_lam != flooded_higher:
            new_lambda_lower = (solution_lam['sandbags_needed']-solution_lower['sandbags_needed']) / (len(solution_lower['flooded_buildings']) - len(solution_lam['flooded_buildings']))
            queue.add(new_lambda_lower)

            new_lambda_higher = (solution_higher['sandbags_needed']-solution_lam['sandbags_needed']) / (len(solution_lam['flooded_buildings']) - len(solution_higher['flooded_buildings']))
            queue.add(new_lambda_higher)

    print("Computed solutions for lambdas:", solutions.keys())

    flooded_buildings = solution_0['flooded_buildings']
    cut_cells = solution_0['cut_cells']

    print("sandbags needed in solution 100:", solution_100['sandbags_needed'])

plot = True
if plot and dichotomic_search:
    # Plot 1: Elevation grid
    plt.figure(figsize=(20, 4))
    plt.subplot(1, 4, 1)
    elevation = grid.at_node['topographic__elevation'].reshape(grid.shape)
    plt.imshow(elevation, cmap='terrain')
    plt.colorbar(label='Elevation (m)')
    plt.title('Topographic Elevation Grid')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')

    # Plot 2: River mask with border
    plt.subplot(1, 4, 2)
    river_mask = grid.at_node['border_of_river'].reshape(grid.shape) * 2 + grid.at_node['river'].reshape(grid.shape)
    plt.imshow(river_mask, cmap='Blues')
    plt.colorbar(label='River')
    plt.title('River Mask with Border')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')

    # Plot 3: Building IDs with Flooded Buildings Highlighted
    plt.subplot(1, 4, 3)
    building_ids_grid = grid.at_node['building_ids'].reshape(grid.shape)
    plt.imshow(building_ids_grid, cmap='terrain')
    plt.colorbar(label='Building ID')
    plt.title('Building IDs (Flooded Highlighted)')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')

    # Overlay flooded buildings
    flooded_mask = np.isin(building_ids_grid, flooded_buildings)
    flooded_y, flooded_x = np.where(flooded_mask)
    plt.scatter(flooded_x, flooded_y, marker='s', color='red', s=20, label='Flooded Buildings', edgecolors='black')
    plt.legend(loc='upper right')

    # Plot 4: Relevant Nodes with Cut Cells
    plt.subplot(1, 4, 4)
    relevant_nodes = grid.at_node['relevant'].reshape(grid.shape) + grid.at_node['border_of_river'].reshape(grid.shape) * 2
    plt.imshow(relevant_nodes, cmap='Reds')
    plt.colorbar(label='Relevant Node')
    plt.title('Relevant Nodes & Cut Cells')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')

    # Overlay cut cells
    cut_cells_mask = np.zeros(grid.shape, dtype=bool)
    for node in cut_cells:
        row = node // grid.shape[1]
        col = node % grid.shape[1]
        cut_cells_mask[row, col] = True
    plt.scatter(
        np.where(cut_cells_mask)[1],  # x (cols)
        np.where(cut_cells_mask)[0],  # y (rows)
        marker='o', color='cyan', s=20, label='Cut Cells', edgecolors='black'
    )
    plt.legend(loc='upper right')

    plt.tight_layout()
    plt.show()

integer_programming = False
if integer_programming:
    integer_program = IntegerProgram(grid, building_weight=1, water_height=river_water_level + water_level_increase)
    integer_program.formulate_problem(number_protected_buildings=0)