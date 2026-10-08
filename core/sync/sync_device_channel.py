from core.api_client import get
from core.db import execute

def sync_device_channel(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("device_channels", [])

    for dc in rows:
        execute("""
            INSERT INTO device_channel (
                id,
                node_id,
                device_type,
                gpio,
                name,
                is_active
            )
            VALUES (%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                device_type=VALUES(device_type),
                gpio=VALUES(gpio),
                name=VALUES(name),
                is_active=VALUES(is_active)
        """, (
            dc["id"],
            dc["node_id"],
            dc["device_type"],
            dc["gpio"],
            dc["name"],
            dc["is_active"]
        ))

    print("? device_channel synced")
