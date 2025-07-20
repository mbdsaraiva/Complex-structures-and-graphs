# Main imports
import pandas as pd           # For data manipulation and reading tabular files
import networkx as nx         # For building and analyzing graphs
import matplotlib.pyplot as plt  # For plotting graphs
import numpy as np            # For numerical operations
import os

# Optional configurations
plt.style.use("ggplot")       # Sets the plot style to 'ggplot' for better aesthetics

# Paths to the input files
nodes_file = r"DATABASE\1A3N.cif_ringNodes"
edges_file = r"DATABASE\1A3N.cif_ringEdges"

# Load data into DataFrames
df_nodes = pd.read_csv(nodes_file, sep="\t")  # Reads the node table using tab as separator
df_edges = pd.read_csv(edges_file, sep="\t")  # Reads the edge table using tab as separator

# Preview the node data
print("Nodes:")
print(df_nodes.head().to_string())  # Shows the first few rows of the node DataFrame

# Preview the edge data
print("Edges:")
print(df_edges.head().to_string())  # Shows the first few rows of the edge DataFrame

# Initialize as a MultiDiGraph to support multiple directed edges between the same pair of nodes
# G = nx.MultiDiGraph()

# Use MultiGraph() instead of MultiDiGraph() if directionality is not important.
# This allows multiple undirected edges between the same node pairs, useful for modeling
# symmetric or bidirectional interactions like Van der Waals forces.
G = nx.MultiGraph()

# Add all nodes with their attributes
for _, row in df_nodes.iterrows():
    node_id = row["NodeId"]                      # Extract the node identifier
    attributes = row.drop("NodeId").to_dict()    # Convert the remaining columns to a dictionary of attributes
    G.add_node(node_id, **attributes)            # Add the node and its attributes to the graph

print(f"Graph created with {G.number_of_nodes()} nodes.")

# Accessing the attributes of a specific node in the graph
# Each node represents an abstract element with several associated properties.
# These attributes may include:
# - Position: the element's index or sequence number
# - Type: classification or category of the element
# - Degree: number of connections this node has in the graph
# - Numerical values (e.g., factor_CA): possibly representing some measurement or score
# - Coordinates (x, y, z): spatial or geometric positioning
# - Metadata: such as source file name or model identifier

print(G.nodes.get("A:1:_:V", "Node not found."))

# Adds all columns as edge attributes, allowing multiple edges between the same pair of nodes
for _, row in df_edges.iterrows():
    source = row["NodeId1"]                  # Source node identifier
    target = row["NodeId2"]                  # Target node identifier
    attributes = row.drop(["NodeId1", "NodeId2"]).to_dict()  # All remaining columns become edge attributes

    # Safe conversion of numeric values (e.g., distance, angle, etc.)
    for key in attributes:
        val = attributes[key]
        if pd.isna(val) or val == "nan":     # Handle missing or non-numeric values
            attributes[key] = None
        else:
            try:
                attributes[key] = float(val)  # Convert strings to float when possible
            except (ValueError, TypeError):
                pass  # Leave as string if conversion fails

    # Add the edge with its full set of attributes
    # Since we are using MultiDiGraph, multiple edges between the same nodes are allowed and preserved
    G.add_edge(source, target, **attributes)

print(f"Graph created with {G.number_of_edges()} edges (multiple interactions per node pair allowed).")

# Accessing the attributes of a specific edge in a MultiDiGraph
# Since multiple edges are allowed between the same pair of nodes, we use a 3-element key:
# (source_node, target_node, edge_index)
# This retrieves the edge with index 0 between nodes "A:1:_:V" and "A:81:_:L"
try:
    print(G.edges[('A:1:_:V', 'A:81:_:L', 0)])
except KeyError:
    print("Edge ('A:1:_:V', 'A:81:_:L', 0) not found.")

# The returned dictionary contains all the metadata associated with this specific interaction:
# - Interaction: a label describing the type of interaction or connection
# - Distance: a numeric value that may represent spatial proximity or intensity
# - Angle: geometric property, if applicable
# - Node1 / Node2: identifiers for specific components involved in the interaction
# - Donor, Positive, Ct, Orientation: optional descriptors that may or may not be filled
# - Model: model or version identifier, useful in some datasets

# Example: list all edges from node A:4:_:T to node A:7:_:E
source = "A:4:_:T"
target = "A:7:_:E"

# Retrieves a dictionary containing all edges between the two nodes,
# where each entry is indexed by a unique edge key (usually an integer starting from 0)
multi_edges = G.get_edge_data(source, target)

# Print all individual interactions (edges) between these two nodes
if multi_edges:
    for key, attrs in multi_edges.items():
        print(f"Edge {key}:")  # Each key represents a unique edge ID between the same source and target
        for attr, value in attrs.items():
            print(f"  {attr}: {value}")  # Print each attribute of the edge
        print()
else:
    print("No edges found between the specified nodes.")

def sanitize_attributes(G):
    # Fix node attributes: replace None or NaN values with empty strings
    for node, attrs in G.nodes(data=True):
        for k, v in attrs.items():
            if v is None or (isinstance(v, float) and pd.isna(v)):
                G.nodes[node][k] = ""

    # Fix edge attributes: replace None or NaN values with empty strings
    for u, v, key, attrs in G.edges(keys=True, data=True):
        for k, v_attr in attrs.items():
            if v_attr is None or (isinstance(v_attr, float) and pd.isna(v_attr)):
                G.edges[u, v, key][k] = ""

# Apply attribute sanitization to make the graph exportable to GEXF format
sanitize_attributes(G)

# Export the graph to a GEXF file, which can be opened in Gephi or reloaded in Python
os.makedirs("DATABASE", exist_ok=True)
nx.write_gexf(G, "DATABASE/final_network.gexf")
print("Export completed successfully.")

# Generate a layout for positioning the nodes using a force-directed algorithm
# 'seed' ensures the layout is reproducible
pos = nx.spring_layout(G, seed=42)

# Set up the figure size
plt.figure(figsize=(12, 10))

# Draw the graph nodes with small size and light color
nx.draw_networkx_nodes(G, pos, node_size=10, node_color='skyblue', alpha=0.7)

# Draw the edges with some transparency
nx.draw_networkx_edges(G, pos, alpha=0.3)

# Set the plot title and remove axes
plt.title("Graph")
plt.axis('off')

# Display the final visualization
plt.show()
