import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import pickle

def generate_map(key_name, location_name, landmark_name, show_plot=False):
    # 1. SETTINGS & FILTERS
    # Filtering for scooter-legal roads (excludes motorways and footpaths)
    hwy_types = [
        'primary', 'secondary', 'tertiary', # Major urban streets (usually have bike lanes or are allowed)
        'residential', 'living_street',     # Neighborhood streets (the "core" of your coverage)
        'unclassified', 'service',          # Small connectors and alleys
        'cycleway'                          # Dedicated bike paths (the "gold standard" for scooters)
    ]
    custom_filter = f'["highway"~"{"|".join(hwy_types)}"]'

    # 2. DOWNLOAD & SIMPLIFY
    location = location_name
    # Complete network for visualization only
    graph_raw = ox.graph_from_place(location)
    # Filtered network for analysis
    graph_filtered = ox.graph_from_place(location, custom_filter=custom_filter)

    # 3. IDENTIFY LANDMARK
    landmark = landmark_name
    # Get the landmark's coordinates
    landmark_coords = ox.geocoder.geocode(landmark)
    # Find the node nearest to the landmark
    landmark_node = ox.distance.nearest_nodes(graph_filtered, X=landmark_coords[1], Y=landmark_coords[0])

    # 4. EXTRACT 3KM REACHABLE NETWORK
    # Change: radius set to 3000 meters
    radius_meters = 3000
    graph3km_raw = nx.ego_graph(graph_raw, landmark_node, radius=radius_meters, distance='length')
    graph3km_filtered = nx.ego_graph(graph_filtered, landmark_node, radius=radius_meters, distance='length')

    # 5. GRAPH CLEANING FOR ANALYSIS (MDS CALCULATIONS)
    # Convert to undirected and then to a simple graph
    graph3km_filtered_undirected = ox.convert.to_undirected(graph3km_filtered)
    graph3km_filtered_simple = nx.Graph(graph3km_filtered_undirected)

    # Keep only the largest connected component
    largest_cc = max(nx.connected_components(graph3km_filtered_simple), key=len)
    graph3km_filtered_final = graph3km_filtered_simple.subgraph(largest_cc).copy()

    # Remove self loops
    graph3km_filtered_final.remove_edges_from(nx.selfloop_edges(graph3km_filtered_final))

    # The clean graph
    graph = nx.Graph(graph3km_filtered_final)

    # Save the graphs
    with open(f"{key_name}_graph.pkl", "wb") as f:
        pickle.dump(graph, f)
    with open(f"{key_name}_graph3km_raw.pkl", "wb") as f:
        pickle.dump(graph3km_raw, f)
    with open(f"{key_name}_graph3km_filtered.pkl", "wb") as f:
        pickle.dump(graph3km_filtered, f)
    with open(f"{key_name}_landmark_node.pkl", "wb") as f:
        pickle.dump(landmark_node, f)

    # 6. VISUALIZATION
    # Cast back to MultiGraph for OSMnx plotting
    graph3km_raw_plot = graph3km_raw
    graph3km_filtered_plot = nx.MultiGraph(graph)

    # Raw map
    node_colors_raw = []
    node_sizes_raw = []

    for node in graph3km_raw_plot.nodes():
        if node == landmark_node:
            node_colors_raw.append('#0000FF') # Neon Green: Plaza Alta
            node_sizes_raw.append(150)
        else:
            node_colors_raw.append('#333333') # Dark Grey: Other nodes
            node_sizes_raw.append(10)

    # Plotting the 3km reachable skeleton
    fig1, ax1 = ox.plot_graph(
        graph3km_raw_plot,
        node_color=node_colors_raw,
        node_size=node_sizes_raw,
        node_zorder=3,
        edge_color='#333333',
        edge_linewidth=0.7,
        bgcolor='w',
        show=False,
        close=False
    )

    plt.savefig(f"{key_name}_3km_raw.pdf", dpi=300, bbox_inches='tight')

    # print("graph3km_raw information")
    # print(f"number of nodes: {graph3km_raw.number_of_nodes()}")
    # print(f"number of edges: {graph3km_raw.number_of_edges()}")
    # print("")

    # Filtered map
    node_colors_filtered = []
    node_sizes_filtered = []

    for node in graph3km_filtered_plot.nodes():
        if node == landmark_node:
            node_colors_filtered.append('#0000FF') # Neon Green: Plaza Alta
            node_sizes_filtered.append(150)
        else:
            node_colors_filtered.append('#333333') # Dark Grey: Other nodes
            node_sizes_filtered.append(10)

    # Plotting the 3km reachable skeleton
    fig2, ax2 = ox.plot_graph(
        graph3km_filtered_plot,
        node_color=node_colors_filtered,
        node_size=node_sizes_filtered,
        node_zorder=3,
        edge_color='#333333',
        edge_linewidth=0.7,
        bgcolor='w',
        show=False,
        close=False
    )

    plt.savefig(f"{key_name}_3km_filtered.pdf", dpi=300, bbox_inches='tight')

    # print("graph3km_filtered (cleaned) information")
    # print(f"number of nodes: {graph.number_of_nodes()}")
    # print(f"number of edges: {graph.number_of_edges()}")
    if show_plot:
        plt.show()

    return graph, graph3km_raw, graph3km_filtered, landmark_node