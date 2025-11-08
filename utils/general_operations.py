###############################################################
### Contains Function which are needed regularly 
###  - load json file 
###  - save graph in a file 
###  - load graph from a given path  
###
################################################################

##########
# PACKAGES
##########

import json
import pickle

################
# load json file 
################

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

#############################
# SAVE THE GRAPH AS .pkl FILE  
#############################

def save_graph_and_positions(graph, positions, filename):
    with open(filename, 'wb') as file:
        pickle.dump({'graph': graph, 'positions': positions}, file)
    print(f"Graph and positions saved to {filename}")

##################
# LOAD A .pkl FILE  
##################

def load_graph_and_positions(filename):
    with open(filename, 'rb') as file:
        data = pickle.load(file)
    print(f"Graph and positions loaded from {filename}")
    return data['graph'], data['positions']