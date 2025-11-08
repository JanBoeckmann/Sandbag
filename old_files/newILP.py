#####################################################################
### Code for the Integer Problem - MBSMP - new Sandbags in Objective
# INPUT: NFI-Instanz 
# OUTPUT: the position of the sandbags 
#####################################################################

### PACKAGES 
from utils.general_operations import load_graph_and_positions
from Simulation_Flooding import simulation_flood
from Instanz_MBSMP import build_NFI
import pulp
from pulp import PULP_CBC_CMD
from pulp import HiGHS
from utils.visualization_MIPSolution import visualize_MIPSolution
from utils.visualization_MIP_pixel import visualize_MIPSolution_pixel
import time
import networkx as nx
import pickle


######################################################################################################################
# FUNCTION
#
# INPUT: NFI Instanz, the Budget, lambda: value which indicates how important the budget is in the objective function 
#        time: time limit for the solver and mipGap: the used mipGap for the solver
# OUTPUT: Objective value and the position of the sandbag (nodes to remove)
# INFORMATION: The solver which wants to be used has to be setted in line 137
########################################################################################################################

def solveModel(NFI, R, l=0, timeSol=float("inf"), mipGap=0):

    # number nodes 
    nodes = list(NFI.nodes)
    #print(nodes)

    # number edges 
    edges = list(NFI.edges)

    #print(edges)
    
    river_node = [node for node in nodes if NFI.nodes[node].get("category") == "river"]

    building_over = [node for node in nodes if NFI.nodes[node].get("category") == "buildingOVER"]

    # removal costs 
    removal_costs = {n: NFI.nodes[n].get("removal_cost") for n in nodes}
    rNodes = [node for node in nodes if NFI.nodes[node].get("removal_cost")<1000000000]

    
    #_________________________________________________________________________________________________________________________


    ### GENERATE THE PROBLEM 

    problem = pulp.LpProblem("Minimization_Problem_Sandbags", pulp.LpMinimize) # We have to minimize the transported capacity from s - t

    ### DECISION VARIABLE 

    # 1 if water can reach the node i 
    y = pulp.LpVariable.dicts("y", nodes, cat = "Binary" )
    # 1 if node i is removed 
    x = pulp.LpVariable.dicts("x", nodes, cat="Binary")

    ### OBJECTIVE FUNCTION

    #problem += pulp.lpSum(capacities[edge] * beta[edge] for edge in edges), "Minimize the water flow from s to t"
    problem += (pulp.lpSum(removal_costs[node] * x[node] for node in nodes)+ pulp.lpSum(y[i] * 3000 for i in building_over))
    #problem += (pulp.lpSum(y[i] for i in building_over))
    #problem += (pulp.lpSum(y[i]*w[i] for i in building_over)) # if building have weights

    ### CONSTRAINTS

    # (I) BUDGET
    problem += pulp.lpSum(y[i] for i in building_over) == R #<=

    # (II)
    for i in river_node:
        problem += y[i] == 1

    # (III)
    for i,j in edges: 
        problem += y[j] >= y[i] - x[i]
        #problem += y[i] >= y[j] - x[j]

    ### SOLVING
    #solver = PULP_CBC_CMD(msg=True, timeLimit=300) # Solution with time limit
    start_time= time.time()
    solver = HiGHS(timeLimit=timeSol, gapRel=mipGap, threads=4)

    problem.solve(solver)
    end_time = time.time()

    solving_time = end_time - start_time

    highlight_nodes = {}
    print("Objective Value (Minimized Capacity):", pulp.value(problem.objective))
    objective_Value = pulp.value(problem.objective)

    flooded = sum(1 - (y[i].varValue if y[i].varValue is not None else 0) for i in building_over)
    protected_building_over = flooded

    costs = objective_Value - 3000*sum((y[i].varValue if y[i].varValue is not None else 0) for i in building_over) #100 muss an lambda angepasst werden
    #costs = objective_Value
    for node in nodes:
        if x[node].varValue ==1:
            #print(f"x[{node}] = {x[node].varValue} | y[{node}] = {y[node].varValue}")
            highlight_nodes[node] = x[node].varValue
            #costs += removal_costs[node] 

    print("protected buildings:",protected_building_over)
    print(costs)
    #print(highlight_nodes)

    print("--------------------------------------")
    print("time for solving: ", solving_time)
    print("--------------------------------------")
    return highlight_nodes, objective_Value, costs, protected_building_over, solving_time


#------------------------------------------------------------------------------------------------------------------
### INPUT DATA 

# NFI Instanz 
#G, node_positions = load_graph_and_positions( "C:/Users/lenas/OneDrive/Masterarbeit/Graphen/StartingGraph_2.pkl")
G, node_positions = load_graph_and_positions( "C:/Users/lenas/OneDrive/Masterarbeit/Graphen/StartingGraph_diag.pkl")

# water rise 
w = 1.8

# Generate flooding
floodedGraph = simulation_flood(G, w)

#Arguments: build_NFI(floodedG, w, node_positions, damHEIGHT)
NFI, node_positions = build_NFI(floodedGraph,w, node_positions)
#NFI, node_positions = build_NFI(floodedGraph,w, node_positions,damHEIGHT=0.2)
#print(nx.is_directed(NFI))
# print(NFI.edges[(358, 593),(358, 594)])
# print(NFI.edges[(358, 594),(358, 593)])

# Budget 
R = 3 # how many flooded
#R = 162
# lambda for objective function 
l = 0 # mean capacity / mean removal costs
# 0.02 bei 1.5 Hochwasser = objective value of 0.02359 Budget= 100

# Solver settings 
#timeLimit = 1800
mipGap = 0   #40% -> should be fractional

#------------------------------------------------------------------------------------------------------------------
### Function Call 

highlight_nodes, objective_Value, costs, prot, status = solveModel(NFI, R, l=l, mipGap=mipGap)

highlight_nodes_list = list(highlight_nodes.keys())

start_solution = {
    "highlighted_nodes": highlight_nodes
}

print(costs, prot)
print(status)



#🛑CHANGE
# file_path = "C:/Users/lenas/OneDrive/Masterarbeit/Results_ILP/newPostD.pkl"
# with open(file_path, "wb") as f:
#     pickle.dump(start_solution, f)

# print(f"Startlösung gespeichert unter: {file_path}")

#------------------------------------------------------------------------------------------------------------------
### VISUALIZATION

#visualize_MIPSolution(NFI, node_positions, highlight_nodes_list)
visualize_MIPSolution_pixel(NFI, node_positions, highlight_nodes)















