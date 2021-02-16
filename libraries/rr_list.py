from warnings import warn
import numpy as np
import os.path
from re import split
from utils import *

class rr_list():
    # Input (optionnal): a list of character strings corresponding to the system's nodes.
    # If no argument is given, the nodes list begins empty
    
    def __init__(self, nodes_list = []):
        self.rules = []
        self.constraints = []
        self.nodes = nodes_list
        self.nodes_init = []
        
    def show(self):
        print("Nodes:")
        print(self.nodes)
        print("Rules:")
        print(self.rules)
        print("Constraints:")
        print(self.constraints)
        return
        
    ######## functions allowing to modify the list of rules and constraints by hand
    
    def replace_rule(self, former_rule, new_rule, is_constraint = False):
        # Replace an existing rule (or constraint) from the system by another one
        if is_constraint == True:
            self.constraits.remove(former_rule)
            self.constraints.append(new_rule)
        else:
            self.rules.remove(former_rule)
            self.rules.append(new_rule)
            
    def replace_constraint(self, former_constraint, new_constraint):
        # Replace an existing constraint from the system by another one
            self.constraits.remove(former_constraint)
            self.constraints.append(new_constraint)

########### Useless? ################
#    def add_rule(self, new_rule, is_constraint = False):
#        if is_constraint == True:
#            self.constraits.append(new_rule)
#        else:
#            self.rules.append(new_rule)
#            
#    def add_constraint(self, constraint):
#        self.constraits.remove(constraint)
#        
#    def remove_rule(self, rule, is_constraint = False):
#        if is_constraint == True:
#            self.constraits.remove(rule)
#        else:
#            self.rules.remove(rule)
#            
#    def remove_constraint(self, constraint):
#            self.constraits.remove(constraint)


        
    ######## functions allowing to add "common" rules to a given rr set ########
    
    # These are our current definitions of predation, competition, and all our common rules
        
    def add_predation(self, predator, preys_list, secondary_preys=[], preferential = True, autotroph = False, strong_dependance = False, allow_appearance = False):
        # Writes the rules corresponding to the predation of a given species
        
        # predator (str): name of the predator
        # preys_list (list of str): list of the main prey's names
        # secondary_preys (list of str): list of the secondary prey's names
        # preferential (bool): if True, secondary preys are eaten only if the main ones are all absent
        # autotroph (bool): if True, no rule causes the predator to disappear in the absence of its preys
        # strong_dependance (bool): if True, adds a constraint that forces the predator to disappear if all its preys (main and secondary) are absent

        # allow_appearance (bool): if True, adds the rules leading to appearance of species (/!\ should probably not be used for the event-based vision, only the process-based one)

        # Check presence of species in the nodes list
        for node in preys_list+[predator]+secondary_preys:
            if not node in self.nodes:
               warn("node {0} not defined !".format(node))
        # Check type
        if type(preys_list) != list:
            raise ValueError("preys_list has to be a list !")
        
        # Rules are illustrated with predator P, main prey N, secondary prey n
        for prey in preys_list:
            self.rules.append(create_rule(predator,"+", prey, "-")) # P+ >> N-
            
            if allow_appearance == True:
                self.rules.append(create_rule(prey, "+", predator, "+")) # N+ >> P+
                self.rules.append(create_rule(predator, "-", prey, "+")) # P- >> N+
 
        if not autotroph == True:    
            if len(preys_list) == 0:
                self.rules.append(create_rule(predator, "+", predator, "-")) # P+ >> P- if no viable prey, like Euplotes Patella in the Weatherby experiments
                if strong_dependance == True:
                    self.constraints.append(create_rule(secondary_preys, "-", predator, "-")) # Constraint: n- >> P-
            else:
                if strong_dependance == True:
                    self.constraints.append(create_rule(preys_list + secondary_preys, "-", predator, "-")) # N-, n- >> P-
                    if len(secondary_preys) > 0: # (otherwise the previous rule is enough)
                        self.rules.append(create_rule(preys_list, "-", predator, "-")) # N- >> P-
                    # the predator can disappear in the absence of its main preys, and is forced to disappear in the absence of all preys
                else:
                    self.rules.append(create_rule(preys_list, "-", predator, "-")) # N- >> P-
        
        
        for s_prey in secondary_preys:
            if preferential == True:
                self.rules.append(create_rule([predator]+preys_list, ["+"]+["-"]*len(preys_list), s_prey, "-")) # N-, P+ >> P-
            else:
                self.rules.append(create_rule(predator, "+", s_prey, "-")) # P+ >> n-
            # P eats the secondary prey if the main preys (in preys_list) are all absent
          
            
    def add_competition(self, A, B, asymmetric = False):
        # Writes the rules corresponding to competition between A and B
        
        # A (str): name of the first competitor (dominant if asymmetric competition)
        # B (str): name of the second competitor
        # asymmetric (bool): if True, B is unable to exclude A
        
        # Note : compétition deux à deux pour le moment, pas sûr que ça soit utile de s'embêter à la faire par plus grands groupes?
        
        # Check types
        if not A in self.nodes:
            warn("node {0} not defined !".format(A))
        if not B in self.nodes:
            warn("node {0} not defined !".format(B))
            
        self.rules.append(create_rule(A, "+", B, "-")) # A+ >> B-
        if asymmetric == False:
            self.rules.append(create_rule(B, "+", A, "-")) # B+ >> A-
            
            
    def add_mutualism(self, A, B, asymmetric = False):
        # Writes the rules corresponding to mutualism
        
        # A, B (str): name of the mutualist species
        # asymmetric (bool): if True, only A depends on B
        
        # Check types
        if not A in self.nodes:
            warn("node {0} not defined !".format(A))
        if not B in self.nodes:
            warn("node {0} not defined !".format(B))
        
        self.rules.append(create_rule(B, "-", A, "-")) # B- >> A-
        if asymmetric == False:
            self.rules.append(create_rule(A, "-", B, "-")) # A- >> B-
            
        
    def add_appearance(self, A, absence_conditions = [], presence_conditions = []):
        # Writes the rules corresponding to appearance of A
        
        # A (str): name of the species that appears
        # absence_conditions (list of str): list of the names of the nodes that have to be absent in order to allow A to appear
        # presence_contitions (list of str): list of the names of the nodes that have to be absent in order to allow A to appear
        if len(absence_conditions) + len(presence_conditions) == 0:
            self.rules.append(create_rule(A, "-", A, "+"))
        else:
            self.rules.append(create_rule(absence_conditions + presence_conditions, ["-"]*len(absence_conditions) + ["+"]*len(presence_conditions), A, "+"))
            
        
    ########### Direct inclusion of community matrices to the rules
    
    def include_matrix(self, S, interaction_choice, **kwd):
        # Write the rules corresponding to the community matrix S
        
        # S (numpy matrix): adjacency matrix ; its size should be equal to the number of components in the system.
        # interaction_choice (str ; "predation" or "competition")
        
        #   For predation, S should be lower diagonal.
        #   S_ij = 1 if i is a "main" prey for j ; 0 < Sij < 1 if it is a "secondary" prey, Sij = O otherwise.
        
        #   For competition, S should have no diagonal elements.
        #   S_ij = 1 if j can outcompete i, O otherwise
        
        # The optionnal arguments of the add_predation method can be passed: preferential, autotroph, strong_dependance, allow_appearance.
        # If so, they will be applied to all predation links.
        
        
        # Check size of S
        if not len(self.nodes) == S.shape[0] == S.shape[1]:
            raise ValueError("The community matrix should have size N x N, with N the number of nodes in the network")

        if interaction_choice == "predation":
#                                   if isin(False, triu(S, k=+1) == 0):
#                                   warn("Community matrix is not lower diagonal. Its upper elements were set to 0, but this shouldn't happen.")
            # check that S is lower diagonal
            if np.isin(False, np.diag(S) == 0):
                warn("Diagonal elements in the matrix are not zero. They were set to zero, but there might be a problem somewhere.")
                S = S - np.diag(np.diag(S))  #sets diagonal elements to zero
            for i in range(len(self.nodes)):
                nodes_as_array = np.array(self.nodes)      # To allow manipulation with numpy
                predator = self.nodes[i]                # Predator name
                preys_list = list(nodes_as_array[S[:,i] == 1]) # 
                secondary_preys = list(nodes_as_array[ (S[:,i] < 1) & (S[:,i] > 0) ])
                if len(preys_list + secondary_preys) > 0:
                    self.add_predation(predator = predator, preys_list = preys_list, secondary_preys = secondary_preys, **kwd)
        
        elif interaction_choice == "competition":
            for i in range(len(self.nodes)):
                nodes_as_array = np.array(self.nodes)
                species = self.nodes[i]
                competitors_list = list(nodes_as_array[S[:,i] == 1])
                
                for competitor in competitors_list:
                    self.add_competition(species, competitor, asymmetric = True)
                    
        else:
            warn("Interaction '{0}' is unknown, no rule was added".format(interaction_choice))
            return

    ############ Writing the .rr file ###################
    
    def write_file(self, filename, folder = "", sure = "?"):
        # Export the list of nodes and rules into the corresponding .rr file, directly readable by ecoserv.
        
        # filename (str): name of the file to create (without the .rr extension)
        # folder (str, optionnal): path to create the file
        # sure (str, "y" or "n"): if "y", will automatically override existing files without asking.
        #                         if "n", will automatically abort operation if the file already exists.
        
        
        complete_filename = folder + filename + ".rr"
        
        # Checking whether the file already exists or not
        if os.path.isfile(complete_filename):
            while not sure in ["y", "Y", "n", "N"]:
                sure = input("the rr file '{0}' already exists. Are you sure that you want to override it? (y/n) \n".format(complete_filename))
            
            if sure in["n","N"]:
                raise ValueError("the rr file '{0}' already exists and you asked not to override it".format(complete_filename)) 
        
        # First test for nodes initialization
        if not len(self.nodes_init) == len(self.nodes):
            warn("initialization of the nodes is incorrect, as the number of nodes is not equal to the number of initial values. All nodes have been initialized to 1.")
            self.nodes_init = np.ones(len(self.nodes))
            
        with open(complete_filename, 'w') as f:
                
            # Write nodes list and initial states
            f.write("nodes:\n")
            for node, init in zip(self.nodes, self.nodes_init):
                if init in (1, "+", True): # node initially present
                    f.write(" "+ node +"+ :\n")
                elif init in (0, "-", False): # node initially absent
                    f.write(" "+node +"- :\n")
                else:
                    print("node {0} was not initialized properly and was set as initially inactive".format(node))
                    f.write(" "+node +"- :\n")
            f.write("\n")
            
            # Write rules and constraints:
            f.write("rules:\n")
            for rule in self.rules:
                f.write(rule +"\n")
            if len(self.constraints) > 0:
                f.write("\nconstraints:\n")
                for constraint in self.constraints:
                    f.write(constraint +"\n")




    ################### Write the .rr file allowing to compute the universe ###########
                
    def write_universe_file(self, filename, folder = "", sure = "?"):
        # Creates the .rr file allowing to compute the state universe, directly readable by ecoserv or ecco.
        
        # filename (str): name of the file to create (without the .rr extension ; the suffix "_universe" will automatically be added to the name.)
        # folder (str, optionnal): path to create the file
        # sure (str, "y" or "n"): if "y", will automatically override existing files without asking.
        #                         if "n", will automatically abort operation if the file already exists.
        
        
        
        
        complete_filename = folder + filename + "_universe.rr"
        
        # Checking whether the file already exists or not
        if os.path.isfile(complete_filename):
            while not sure in ["y", "Y", "n", "N"]:
                sure = input("the rr file '{0}' already exists. Are you sure that you want to override it? (y/n) \n".format(complete_filename))
            
            if sure in["n","N"]:
                raise ValueError("the rr file '{0}' already exists and you asked not to override it".format(complete_filename)) 
                
        with open(complete_filename, 'w') as f:
            
            # Write nodes list and initial states
            f.write("nodes:\n")
            for node in self.nodes:
                f.write(" "+ node +"- :\n")
            f.write(" i+ :\n")
            f.write("\n")
            
            # Write rules and constraints:
            f.write("rules:\n")
            for rule in self.rules:
                if "]" in rule:         # Tests whether rules have a name, in order to insert the "i-" condition after it
                    temp_string = split("\] ", rule)
                    f.write(temp_string[0]+"] i-, "+temp_string[1] +"\n")
                else:
                    f.write(" i-," + rule +"\n")
            for node in self.nodes:
                f.write(" i+ >> " + node +"+\n")
            f.write(" i+ >> i-\n")
            if len(self.constraints) > 0:
                f.write("\nconstraints:\n")
                for constraint in self.constraints:
                    f.write(" i-," + constraint +"\n")
                    

                    
            