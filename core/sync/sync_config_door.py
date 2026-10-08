from core.api_client import get
from core.db import execute

def sync_config_door(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("config", {}).get("door", [])

    for cd in rows:
        execute("""
            INSERT INTO config_door (
                node_id,
                mqtt_broker,
                mqtt_port,
                command_door_open,
                command_door_close,
                sync_version
            )
            VALUES (%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                mqtt_broker=VALUES(mqtt_broker),
                mqtt_port=VALUES(mqtt_port),
                command_door_open=VALUES(command_door_open),
                command_door_close=VALUES(command_door_close),
                sync_version=VALUES(sync_version)
        """, (
            cd["node_id"],
            cd["mqtt_broker"],
            cd["mqtt_port"],
            cd["command_door_open"],
            cd["command_door_close"],
            cd["sync_version"]
        ))

    print("? config_door synced")
