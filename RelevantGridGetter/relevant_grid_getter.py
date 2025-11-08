import numpy as np

class RelevantGridGetter:
    def __init__(self, grid):
        self.grid = grid

    # Define helper function to get neighbors for a node
    def get_neighbors(self, node_id):
        rows, cols = self.grid.shape
        row, col = divmod(node_id, cols)  # Convert flat index to (row, col)
        neighbors = []
        if row > 0:  # Up
            neighbors.append(node_id - cols)
        if row < rows - 1:  # Down
            neighbors.append(node_id + cols)
        if col > 0:  # Left
            neighbors.append(node_id - 1)
        if col < cols - 1:  # Right
            neighbors.append(node_id + 1)
        return neighbors
    
    def get_border_of_river(self):
        self.grid.add_zeros("border_of_river", at="node")
        for node_id in range(self.grid.number_of_nodes):
            if self.grid.at_node["river"][node_id] > 0:
                neighbors = self.get_neighbors(node_id)
                for neighbor in neighbors:
                    if self.grid.at_node["river"][neighbor] == 0:
                        self.grid.at_node["border_of_river"][node_id] = 1
        return self.grid
    
    def get_relevant_nodes(self, river_height=380, elevation_threshold=1):
        self.grid.add_zeros("relevant", at="node")

        # Set all river border nodes to relevant
        self.grid.at_node["relevant"] = self.grid.at_node["border_of_river"].copy()

        border_nodes = np.where(self.grid.at_node["border_of_river"] == 1)[0]
        queue = set(border_nodes)

        critical_height = river_height + elevation_threshold

        while len(queue) > 0:
            node = queue.pop()
            #check all neighbors of the node
            neighbors = self.get_neighbors(node)
            geodesic_elevation = self.grid.at_node["topographic__elevation"][node]
            if geodesic_elevation <= critical_height:
                value = 1

                if self.grid.at_node["river"][node] - self.grid.at_node["border_of_river"][node] > 0:
                    value = 0
                
                if value == 1 and self.grid.at_node["building_ids"][node] > 0:
                    value = 0
                    for neighbor in neighbors:
                        if self.grid.at_node["building_ids"][neighbor] == 0:
                            value = 1
                            break
                
                self.grid.at_node["relevant"][node] = value
                if value == 1:
                    for neighbor in neighbors:
                        if self.grid.at_node["relevant"][neighbor] == 0:
                            queue.add(neighbor)
        return self.grid