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
    
    def create_rr(self, allow_appearance = True, strong_dependance = True, appearance_options = [], **kwd):
        # Creates a rr_list object corresponding to the translation of the network

        # allow_appearance (bool): if True, species will be allowed to reappear.
        # strong_dependance (bool): if True, predators immediately disappear (constraint) when they have no prey at all (no main prey nor secondary)
        # appearance_options (list of str): options for the allow_appearance = True case): 
        #       if empty (default), species can appear as long as they have something to eat (main or secondary)
        #       if "only_main_prey" is in the list, species can appear only if a main prey is present
        #       if "no_predator" is in the list, species can only appear if no main predator is present
        #       if "no_competitor" is in the list, species cannot appear if a competitor is present
        #       if "all_mutualists" is in the list, species can appear if all its mutuals are present
        
        # Check of initialisation
        if hasattr(self, "nodes_init") == False:
            sure = input("the nodes have not been initialized. Do you want to initialize them all to 1 ? (y/n)")
            
            if sure in["y","Y"]:
                self.initialize_nodes(initially_present = list(self.nodes))
#            else:
#                raise ValueError("aborted conversion to rr, please initialize the nodes properly") 

        # Creation of the rr_list object
        rr_out = rr_list(nodes_list = list(self.nodes))
        
        if hasattr(self, "nodes_init") == True:
            rr_out.nodes_init = list(self.nodes_init["init"])
        
        edges = nx.to_pandas_edgelist(self)
        
        for node in self.nodes:
            
            # Identification of species with which the node interacts

            preys = list(edges["target"][(edges['source'] == node) & (edges["kind"] == "predation")])
            secondary_preys = list(edges["target"][(edges['source'] == node) & (edges["kind"] == "secondary_predation")])
            predators = list(edges["source"][(edges['target'] == node) & (edges["kind"] == "predation")])
            competitors = list(edges["source"][(edges['target'] == node) & (edges["kind"] == "competition")])
            mutuals = list(edges["source"][(edges['target'] == node) & (edges["kind"] == "mutualism")])
            
            # Rules corresponding to predation links #
            
            if len(preys + secondary_preys) > 0:
                if "feature" in self.nodes[node]:
                # exceptionif a species is autotroph : it will not disappear in the absence of its preys
                    if self.nodes[node]["feature"] == "autotroph":
                        rr_out.add_predation(node, preys_list = preys, secondary_preys = secondary_preys, autotroph = True, strong_dependance = strong_dependance)
                else :
                    rr_out.add_predation(node, preys_list = preys, secondary_preys = secondary_preys, strong_dependance = strong_dependance)

            # Rules corresponding to competition links #

            for competitor in competitors:
                rr_out.add_competition(node, competitor, asymmetric = True) # The links in the network are asymmetric ; if competition is symmetric the link will appear once for each direction and the translation has therefore to be asymmetric
                #rr_out.rules.append(create_rule(node, "+", competitor, "-"))
                
            # Rules corresponding to mutualism links #
            
            for mutual in mutuals:
                rr_out.add_mutualism(node, mutual, asymmetric = True)
                #rr_out.rules.append(create_rule(mutuals, "-", node, "-"))

            ## Rules corresponding to the node's appearance #
            
            if allow_appearance == True:
                # choice of other nodes that have to be absent from the system to allow the node to reappear:
                absence_conditions = []
                if "no_predator" in appearance_options:
                    absence_conditions += predators
                if "no_competitor" in appearance_options:
                    absence_conditions += competitors
                
                # choice of other nodes that have to be present in the system to allow the node to reappear:
                presence_conditions = []
                if "all_mutualists" in appearance_options:
                    presence_conditions += mutuals
                    
                if len(preys + secondary_preys) == 0:
                # if the species has no preys, it has to be an autotroph
                    rr_out.add_appearance(node, presence_conditions = presence_conditions, absence_conditions = absence_conditions)
                else:
                    # if autotroph, only absence conditions
                    if "feature" in self.nodes[node]:
                        if self.nodes[node]["feature"] == "autotroph":
                            rr_out.add_appearance(node, presence_conditions = presence_conditions, absence_conditions = absence_conditions)
                    # if not, duplication of the the rule for each prey
                    else:
                        for prey in preys:
                            rr_out.add_appearance(node, absence_conditions = absence_conditions, presence_conditions = presence_conditions+[prey])
                        if not "only_main_prey" in appearance_options:
                            for prey in secondary_preys:
                                rr_out.add_appearance(node, absence_conditions = absence_conditions, presence_conditions = presence_conditions+[prey])
                    
                
        return rr_out
    
    
    def write_rr_file(self, filename, folder = "", sure = "?", universe = False, **kwd):
        # Directly writes the .rr file translated from the network (the rr_list object is created but not stored)

        # filename (str): name of the file to create (without the .rr extension)
        # folder (str, optionnal): path to create the file
        # sure (str, "y" or "n"): if "y", will automatically override existing files without asking.
        #                         if "n", will automatically abort operation if the file already exists.
        # universe (bool): if True, writes the .rr file allowing to compute the state universe

        # Check of nodes initialization
        if hasattr(self, "nodes_init") == False:
            sure = input("the nodes have not been initialized. Do you want to initialize them all to 1 ? (y/n)")
            
            if sure in["y","Y"]:
                self.initialize_nodes(initially_present = list(self.nodes))
            else:
                raise ValueError("aborted conversion to rr, please initialize the nodes properly") 
        
        # Creation of a temporary rr_list object
        temp_rr = self.create_rr(**kwd)
        
        # Exportation of the .rr file
        if universe == True:
            temp_rr.write_universe_file(filename = filename, folder = folder, sure = sure)
        else :
            temp_rr.write_file(filename = filename, folder = folder, sure = sure)
    
    #########
    # Other #
    #########
    
    def network_from_state(self, present):
        # Allows to obtain the ecological network corresponding to a given state (i.e. removing all absent nodes), for example to compute its structure.
        
        # present (list of str): list of the names of active nodes.
        temp_net = self
        for off_node in set(self.nodes) - set(present):
            temp_net.remove_node(off_node)
        return temp_net