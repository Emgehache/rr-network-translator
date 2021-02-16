import networkx as nx
import pandas as pd
import numpy as np
from rr_list import *
from utils import *

class rr_network(nx.DiGraph):
    # Overlayer of the nx.DiGraph class from the networkx library, intended to allow translation towards the rr_list class
    # No initialization, the initial network will be empty
    
    ##########################################
    # Addition of ecologically meaning links #
    ##########################################
    
    def add_predation(self, predator, preys_list, secondary_preys=[]):
        # Adds predation links to the system
        # predator (str): name of the predator [i.e. its node's name]
        # preys_list (list of str): list of the main prey's names
        # secondary_preys (list of str): list of the secondary prey's names
        self.add_edges_from([(predator, prey) for prey in preys_list], kind = "predation")
        self.add_edges_from([(predator, prey) for prey in secondary_preys], kind = "secondary_predation")
        
    def add_competition(self, A, B, asymmetric = False):
        # Adds a competition link between species A and B
        # A, B (str): names of the competitors
        # asymmetric (bool): if True, only A can exclude B
        self.add_edge(A, B, kind = "competition")
        if asymmetric == False:
            self.add_edge(B, A, kind = "competition")
        
    def add_mutualism(self, A, B):
        # Adds a mutualism link between species A and B
        # A, B (str): names of the species
        self.add_edges_from([(A, B), (B, A)], kind = "mutualism")
    
    ###############################
    # Initialization of the nodes #
    ###############################
    
    # Optionnal (but recommended) if the rr_list is meant to be manipulated later
    # Mandatory if the .rr file is meant to be created directly

    def initialize_nodes(self, initially_present = []):
        # Sets the initial state of the system.
        # initially_present(list of str, optionnal): list of the names of the nodes initially present (all other are set initially absent)
        self.nodes_init = pd.DataFrame({"nodes" : list(self.nodes), "init" : list(np.zeros(len(self.nodes)))})
        for node in initially_present:
            self.nodes_init.loc[self.nodes_init["nodes"] == node, "init"] = 1
    
    def set_node_init(self, node, init):
        # Sets or modifies the initial state of a given node
        # node (str) : name of the node whose initial state has to be set
        # init (0 or 1): initial state (0 if absent, 1 if present)
        if hasattr(self, "nodes_init") == False:
            raise ValueError("please initialize the nodes using the initialize_nodes method")
        self.nodes_init.loc[self.nodes_init["nodes"] == node, "init"] = init

    ###############################
    # Translation into an rr_list #
    ###############################
    
    def create_rr(self, allow_appearance = True, strong_dependance = True, **kwd):
        if hasattr(self, "nodes_init") == False:
            sure = input("the nodes have not been initialized. Do you want to initialize them all to 1 ? (y/n)")
            
            if sure in["y","Y"]:
                self.initialize_nodes(initially_present = list(self.nodes))
            else:
                raise ValueError("aborted conversion to rr, please initialize the nodes properly") 

        rr_out = rr_list(nodes_list = list(self.nodes))
        rr_out.nodes_init = list(self.nodes_init["init"])
        
        edges = nx.to_pandas_edgelist(self)
        
        for node in self.nodes:
            
            ######## predation ########

            preys = list(edges["target"][(edges['source'] == node) & (edges["kind"] == "predation")])
            secondary_preys = list(edges["target"][(edges['source'] == node) & (edges["kind"] == "secondary_predation")])
            predators = list(edges["source"][(edges['target'] == node) & (edges["kind"] == "predation")])
            competitors = list(edges["source"][(edges['target'] == node) & (edges["kind"] == "competition")])
            mutuals = list(edges["source"][(edges['target'] == node) & (edges["kind"] == "mutualism")])
            
            if len(preys + secondary_preys) > 0:
                if "feature" in self.nodes[node]:
                # exceptionif a species is autotroph : it will not disappear in the absence of its preys
                    if self.nodes[node]["feature"] == "autotroph":
                        rr_out.add_predation(node, preys_list = preys, secondary_preys = secondary_preys, autotroph = True, strong_dependance = strong_dependance)
                else :
                    rr_out.add_predation(node, preys_list = preys, secondary_preys = secondary_preys, strong_dependance = strong_dependance)

            ######## competition ######

            for competitor in competitors:
                rr_out.rules.append(create_rule(node, "+", competitor, "-"))
                
            ######## mutualism ########
            
            if len(mutuals) > 0:
                rr_out.rules.append(create_rule(mutuals, "-", node, "-"))

            ###########################
            ######## appearance #######
            ###########################
            if allow_appearance == True:
                
                if len(preys + secondary_preys) == 0:
                # if the species has no preys, it has to be an autotroph
                    rr_out.add_appearance(node, absence_conditions = predators + competitors)
                else:
                    if "feature" in self.nodes[node]:
                        if self.nodes[node]["feature"] == "autotroph":
                            rr_out.add_appearance(node, absence_conditions = predators + competitors)
                    else:
                        # one main prey has to be present, and no competitor or predator
                        for prey in preys:
                            rr_out.add_appearance(node, absence_conditions = predators + competitors, presence_conditions = [prey])
                    
                
        return rr_out
    
    def write_rr_file(self, filename, folder = "", sure = "?", universe = False, **kwd):
        temp_rr = self.create_rr(**kwd)
        if universe == True:
            temp_rr.write_universe_file(filename = filename, folder = folder, sure = sure)
        else :
            temp_rr.write_file(filename = filename, folder = folder, sure = sure)
            
    def network_from_state(self, present):
        temp_net = self
        for off_node in set(self.nodes) - set(present):
            temp_net.remove_node(off_node)
        return temp_net
                
        
# class rr_network2(nx.MultiDiGraph):
#     def add_predation(self, predator, preys_list, secondary_preys=[]):
#         self.add_edges_from([(predator, prey) for prey in preys_list], key = "predation")
#         self.add_edges_from([(predator, prey) for prey in secondary_preys], key = "secondary_predation")
        
#     def add_competition(self, A, B):
#         self.add_edges_from([(A, B), (B, A)], key = "competition")