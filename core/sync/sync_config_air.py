from core.api_client import get
from core.db import execute


def sync_config_air(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("config", {}).get("air", [])

    for a in rows:
        execute("""
            INSERT INTO config_air (
                config_air_id,
                node_id,
                rm_air_ip,
                rm_air_mac,
                ir_command_air_on,
                ir_command_air_off,
                sync_version
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                rm_air_ip=VALUES(rm_air_ip),
                rm_air_mac=VALUES(rm_air_mac),
                ir_command_air_on=VALUES(ir_command_air_on),
                ir_command_air_off=VALUES(ir_command_air_off),
                sync_version=VALUES(sync_version)
        """, (
            a["config_air_id"],
            a["node_id"],
            a["rm_air_ip"],
            a["rm_air_mac"],
            a["ir_command_air_on"],
            a["ir_command_air_off"],
            a["sync_version"]
        ))

    print("config_air synced")
