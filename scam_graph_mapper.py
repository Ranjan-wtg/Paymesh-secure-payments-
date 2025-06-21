import sqlite3
import os
import matplotlib.pyplot as plt
import networkx as nx

# --- Config ---
BASE_DIR = r"D:\The New Data Trio"
DB_PATH = os.path.join(BASE_DIR, "ledger.db")
GRAPH_IMG_PATH = os.path.join(BASE_DIR, "scam_graph.png")

# --- Scam Graph Builder ---
def build_scam_graph(limit=30):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Only fetch risky txns (fraud OR phishing OR major flags)
    cursor.execute('''
        SELECT to_user, amount, time, is_fraud, is_phishing, flags
        FROM transactions
        WHERE is_fraud=1 OR is_phishing=1
        ORDER BY id DESC
        LIMIT ?
    ''', (limit,))
    txns = cursor.fetchall()
    conn.close()

    G = nx.DiGraph()
    source_node = "YOU"

    for txn in txns:
        to_user, amount, time, is_fraud, is_phishing, flags = txn
        label = f"{amount} @ {time}"
        G.add_edge(source_node, to_user, label=label)

        # Highlight risky nodes
        if is_fraud or is_phishing or ("amount_outlier" in flags or "odd_hour" in flags):
            G.nodes[to_user]["color"] = "red"
        else:
            G.nodes[to_user]["color"] = "skyblue"

    # Draw graph
    node_colors = [G.nodes[n].get("color", "skyblue") for n in G.nodes]

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=1200, font_size=8, font_weight='bold', edge_color='gray', arrowsize=20)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)

    plt.title("🕸️ Scam UPI Graph (Recent Risky Txns)", fontsize=10)
    plt.tight_layout()
    plt.savefig(GRAPH_IMG_PATH, dpi=150)
    plt.close()

    print(f"✅ Scam graph saved at {GRAPH_IMG_PATH}")

# ✅ Run this to generate
if __name__ == "__main__":
    build_scam_graph(limit=30)
