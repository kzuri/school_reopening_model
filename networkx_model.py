# -*- coding: utf-8 -*-
"""Networkx model.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Voss17Kf50Ls4Qu8pfpq2qpKB8vbgqX8

Installing missing libraries
"""

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# !pip install EoN
# !pip install pyvis

"""Defining libraries to be used"""

import networkx as nx
import EoN
import matplotlib.pyplot as plt
import pandas as pd
import random as random
from itertools import combinations
import copy

"""# Data pre-processing"""

ptable = pd.read_csv(
    "https://raw.githubusercontent.com/kzuri/school_reopening_model/main/UntilContactMatrix.csv"
)
Contact_school = pd.read_excel(
    "https://github.com/kzuri/school_reopening_model/blob/main/ContactMatricesPremetAl.xlsx?raw=true",
    sheet_name="School Contacts",engine='openpyxl'
)
Contact_res = pd.read_excel(
    "https://github.com/kzuri/school_reopening_model/blob/main/ContactMatricesPremetAl.xlsx?raw=true",
    sheet_name="Residential Contacts",engine='openpyxl'
)  # import contact matrix

ptable = ptable[ptable["ContactMatrix"] == 1]
pdict = ptable.T.to_dict()

# Underlying contact network- will make edges on random with 6 different people
# depend on their age and average number of contacts they have from PremetAl Matrix


def getUserLists(UserType):
    UserList = ptable[ptable["categ"] == UserType].index.to_list()
    return UserList


# Each student interacts with (5-10) other students, Student <-> non teaching (3-4)
# Teacher to Teacher (3) , Student <-> Teacher = 3-4 students for every teacher, Non-Taching <-> Non Teaching = (6),
# Teaching <-> Non Teaching = For every teacher 3-4 Non Teaching.

stud_list = getUserLists("Students")
teach_list = getUserLists("Teaching")
non_teach_list = getUserLists("Non teaching")
stud_age = list(set(ptable[ptable["categ"] == "Students"]["Age"]))

Student_num = len(stud_list)
Teacher_num = len(teach_list)
Non_teach_num = len(non_teach_list)

"""# Conditions for edge formation"""


def create_edges(list1, list2, multiplier):  ## for every member in list1 there will be "multiplier" number of edges in list 2
    edges = []

    total_interactions = multiplier * len(list1)
    while total_interactions > 0:
        node1 = random.choice(list1)
        node2 = random.choice(list2)
        if node1 != node2:
            edges.append((node1, node2))
            total_interactions = total_interactions - 1

    return edges


def divide_age_grp(pdict, stud_age, stud_list):
    age_grp = {}

    for i in stud_age:
        age_grp[i] = []

    for i in stud_list:
        age_grp[pdict[i]["Age"]].append(i)

    return age_grp


def get_index_combination(combination, source_list):
    # combination_list = list(combination)
    a, b = zip(*combination)
    a = list(a)
    sl = set(a)
    return [a.index(i) for i in sl]


def intraclass_generate(ncluster, prob_interaction=0):
    connection_grp = {}
    connection = []
    age_grp = divide_age_grp(pdict, stud_age, stud_list)

    for k in age_grp.keys():
        combination = combinations(age_grp[k], 2)
        combination1 = copy.copy(combination)

        idx_list = get_index_combination(combination, age_grp[k])
        combination_list = list(combination1)

        for i, idx in enumerate(idx_list[:-1]):
            if idx_list[i + 1] - idx_list[i] < ncluster + 1:
                connection += combination_list[idx_list[i] : idx_list[i + 1]]
            else:
                for j in random.sample(
                    combination_list[idx_list[i] : idx_list[i + 1]],
                    random.randint(ncluster - 1, ncluster + 1),
                ):
                    connection.append(j)

    return connection


def interclass_generate():
    connection_list = []

    age_grp = divide_age_grp(pdict, stud_age, stud_list)
    combination = combinations(age_grp.keys(), 2)
    for i in combination:
        connection_list += create_edges(age_grp[i[0]], age_grp[i[1]], 1)

    return connection_list


"""Combining result from above helper functions"""

edges_list = []
edges_list += create_edges(teach_list, teach_list, 3)
edges_list += create_edges(non_teach_list, non_teach_list, 6)
edges_list += create_edges(teach_list, non_teach_list, 3)
edges_list += create_edges(teach_list, stud_list, 3)  # For every teacher 3 students
edges_list += create_edges(stud_list, non_teach_list, 3)

# Age wise students to be added into classes & their interactions to be appended
edges_list += intraclass_generate(ncluster=5)
edges_list += interclass_generate()
edges_list = list(set(edges_list))

print(
    "The number of Edges formed are ",
    len(edges_list),
    "and one of the sample is ",
    edges_list[0],
)

"""# Initializing  `Contacts` network"""

categ_contact_matrix = [[10.0, 6.0, 0.8],  # s-s s-t s-nt
                        [6.0, 8.0, 2.0],  # t-s t-t t-nt
                        [0.8, 2.0, 4.0],]  # nt-s nt-t nt-nt

age_contact_matrix = Contact_school.to_numpy()


def add_nodes(pdict):
    node = []

    for k in pdict.keys():
        node.append((k,{"categ": pdict[k]["categ"],
                        "Age": pdict[k]["Age"],
                        "Infected": pdict[k]["Infected"],
                        "DayOfInfection": pdict[k]["day of infection"],
                        "Status": pdict[k]["Status"],
                        "risk_coeff": pdict[k]["danger"]},))

    return node


def edge_weights(contact_matrix_categ, contact_matrix_age, pdict, edge, mode):  # According to category
    i = edge[0]
    j = edge[1]

    categ_index = {"Students": 0, "Teaching": 1, "Non teaching": 2}

    if mode == "category":
        return contact_matrix_categ[categ_index[pdict[i]["categ"]]][categ_index[pdict[i]["categ"]]]
    elif mode == "age":
        return contact_matrix_age[pdict[i]["Age"] // 8][pdict[j]["Age"] // 8]
    else:
        raise NameError(mode)


def edge_weights_premetal(contact_matrix, pdict, edge):  # According to age
    i = edge[0]
    j = edge[1]
    return contact_matrix[pdict[i]["Age"] // 8][pdict[j]["Age"] // 8]


Contacts = nx.Graph()

Node_info = add_nodes(pdict)
Contacts.add_nodes_from(Node_info)

# Contacts graph will basically consist of the edge weight which would be the number of connects a node can make according to the age and also whether or not it is infected
Contacts.add_edges_from(edges_list)  

# transmission_weight will come from contact_matrix and hence we wont need above weights but this will depend on age

# Uncomment below for category one

edge_attribute_dict = {edge: edge_weights(categ_contact_matrix, 
                                          age_contact_matrix, 
                                          pdict, 
                                          edge, 
                                          mode="age")  # mode : age,category
                        for edge in Contacts.edges()}

nx.set_edge_attributes(Contacts, values=edge_attribute_dict, name="transmission_weight")

print("Contacts network done!")
'''
"""# EoN magic"""

#Graph which is not induced, for example: E -> I, I -> R 
H=nx.DiGraph()
H.add_node('S') #Susceptible
H.add_edge('E', 'I', rate = 0.29) #we can also have a weight label to add higher chances of people moving from E->I depending on duration- not needed now, need this rate, could be constant, need lit
H.add_edge('I', 'R', rate = 0.95) #need recovery rate for India/TN

#Induced Graph according to transmission rates or probability of transitions
J = nx.DiGraph()
for nodes in Contacts.nodes():
  if Contacts.nodes[nodes]["Status"] == "Asymptomatic":
    J.add_edge(('I', 'S'), ('I', 'E'), rate = 0.225, weight_label='transmission_weight')
  else:
    J.add_edge(('I', 'S'), ('I', 'E'), rate = 0.9, weight_label='transmission_weight') #Input - Transmission rate (beta)

IC={}   #initial status
for nodes in Contacts.nodes():
  if Contacts.nodes[nodes]["Infected"]== 1:
    IC[nodes]='I'
  else:
    IC[nodes]= 'S'

return_statuses = ('S', 'E', 'I', 'R')


#sim=EoN.Gillespie_SIR(Contacts,1,1,return_full_data=True)
t, S, E, I, R = EoN.Gillespie_simple_contagion(Contacts, 
                                               H, J, IC, 
                                               return_statuses,
                                               tmax = float('Inf'))

plt.semilogy(t, S, label = 'Susceptible')
plt.semilogy(t, E, label = 'Exposed')
plt.semilogy(t, I, label = 'Infected')
plt.semilogy(t, R, label = 'Recovered')
plt.legend()
#sim.display(time=1)
plt.show()

#T = sim.transmission_tree() #A networkx DiGraph with the transmission tree
#Tpos = EoN.hierarchy_pos(T) #pos for a networkx plot
#fig = plt.figure(figsize = (8,5))
#ax = fig.add_subplot(111)
#nx.draw(T, Tpos, ax=ax, node_size = 15, with_labels=True)
plt.show()
'''
