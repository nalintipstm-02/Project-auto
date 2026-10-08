from core.api_client import get
from core.db import execute


def sync_config_computer(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("config", {}).get("computer", [])

    for cc in rows:
        execute("""
            INSERT INTO config_computer (
                config_com_id,
                node_id,
                ip_address,
                port_on,
                port_off,
                command_com_on,
                command_com_off,
                mqtt_broker,
                mqtt_port,
                sync_version
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                ip_address=VALUES(ip_address),
                port_on=VALUES(port_on),
                port_off=VALUES(port_off),
                command_com_on=VALUES(command_com_on),
                command_com_off=VALUES(command_com_off),
                mqtt_broker=VALUES(mqtt_broker),
                mqtt_port=VALUES(mqtt_port),
                sync_version=VALUES(sync_version)
        """, (
            cc["config_com_id"],
            cc["node_id"],
            cc["ip_address"],
            cc["port_on"],
            cc["port_off"],
            cc["command_com_on"],
            cc["command_com_off"],
            cc["mqtt_broker"],
            cc["mqtt_port"],
            cc["sync_version"]
        ))

    print("? config_computer synced")
