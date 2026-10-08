from core.api_client import get
from core.db import execute


def sync_building(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    buildings = resp["data"].get("building", [])

    for b in buildings:
        execute("""
            INSERT INTO Building (building_id, building_name, location, sync_version)
            VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                building_name=VALUES(building_name),
                location=VALUES(location),
                sync_version=VALUES(sync_version)
        """, (
            b["building_id"],
            b["building_name"],
            b["location"],
            b["sync_version"]
        ))

    print("building synced")
