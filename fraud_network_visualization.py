import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# -----------------------------
# STEP 1: LOAD DATA
# -----------------------------
df = pd.read_excel("fraud_tracking_report.xlsx")

# Limit for clarity
df = df.head(30)

# -----------------------------
# STEP 2: CREATE GRAPH
# -----------------------------
G = nx.Graph()

for _, row in df.iterrows():
    sender = f"S_{row['sender_account']}"
    receiver = f"R_{row['receiver_account']}"
    ip = f"IP_{row['ip_address']}"
    device = f"D_{row['device_hash']}"

    G.add_edge(sender, receiver)
    G.add_edge(receiver, ip)
    G.add_edge(ip, device)

# -----------------------------
# STEP 3: DRAW GRAPH
# -----------------------------
plt.figure(figsize=(16, 12))

pos = nx.spring_layout(G, k=0.8, seed=42)

# Node colors
color_map = []
for node in G:
    if node.startswith("S_"):
        color_map.append("#3b82f6")   # Blue
    elif node.startswith("R_"):
        color_map.append("#ef4444")   # Red
    elif node.startswith("IP_"):
        color_map.append("#22c55e")   # Green
    else:
        color_map.append("#f59e0b")   # Orange

# Draw nodes
nx.draw_networkx_nodes(
    G, pos,
    node_color=color_map,
    node_size=500,
    alpha=0.9
)

# Draw edges
nx.draw_networkx_edges(
    G, pos,
    width=1,
    alpha=0.4
)

# Labels (smaller for readability)
nx.draw_networkx_labels(
    G, pos,
    font_size=6
)

# -----------------------------
# STEP 4: LEGEND
# -----------------------------
import matplotlib.patches as mpatches

legend_elements = [
    mpatches.Patch(color='#3b82f6', label='Sender'),
    mpatches.Patch(color='#ef4444', label='Receiver'),
    mpatches.Patch(color='#22c55e', label='IP'),
    mpatches.Patch(color='#f59e0b', label='Device')
]

plt.legend(handles=legend_elements, loc='upper left')

# -----------------------------
# STEP 5: FINAL SETTINGS
# -----------------------------
plt.title("Fraud Network Graph", fontsize=16)
plt.axis("off")
plt.tight_layout()

# ✅ IMPORTANT: SAVE BEFORE SHOW
plt.savefig("fraud_network.png", dpi=300, bbox_inches="tight")

# Optional display
# plt.show()

plt.close()