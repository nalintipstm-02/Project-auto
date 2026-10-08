from core.api_client import get
from core.db import execute


def sync_node(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("node", [])

    for n in rows:
        execute("""
            INSERT INTO Node (
                node_id,
                node_type,
                node_name,
                node_status,
                computer_role,
                sync_version
            )
            VALUES (%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                node_type=VALUES(node_type),
                node_name=VALUES(node_name),
                node_status=VALUES(node_status),
                computer_role=VALUES(computer_role),
                sync_version=VALUES(sync_version)
        """, (
            n["node_id"],
            n["node_type"],
            n["node_name"],
            n["node_status"],
            n.get("computer_role"),
            n["sync_version"]
        ))

    print("? node synced")
