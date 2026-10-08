from core.api_client import get
from core.db import execute

def sync_booking_led_channel(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("booking_led_channel", [])

    for blc in rows:
        execute("""
            INSERT INTO booking_led_channel (
                booking_id,
                node_id,
                channel_id
            )
            VALUES (%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                channel_id=VALUES(channel_id)
        """, (
            blc["booking_id"],
            blc["node_id"],
            blc["channel_id"]
        ))

    print("? booking_led_channel synced")
