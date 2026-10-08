from core.api_client import get
from core.db import execute


def sync_bookings(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("bookings", [])

    for bk in rows:
        execute("""
            INSERT INTO bookings
            (booking_id, room_id, booking_date, start_time, end_time, status, sync_version)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                start_time=VALUES(start_time),
                end_time=VALUES(end_time),
                status=VALUES(status),
                sync_version=VALUES(sync_version)
        """, (
            bk["id"],
            bk["room_id"],
            bk["booking_date"],
            bk["start_time"],
            bk["end_time"],
            bk["status"],
            bk["sync_version"]
        ))

    print("? bookings synced")
