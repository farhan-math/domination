# 1. GENERATE MAP GRAPH

key_name      = "lalinea"
location_name = "La Línea de la Concepción, Spain"
landmark_name = "Plaza de toros el arenal, La Línea de la Concepción, Spain"

# This part generates the map graph. Comment if the graph file already exists

from generate_map import generate_map
graph, graph3km_raw, graph3km_filtered, landmark_node = generate_map(
    key_name, location_name, landmark_name, show_plot=False
    )

# Import map graph if the file already exists

import pickle

with open(f"{key_name}_graph.pkl", "rb") as f:
    graph = pickle.load(f)
with open(f"{key_name}_graph3km_raw.pkl", "rb") as f:
    graph3km_raw = pickle.load(f)
with open(f"{key_name}_graph3km_filtered.pkl", "rb") as f:
    graph3km_filtered = pickle.load(f)
with open(f"{key_name}_landmark_node.pkl", "rb") as f:
    landmark_node = pickle.load(f)

# 2. GENERATE MINIMAL DOMINATING SETS OF THE MAP
# This generates 2000 minimal dominating sets of the specified map graph
# The resulted sets will be saved in 4 bundles, each contains 500

from generate_mds import generate_mds
generate_mds(key_name, graph)

# 3. GRAPH INFORMATION

from tabulate import tabulate

graph_information = [
    ["graph", graph.number_of_nodes(), graph.number_of_edges()],
    ["graph3km_raw", graph3km_raw.number_of_nodes(), graph3km_raw.number_of_edges()],
    ["graph3km_filtered", graph3km_filtered.number_of_nodes(), graph3km_filtered.number_of_edges()]
]

headers = ["graph name", "nodes", "edges"]

print("===== GRAPH INFORMATION =====")
print(tabulate(graph_information, headers=headers, tablefmt="grid"))
print("")

# 4. MDS ANALYSIS

# MERGE DATA BUNDLES
# Open all result files and merge them into one set mds_list

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
graph_plot = graph3km_filtered

# Raw map
node_colors = []
node_sizes  = []

for node in graph_plot.nodes():
    if node == landmark_node:
        node_colors.append('#0000FF') # Neon Green: Landmark
        node_sizes.append(150)
    elif node in max_freq_nodes:
        node_colors.append('#FF0000') # Bright Red: Scooter Hubs
        node_sizes.append(70)
    else:
        node_colors.append('#333333') # Dark Grey: Other nodes
        node_sizes.append(10)

# Plotting the 3km reachable skeleton
plt.figure()
fig, ax = ox.plot_graph(
    graph_plot,
    node_color=node_colors,
    node_size=node_sizes,
    node_zorder=3,
    edge_color='#333333',
    edge_linewidth=0.7,
    bgcolor='w',
    show=False,
    close=False
)

plt.savefig(f"{key_name}_3km_final.pdf", dpi=300, bbox_inches='tight')