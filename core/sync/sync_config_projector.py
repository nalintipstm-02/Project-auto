from core.api_client import get
from core.db import execute


def sync_config_projector(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("config", {}).get("projector", [])

    for cp in rows:
        execute("""
            INSERT INTO config_projector (
                config_pro_id,
                node_id,
                rm_pro_ip,
                rm_pro_mac,
                ir_command_pro_on,
                ir_command_pro_off,
                sync_version
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                rm_pro_ip=VALUES(rm_pro_ip),
                rm_pro_mac=VALUES(rm_pro_mac),
                ir_command_pro_on=VALUES(ir_command_pro_on),
                ir_command_pro_off=VALUES(ir_command_pro_off),
                sync_version=VALUES(sync_version)
        """, (
            cp["config_pro_id"],
            cp["node_id"],
            cp["rm_pro_ip"],
            cp["rm_pro_mac"],
            cp["ir_command_pro_on"],
            cp["ir_command_pro_off"],
            cp["sync_version"]
        ))

    print("? config_projector synced")
