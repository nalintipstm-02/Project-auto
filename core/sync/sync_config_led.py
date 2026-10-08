from core.api_client import get
from core.db import execute

def sync_config_led(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("config", {}).get("led", [])

    for cl in rows:
        execute("""
            INSERT INTO config_led (
                node_id,
                command_led_on,
                command_led_off,
                mqtt_broker,
                mqtt_port,
                sync_version
            )
            VALUES (%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                command_led_on=VALUES(command_led_on),
                command_led_off=VALUES(command_led_off),
                mqtt_broker=VALUES(mqtt_broker),
                mqtt_port=VALUES(mqtt_port),
                sync_version=VALUES(sync_version)
        """, (
            cl["node_id"],
            cl["command_led_on"],
            cl["command_led_off"],
            cl["mqtt_broker"],
            cl["mqtt_port"],
            cl["sync_version"]
        ))

    print("? config_led synced")
