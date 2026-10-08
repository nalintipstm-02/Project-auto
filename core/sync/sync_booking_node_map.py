from core.api_client import get
from core.db import execute


def sync_booking_node_map(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    cbnm = resp["data"].get("cluster_booking_node_map", [])

    for bn in cbnm:
        execute("""
            INSERT INTO cluster_booking_node_map
            (booking_id, node_id, sync_version)
            VALUES (%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                sync_version=VALUES(sync_version)
        """, (
            bn["booking_id"],
            bn["node_id"],
            bn["sync_version"]
        ))

    print("? booking-node-map synced")
