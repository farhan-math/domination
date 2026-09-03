# 1. GENERATE GRAPH

n        = 7
key_name = f"strong_{n}"

import networkx as nx

graph = nx.strong_product(
    nx.path_graph(3*n),
    nx.path_graph(3*n)
    )

# 2. GENERATE MINIMAL DOMINATING SETS OF THE GRAPH
# This generates 2000 minimal dominating sets of the strong grid
# The resulted sets will be saved in 4 bundles, each contains 500

# from generate_mds import generate_mds
# generate_mds(key_name, graph)

# 3. MDS ANALYSIS

# MERGE DATA BUNDLES
# Open all result files and merge them into one set mds_list

import pickle

mds_list = []
for i in range(1,5):
    with open(f'{key_name}_0.1_100_{i}.pkl', 'rb') as f:
        mds_list += pickle.load(f)

# UNIQUENESS TEST
# Check if all 2000 MDS generated are pairwise distinct

# Convert each set to a frozenset, then wrap in a set to remove duplicates
unique_frozensets = set(frozenset(mds) for mds in mds_list)

# Convert back to a list of regular sets if needed
unique_list = [set(mds) for mds in unique_frozensets]

print("===== UNIQUENESS TEST =====")
print(f"Each MDS generated is unique : {len(unique_list) == len(mds_list)}")
print(f"Number of unique MDS         : {len(unique_list)} \n")

# MDS LENGTH DISTRIBUTION

from collections import Counter

length = [len(mds) for mds in mds_list]
min_length = min(length)
max_length = max(length)

print("===== MDS LENGTH DISTRIBUTION =====")
print(f"minimum length: {min_length}")
print(f"maximum length: {max_length} \n")

dist_length = Counter(length)
dist_set    = {}
for length in range(min_length,max_length+1):
    dist_set[length] = [mds for mds in mds_list if len(mds) == length]

with open(f'{key_name}_distribution.txt', 'w') as f:
    for item in sorted(dist_length.items()):
        f.write(f"{item}\n")

# CREATE THE DISTRIBUTION PLOT

import matplotlib.pyplot as plt

plt.figure()
plt.bar(dist_length.keys(), dist_length.values(), color='skyblue', edgecolor='navy')

# Add labels and title
plt.xlabel('Set Lengths')
plt.ylabel('Number of MDS Generated')
plt.title('MDS Length Distribution')

# Save the plot
plt.savefig(f"{key_name}_distribution.png")

# NODES WITH MAXIMUM FREQUENCY

# Counts the number of appearances of each node across all generated mds
counts = Counter(node for mds in mds_list for node in mds)

# Find the maximum frequency value
max_freq = max(counts.values())

# Extract all nodes with the maximum frequency
max_freq_nodes = [node for node, count in counts.items() if count == max_freq]

print("===== NODES WITH MAX FREQUENCY =====")
print(f"max_freq       : {max_freq}")
print(f"max_freq_nodes : {len(max_freq_nodes)}")
print(f"total nodes    : {graph.number_of_nodes()}")
print(f"% of nodes     : {len(max_freq_nodes) / graph.number_of_nodes() * 100}")

# 5. SHOW IN MAP
# Show in the map all nodes with maximum frequency

import osmnx as ox

# Cast back to MultiGraph for OSMnx plotting
graph_plot = graph

pos = {node: node for node in graph.nodes()}

# Raw map
node_colors = []
node_sizes  = []

for node in graph_plot.nodes():
    if node in max_freq_nodes:
        node_colors.append('#FF0000') # Bright Red: Scooter Hubs
        node_sizes.append(70)
    else:
        node_colors.append('#333333') # Dark Grey: Other nodes
        node_sizes.append(10)

# Plotting the 3km reachable skeleton

plt.figure(figsize=(3*n, 3*n))
nx.draw(
    graph,
    pos=pos,
    with_labels=True,
    node_color=node_colors,
    node_size=node_sizes,
    edge_color="gray",
)

plt.axis("equal")  # Ensures grid spacing remains square
plt.savefig(f"{key_name}_final.pdf", dpi=300, bbox_inches='tight')