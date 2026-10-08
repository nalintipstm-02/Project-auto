from core.api_client import get
from core.db import execute


def sync_cluster_detail(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("cluster_detail", [])

    for ct in rows:
        execute("""
            INSERT INTO Cluster_Detail (
                cluster_id,
                room_id,
                sync_version
            )
            VALUES ( %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                cluster_id   = VALUES(cluster_id),
                room_id      = VALUES(room_id),
                sync_version = VALUES(sync_version)
        """, (
            ct["cluster_id"],
            ct["room_id"],
            ct["sync_version"]
        ))

    print("cluster_detail synced")
