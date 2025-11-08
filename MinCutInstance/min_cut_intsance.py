from ortools.graph.python import max_flow
import numpy as np
import matplotlib.pyplot as plt

class MinCutInstance:
    def __init__(self, grid, building_weight=1, scaling_factor=1e6):
        self.grid = grid
        self.node_positions = {}
        self.categories = {}
        self.building_weight = building_weight
        self.arcs = []  # (u, v, capacity)
        self.node_map = {}  # internal mapping for grid nodes
        self.scaling_factor = scaling_factor  # to convert float capacities to int
        self.infinity = int(int(1e9)*self.scaling_factor)

    def build_graph(self, water_height):
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
        """
        Build a directed graph according to the problem rules:
        1) Building and river border cells -> single node
        2) Normal relevant cells -> in- and out-nodes
        3) Arcs between in/out and neighbors
        4) Source connected to all river border nodes
        5) River border nodes connected to adjacent normal in-nodes
        6) Building nodes connected to their cell nodes
        7) Sink connected from building nodes
        """
        grid = self.grid
        elev = grid.at_node["topographic__elevation"]
        border = grid.at_node["border_of_river"]
        bldg_ids = grid.at_node["building_ids"]
        relevant = grid.at_node["relevant"]

        n_nodes = grid.number_of_nodes
        xy = (grid.node_x, grid.node_y)

        self.node_positions.clear()
        self.categories.clear()
        self.arcs.clear()
        self.node_map.clear()

        node_id_counter = 0
        building_nodes = {}  # building_id -> node_id

        # --- Create grid cell nodes ---
        for nid in range(n_nodes):
            if relevant[nid] == 0:
                continue

            x, y = xy[0][nid], xy[1][nid]

            if border[nid] == 1 or bldg_ids[nid] != 0:
                # single node
                self.node_positions[node_id_counter] = (x, y)
                cat = "river" if border[nid] == 1 else "building"
                self.categories[node_id_counter] = cat
                self.node_map[(nid, "single")] = node_id_counter
                node_id_counter += 1
            else:
                # normal node: in + out
                in_id, out_id = node_id_counter, node_id_counter + 1
                node_id_counter += 2

                self.node_positions[in_id] = (x, y)
                self.node_positions[out_id] = (x, y)
                self.categories[in_id] = "normal_in"
                self.categories[out_id] = "normal_out"

                self.node_map[(nid, "in")] = in_id
                self.node_map[(nid, "out")] = out_id

                cap = max(0, water_height - elev[nid])
                #round cap to two decimals
                cap = round(cap, 2)
                cap = int(cap * self.scaling_factor)
                self.arcs.append((in_id, out_id, cap))

        # --- Source and sink ---
        source = node_id_counter
        sink = node_id_counter + 1
        node_id_counter += 2
        self.categories[source] = "source"
        self.categories[sink] = "sink"
        self.node_positions[source] = (-1, -1)
        self.node_positions[sink] = (-2, -2)

        # --- River border -> source edges ---
        for (nid, role), node_id in self.node_map.items():
            if role == "single" and border[nid] == 1:
                self.arcs.append((source, node_id, self.infinity))

        # --- Building nodes (unique per building id) ---
        for b_id in np.unique(bldg_ids[bldg_ids > 0]):
            b_node = node_id_counter
            node_id_counter += 1
            building_nodes[b_id] = b_node
            self.node_positions[b_node] = (0, -b_id * 2)
            self.categories[b_node] = "building_sink"
            # connect building node -> sink
            self.arcs.append((b_node, sink, int(self.building_weight * self.scaling_factor)))

        # --- Connect building cells to building node ---
        for nid in range(n_nodes):
            if relevant[nid] == 0 or bldg_ids[nid] == 0:
                continue
            bid = bldg_ids[nid]
            cell_node = self.node_map.get((nid, "single"))
            if cell_node is not None:
                self.arcs.append((cell_node, building_nodes[bid], self.infinity))

        # --- Neighbor connections ---
        for nid in range(n_nodes):
            if relevant[nid] == 0:
                continue

            if bldg_ids[nid] != 0:
                continue  # no building cell neighbors

            neighbors = eight_neighbors(self.grid, nid)
            for nb in neighbors:
                if nb < 0 or relevant[nb] == 0:
                    continue

                if border[nid] == 1 and border[nb] == 1:
                    continue  # no river->river edges

                # source node
                if (nid, "out") in self.node_map:
                    src = self.node_map[(nid, "out")]
                elif (nid, "single") in self.node_map:
                    src = self.node_map[(nid, "single")]
                else:
                    continue

                # destination node
                if (nb, "in") in self.node_map:
                    dst = self.node_map[(nb, "in")]
                elif (nb, "single") in self.node_map:
                    dst = self.node_map[(nb, "single")]
                else:
                    continue

                self.arcs.append((src, dst, self.infinity))

        # --- River borders -> adjacent normal in-nodes ---
        for nid in range(n_nodes):
            if border[nid] != 1 or relevant[nid] == 0:
                continue

            river_node = self.node_map.get((nid, "single"))
            for nb in eight_neighbors(self.grid, nid):
                if relevant[nb] == 1 and (nb, "in") in self.node_map:
                    dst = self.node_map[(nb, "in")]
                    self.arcs.append((river_node, dst, self.infinity))

        return source, sink

    def visualize(self, max_edges_to_draw=5000, show_elevation=False, out_offset=0.2):
        """
        Fast visualization of the flow network with arrows and offset for out-nodes.
        
        Args:
            max_edges_to_draw: maximum number of edges to draw (for performance)
            show_elevation: overlay topography from the grid
            out_offset: fraction of grid spacing to offset out-nodes for visibility
        """
        plt.figure(figsize=(12, 10))

        # --- Elevation background ---
        if show_elevation and "topographic__elevation" in self.grid.at_node:
            elev = self.grid.at_node["topographic__elevation"].reshape(self.grid.shape)
            plt.imshow(
                elev,
                origin="lower",
                extent=[0, self.grid.shape[1], 0, self.grid.shape[0]],
                cmap="terrain",
                alpha=0.4,
            )

        pos = {}
        dx = dy = out_offset

        # --- Apply offset to out-nodes ---
        for n, (x, y) in self.node_positions.items():
            if self.categories.get(n) == "normal_out":
                pos[n] = (x + dx, y + dy)
            else:
                pos[n] = (x, y)

        color_map = {
            "normal_in": "#a6cee3",
            "normal_out": "#1f78b4",
            "river": "#33a02c",
            "building": "#e31a1c",
            "building_sink": "#fb9a99",
            "source": "#ff7f00",
            "sink": "#6a3d9a",
        }

        # --- Draw nodes ---
        for cat in sorted(set(self.categories.values())):
            nodes = [n for n, c in self.categories.items() if c == cat]
            if not nodes:
                continue
            xy = np.array([pos[n] for n in nodes])
            plt.scatter(
                xy[:, 0],
                xy[:, 1],
                s=10,
                color=color_map.get(cat, "#bdbdbd"),
                label=cat,
                alpha=0.9,
            )

        # --- Draw directed edges ---
        arrow_alpha = 0.2
        for (u, v, cap) in self.arcs[:max_edges_to_draw]:
            if u in pos and v in pos:
                x1, y1 = pos[u]
                x2, y2 = pos[v]
                # draw light line
                plt.plot([x1, x2], [y1, y2], color="k", alpha=0.05, linewidth=0.4)
                # draw small arrow for direction
                plt.arrow(
                    x1, y1,
                    (x2 - x1) * 0.8,
                    (y2 - y1) * 0.8,
                    head_width=0.1,
                    head_length=0.15,
                    fc="k",
                    ec="k",
                    alpha=arrow_alpha,
                    length_includes_head=True,
                )

        plt.legend(markerscale=3, frameon=False)
        plt.axis("off")
        plt.title("Flow Network (with directed arcs & out-node offset)")
        plt.tight_layout()
        plt.show()

    def run_min_cut(self, source, sink):
        """
        Run the min-cut algorithm using the new OR-Tools API.
        """
        flow, smf = self.run_max_flow(source, sink)
        return self.get_min_cut(smf)

    def run_max_flow(self, source, sink):
        """
        Run the max-flow algorithm using the new OR-Tools API.
        """
        smf = max_flow.SimpleMaxFlow()
        print(smf)
        for u, v, cap in self.arcs:
            smf.add_arc_with_capacity(u, v, cap)

        status = smf.solve(source, sink)
        if status == max_flow.SimpleMaxFlow.OPTIMAL:
            return smf.optimal_flow(), smf
        else:
            raise ValueError("Max flow problem has no optimal solution.")

    def get_min_cut(self, smf):
        """
        Retrieve the minimum cut from the solved max-flow instance.
        """
        source_side = smf.get_source_side_min_cut()
        sink_side = smf.get_sink_side_min_cut()
        return source_side, sink_side
    
    def get_cut_cells(self, smf):
        """
        Return the grid node indices of normal cells where the (in->out) arc lies in the min cut.
        """
        source_side = set(smf.get_source_side_min_cut())
        sink_side = set(smf.get_sink_side_min_cut())

        cut_cells = []
        for (nid, role), node_id in self.node_map.items():
            if role != "in":
                continue

            out_id = self.node_map.get((nid, "out"))
            if out_id is None:
                continue

            # If in-node is reachable from source, but out-node is not, this arc crosses the cut
            if node_id in source_side and out_id in sink_side:
                cut_cells.append(nid)

        return cut_cells
    
    def get_buildings_in_cut(self, smf):
        """
        Returns a list of building IDs where the building→sink arc is part of the min cut,
        i.e., the building node is on the source side and the sink is on the sink side.

        Args:
            smf (max_flow.SimpleMaxFlow): Solved max-flow instance.

        Returns:
            List[int]: Building IDs in the cut (disconnected or 'flooded' buildings).
        """
        source_side = set(smf.get_source_side_min_cut())
        flooded_buildings = []

        for node_id, cat in self.categories.items():
            if cat == "building_sink" and node_id in source_side:
                # building_sink node position encoding: y = -2 * b_id  →  b_id = int(abs(y) / 2)
                x, y = self.node_positions[node_id]
                b_id = int(abs(y) / 2)
                flooded_buildings.append(b_id)

        return flooded_buildings

