from MinCutInstance.min_cut_intsance import MinCutInstance

def compute_min_cut_solution(grid, building_weight, scaling_factor, river_water_level, water_level_increase):
    solution = {}

    building_weight = building_weight
    min_cut_instance = MinCutInstance(grid, building_weight=building_weight, scaling_factor=scaling_factor)
    source, sink = min_cut_instance.build_graph(water_height=river_water_level + water_level_increase)

    vizualization = False
    if vizualization:
        min_cut_instance.visualize(max_edges_to_draw=10000, show_elevation=True)

    flow_value, smf = min_cut_instance.run_max_flow(source, sink)

    cut_cells = min_cut_instance.get_cut_cells(smf)

    flooded_buildings = min_cut_instance.get_buildings_in_cut(smf)

    print("Flooded Buildings: ", len(flooded_buildings))

    sandbags_needed = flow_value - len(flooded_buildings)*building_weight*scaling_factor
    sandbags_needed = sandbags_needed/scaling_factor

    print("needed sandbags:", sandbags_needed)

    solution['flow_value'] = flow_value
    solution['cut_cells'] = cut_cells
    solution['flooded_buildings'] = flooded_buildings
    solution['sandbags_needed'] = sandbags_needed

    #write file
    with open(f"solutions/cut_cells_{building_weight}.txt", "w") as f:
        f.write("cut_cells:" + ",".join(str(cell) for cell in cut_cells) + "\n")
        f.write("sandbags_needed:" + str(sandbags_needed) + "\n")
        f.write("flooded_buildings:" + ",".join(str(bid) for bid in flooded_buildings) + "\n")

    return solution