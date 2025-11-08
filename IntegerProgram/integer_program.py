import pulp
import numpy as np
import pyomo.environ as pyo

class IntegerProgram:
    def __init__(self, grid, building_weight=1, water_height=0):
        self.grid = grid
        self.building_weight = building_weight
        self.water_height = water_height

    def formulate_problem(self, number_protected_buildings):
        def eight_neighbors(grid, nid):
            nrows, ncols = grid.shape
            row, col = np.unravel_index(nid, (nrows, ncols))
            neighbors = []
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    r, c = row + dr, col + dc
                    if 0 <= r < nrows and 0 <= c < ncols:
                        neighbors.append(r * ncols + c)
            return neighbors
        
        grid = self.grid
        elev = grid.at_node["topographic__elevation"]
        border = grid.at_node["border_of_river"]
        bldg_ids = grid.at_node["building_ids"]
        relevant = grid.at_node["relevant"]

        #get ids of relevant nodes
        relevant_node_ids = [nid for nid in range(grid.number_of_nodes) if relevant[nid] == 1]
        river_node_ids = [nid for nid in range(grid.number_of_nodes) if border[nid] == 1]

        removal_costs = {}
        for nid in relevant_node_ids:
            removal_costs[nid] = self.water_height - elev[nid] if self.water_height > elev[nid] else 0

        # generate new ids for building ids as unique values in bldg ids except 0
        max_nid = max(relevant_node_ids)

        new_building_id = max_nid + 1

        building_ids = np.unique(bldg_ids)
        building_ids = building_ids[building_ids != 0]  # remove 0

        building_node_ids = []
        building_node_ids_map = {}
        building_node_ids_map_reverse = {}

        for bid in building_ids:
            building_node_ids_map[bid] = new_building_id
            building_node_ids.append(new_building_id)
            building_node_ids_map_reverse[new_building_id] = bid
            new_building_id += 1

        all_node_ids = relevant_node_ids + building_node_ids

        print("number of node ids:", len(all_node_ids))
        num_node_ids = len(all_node_ids)

        model = pyo.ConcreteModel("Flood_Protection_Problem")

        # --- Sets ---
        model.ALL = pyo.Set(initialize=all_node_ids)
        model.REL = pyo.Set(initialize=relevant_node_ids)
        model.RIV = pyo.Set(initialize=river_node_ids)
        model.BLDG = pyo.Set(initialize=building_ids)

        # --- Variables ---
        model.y = pyo.Var(model.ALL, domain=pyo.Binary)
        model.x = pyo.Var(model.REL, domain=pyo.Binary)

        # --- Objective ---
        def obj_rule(m):
            return sum(removal_costs[i] * m.x[i] for i in m.REL)
        model.Obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

        # --- Constraints ---
        # Budget / protection constraint
        def budget_rule(m):
            return sum(m.y[i] for i in building_node_ids) == number_protected_buildings
        model.BudgetConstraint = pyo.Constraint(rule=budget_rule)

        # River constraints
        def river_rule_y(m, i):
            return m.y[i] == 1
        model.RiverY = pyo.Constraint(model.RIV, rule=river_rule_y)

        def river_rule_x(m, i):
            return m.x[i] == 0
        model.RiverX = pyo.Constraint(model.RIV, rule=river_rule_x)

        # Neighbor (edge) constraints
        # Precompute edges as a list of (nid, neighbor)
        print("Precomputing edges...")
        relevant_node_ids_set = set(relevant_node_ids)

        edges = [
            (nid, neighbor)
            for nid in relevant_node_ids
            for neighbor in eight_neighbors(grid, nid)
            if neighbor in relevant_node_ids_set
        ]
        print("Number of edges:", len(edges))

        model.EDGES = pyo.Set(dimen=2, initialize=edges)

        def edge_rule(m, nid, neighbor):
            return m.y[neighbor] >= m.y[nid] - m.x[nid]
        model.EdgeConstraint = pyo.Constraint(model.EDGES, rule=edge_rule)

        # Building constraints
        bldg_pairs = [
            (building_node_ids_map[bid], cell_nid)
            for bid in building_ids
            for cell_nid in relevant_node_ids
            if bldg_ids[cell_nid] == bid
        ]
        model.BLDGPAIRS = pyo.Set(dimen=2, initialize=bldg_pairs)

        def bldg_rule(m, building_nid, cell_nid):
            return m.y[building_nid] >= m.y[cell_nid]
        model.BuildingConstraint = pyo.Constraint(model.BLDGPAIRS, rule=bldg_rule)

        solver = pyo.SolverFactory("highs")  # or "cbc", "glpk", "gurobi", etc.
        results = solver.solve(model, tee=True)
        print("Objective value:", pyo.value(model.Obj))