from core.api_client import get
from core.db import execute


def sync_installation(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("installation_node", [])

    for i in rows:
        execute("""
            INSERT INTO Installation_Node (
                node_id,
                room_id,
                status,
                sync_version
            )
            VALUES ( %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                node_id = VALUES(node_id),
                room_id = VALUES(room_id),
                status = VALUES(status),
                sync_version = VALUES(sync_version)
        """, (
            i["node_id"],
            i["room_id"],
            i["status"],
            i["sync_version"]
        ))

    print("? installation synced")
