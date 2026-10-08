from core.api_client import get
from core.db import execute


def sync_building_detail(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("building_detail", [])

    for bd in rows:
        execute("""
            INSERT INTO Building_detail (
                building_id,
                cluster_id,
                sync_version
            )
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                cluster_id   = VALUES(cluster_id),
                sync_version = VALUES(sync_version)
        """, (
            bd["building_id"],
            bd["cluster_id"],
            bd["sync_version"]
        ))

    print("building_detail synced")

