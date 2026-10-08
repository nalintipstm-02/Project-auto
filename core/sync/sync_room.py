from core.api_client import get
from core.db import execute


def sync_room(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("room", [])

    for r in rows:
        execute("""
            INSERT INTO Room (room_id, room_name, floor_number, room_type, sync_version)
            VALUES (%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                room_name=VALUES(room_name),
                sync_version=VALUES(sync_version)
        """, (
            r["room_id"],
            r["room_name"],
            r["floor_number"],
            r["room_type"],
            r["sync_version"]
        ))

    print("? room synced")
