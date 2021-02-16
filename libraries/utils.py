########### Function to automatically write a rule #############
def create_rule(A, sign_A, B, sign_B, tag="", comment=""):
#     A (string) : name of the component to be added as input of the rule.
#     B (string) : -------------------------------------output------------
#     sign_A ("+" or "-"): state of A allowing the rule to be fired (has to be "+" or "-")
#     sign_B ("+" or "-"): state of B set by the rule (has to be "+" or "-")
#     tag (string, optional): tag for the rule
#     comment (string, optionnal): comment to be added after the rule
#     A, B, sign_A and sign_B may also be lists or tuples containing the names and signs
#       of the components in order to write non-dyadic rules:
#       - If A is a list and sign_A is "+" or "-", the sign will be replicated for each element in A. 
#       - If A and sign_A are both lists, the sign will be chosen in sign_A for each element of A
#       (in which case, be careful as both lists need to have equal lengths!)
    
    # Verification of arguments
    if type(A) == list or type(A) == tuple:
        if type(sign_A) ==  str:
            sign_A = [sign_A]*len(A)
        elif len(A) != len(sign_A):
            raise ValueError("The number of species and signs for A does not match")
    if type(B) == list or type(B) == tuple:
        if type(sign_B) ==  str:
            sign_B = [sign_B]*len(B)
        elif len(B) != len(sign_B):
            raise ValueError("The number of species and signs for B does not match")
        
    # Format rule tag if needed
    if len(tag) != 0:
        tag_str = "[{0}] ".format(tag)
    else:
        tag_str = " "
        
    lhs = ""
    rhs = ""
    # Quick output if only one input and one output
    if type(A) == str:
        lhs += "{A}{s1}".format(A=A, s1=sign_A)
    else:
        for elm, sign in zip(A[:-1], sign_A[:-1]):
            lhs += "{A}{s}, ".format(A = elm, s = sign)
        lhs += "{A}{s}".format(A = A[-1], s = sign_A[-1])
        
    if type(B) == str:
        rhs += "{B}{s2}".format(B=B, s2=sign_B)
    else:
        for elm, sign in zip(B[:-1], sign_B[:-1]):
            rhs += "{B}{s}, ".format(B = elm, s = sign)
        rhs += "{B}{s}".format(B = B[-1], s = sign_B[-1])
        
    out_str = tag_str + lhs + " >> " + rhs
    
    #Addition of comment if necessary
    if len(comment) != 0:
        out_str += "\t\t # {0}".format(comment)
    
    return out_str


########## Quick, convenient functions based on create_rule ############
def apbp(A, B, tag="", comment=""):
    return create_rule(A, "+", B, "+", tag, comment)
def apbm(A, B, tag="", comment=""):
    return create_rule(A, "+", B, "-", tag, comment)
def ambp(A, B, tag="", comment=""):
    return create_rule(A, "-", B, "+", tag, comment)
def ambm(A, B, tag="", comment=""):
    return create_rule(A, "-", B, "-", tag, comment)