#########################################################
# FUNCTION to apply the basic minCut with NODE SPLITTING 
# also with building in the solution (NFI_2)
#########################################################

### PACKAGES 
from utils.general_operations import load_graph_and_positions
from utils.Simulation_Flooding import simulation_flood
from utils.Instanz_nodeSplitting_buildings import build_NFI_nodeSplitting_building
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from utils.visualization_MIP_pixel import visualize_MIPSolution_pixel
import pickle
import time

#------------------------------------------------------------------------------------------------------------------
### INPUT DATA 

# NFI Instanz 
#G, node_positions = load_graph_and_positions( "C:/Users/lenas/OneDrive/Masterarbeit/Graphen/StartingGraph_2.pkl")
G, node_positions = load_graph_and_positions( "C:/Users/lenas/OneDrive/Masterarbeit/Graphen/StartingGraph_diag.pkl")

# water rise 
w = 4

# Budget
#R = 10

# Importance of the building protection (low= buildings can be flooded / high= no building should be in danger by the flooding)
M = 25#100#25#7

# Generate flooding
floodedGraph = simulation_flood(G, w)

# Generate the NFI where all buildings are protected 
#NFI_2, node_positions = build_NFI_nodeSplitting(floodedGraph,w, node_positions)
NFI_3, node_positions = build_NFI_nodeSplitting_building(floodedGraph,w, node_positions, M)

#------------------------------------------------------------------------------------------------------------------
### Function Call without budget 

def compute_min_cut(NFI,w):
    # Calculate the minimum cut between s and t 
    cut_value, partition = nx.minimum_cut(NFI, "s", "t")

    # The two parts which we get after the cut (s-side and t-side)
    reachable, non_reachable = partition

    # Find the edges between the side to know where the graph is cutted
    cut_edges = [(u, v) for u in reachable for v in NFI.neighbors(u) if v in non_reachable]

    #------------------------------------------------------------------------------------------------------------------
    ### MARK THE NODE

    highlighted_nodes = set()
    
    for u, v in cut_edges:
        if NFI.nodes[u].get("category") == "empty" and NFI.nodes[v].get("category") == "copied_node":
            highlighted_nodes.add(u)
    #print(highlighted_nodes)

    #print(highlighted_nodes)
    protected = sum(1 for node in non_reachable if NFI.nodes[node].get("category") == "buildingOVER")
    print(f"The number of protected buildings is: {protected}")

    cost = 0
    for node in highlighted_nodes:
        if NFI.nodes[node].get("category")!="building":
            cost += 380 + w - NFI.nodes[node].get("elevation")
    print(f"The costs are {cost}")

    #------------------------------------------------------------------------------------------------------------------
    ### REMOVE COPIED NODES FROM NFI - could be added to the function

    for node in list(NFI.nodes):
        if NFI.nodes[node].get("category") == "copied_node":
            NFI.remove_node(node)

    return cut_value, cut_edges, highlighted_nodes, protected, cost, NFI


#------------------------------------------------------------------------------------------------------------------
### Example

# with node Splitting
# timeS=time.time()
#cut_value, cut_edges, highlighted_nodes_2, protected_2, cost_2, NFI_2 = compute_min_cut(NFI_2,w)
# timeE=time.time()
# t = timeE-timeS
# print(t)
# print("Minimaler Schnittwert:", cut_value)

# start_solution = {
#     "highlighted_nodes": highlighted_nodes_2,
#     "cut":cut_edges
# }

# # with node Splitting and buildings
# timeS=time.time()
cut_value, cut_edges, highlighted_nodes_3, protected_3, cost_3, NFI_3 = compute_min_cut(NFI_3,w)
# timeE=time.time()
# t = timeE-timeS
# print(t)
#print("Minimaler Schnittwert:", cut_value)

# start_solution = {
#     "highlighted_nodes": highlighted_nodes_3,
#     "cut":cut_edges
# }

#------------------------------------------------------------------------------------------------------------------
### REMOVE COPIED NODES FROM NFI - could be added to the function

# for node in list(NFI_2.nodes):
#     if NFI_2.nodes[node].get("category") == "copied_node":
#         NFI_2.remove_node(node)


# for node in list(NFI_3.nodes):
#     if NFI_3.nodes[node].get("category") == "copied_node":
#         NFI_3.remove_node(node)

#------------------------------------------------------------------------------------------------------------------
### SAVE OUTPUT
# #🛑CHANGE
# file_path = "C:/Users/lenas/OneDrive/Masterarbeit/Results_mincut/2.5.pkl"
# with open(file_path, "wb") as f:
#     pickle.dump(start_solution, f)

# print(f"Startlösung gespeichert unter: {file_path}")


#------------------------------------------------------------------------------------------------------------------
### VISUALIZATION

# plot with nodes as pixel map 
#visualize_MIPSolution_pixel(NFI_2, node_positions, highlighted_nodes_2)
visualize_MIPSolution_pixel(NFI_3, node_positions, highlighted_nodes_3)


#------------------------------------------------------------------------------------------------------------------
### plot wiht the edges which should be cutted 
# def visualize_min_cut(G, cut_edges, node_positions):
#     color_map = {
#         "building": "tan",
#         "river": "lightseagreen",
#         "empty": "darkseagreen",
#         "sink": "red",
#         "source": "midnightblue",
#         "buildingOVER": "orange"
#     }
    
#     node_colors = [color_map[G.nodes[node]["category"]] for node in G.nodes()]
    
#     plt.figure(figsize=(12, 12))

#     edge_colors = ["red" if (u, v) in cut_edges or (v, u) in cut_edges else "grey" for u, v in G.edges()]

#     #edges_to_remove = [(u,v) for u, v in G.edges if G.nodes[u].get("category")=="building" and G.nodes[v].get("category")=="buildingOVER"]
#     #G.remove_edges_from(edges_to_remove)

#     nx.draw(G, pos=node_positions, node_size=10, node_color=node_colors, with_labels=False, edge_color=edge_colors)
    

#     building_centroids = {}
#     for node_id, data in G.nodes(data=True):
#         if data["category"] == "building" and data.get("building_id") is not None:
#             building_id = data["building_id"]
#             if building_id not in building_centroids:
#                 building_centroids[building_id] = []
#             building_centroids[building_id].append(node_positions[node_id])

#     for building_id, points in building_centroids.items():
#         centroid_x = np.mean([p[0] for p in points])
#         centroid_y = np.mean([p[1] for p in points])
#         plt.text(centroid_x, centroid_y, str(building_id), fontsize=10, fontweight='bold', ha="center", va="center")

#     plt.title("Square Grid Graph Visualization with Min-Cut Edges in Red")
#     plt.xlabel("X Coordinate")
#     plt.ylabel("Y Coordinate")
#     plt.show()



#visualize_min_cut(NFI, cut_edges, node_positions)
#visualize_min_cut(NFI_2, cut_edges, node_positions)
