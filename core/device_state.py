# device_state.py

from core.db import get_conn
from core.runtime_state import get_runtime_state

def init_device_status():

    runtime = get_runtime_state()
    if not runtime:
        return

    conn = get_conn()
    cur = conn.cursor()

    for node_id, node in runtime["nodes"].items():

        node_type = node.get("node_type")

        # -------- LED DEVICE --------
        if node_type == "led":

            channels = runtime.get("device_channels", {}).get(node_id, [])

            if channels:

                for ch in channels:

                    ch_id = ch["channel_id"]

                    cur.execute("""
                        INSERT INTO device_status (node_id, channel, status, updated_at)
                        VALUES (%s,%s,'off',NOW())
                        ON DUPLICATE KEY UPDATE
                            status='off',
                            updated_at = NOW()
                    """, (node_id, ch_id))

            else:
                # led single channel
                cur.execute("""
                    INSERT INTO device_status (node_id, channel, status, updated_at)
                    VALUES (%s,0,'off',NOW())
                    ON DUPLICATE KEY UPDATE
                        status='off',
                        updated_at = NOW()
                """, (node_id,))

        # -------- NORMAL DEVICE --------
        else:

            cur.execute("""
                INSERT INTO device_status (node_id, channel, status, updated_at)
                VALUES (%s,0,'off',NOW())
                ON DUPLICATE KEY UPDATE
                    status='off',
                    updated_at = NOW()
            """, (node_id,))

    conn.commit()
    cur.close()
    conn.close()

    print("[INIT] device_status ready")
    


def update_device_status(node_id, channel, status):

    if channel is None:
        channel = 0

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE device_status
        SET status=%s,
            updated_at=NOW()
        WHERE node_id=%s AND channel=%s
    """, (status, node_id, channel))

    conn.commit()
    cur.close()
    conn.close()
