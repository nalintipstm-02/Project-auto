from core.api_client import get
from core.db import execute


def sync_cluster(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    clusters = resp["data"].get("cluster", [])

    for c in clusters:
        execute("""
            INSERT INTO Cluster (cluster_id, cluster_name, sync_version)
            VALUES (%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                cluster_name=VALUES(cluster_name),
                sync_version=VALUES(sync_version)
        """, (
            c["cluster_id"],
            c["cluster_name"],
            c["sync_version"]
        ))

    print("cluster synced")
