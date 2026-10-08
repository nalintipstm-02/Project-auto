from core.api_client import get
from core.db import execute

def sync_config_audio_equipment(cluster_id):
    resp = get(f"sync/cluster/{cluster_id}")
    rows = resp["data"].get("config", {}).get("audio", [])

    for ca in rows:
        execute("""
            INSERT INTO config_audio_equipment (
                config_audio_id,
                node_id,
                command_audio_on,
                command_audio_off,
                mqtt_broker,
                mqtt_port,
                sync_version
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                command_audio_on=VALUES(command_audio_on),
                command_audio_off=VALUES(command_audio_off),
                mqtt_broker=VALUES(mqtt_broker),
                mqtt_port=VALUES(mqtt_port),
                sync_version=VALUES(sync_version)
        """, (
            ca["config_audio_id"],
            ca["node_id"],
            ca["command_audio_on"],
            ca["command_audio_off"],
            ca["mqtt_broker"],
            ca["mqtt_port"],
            ca["sync_version"]
        ))

    print("? config_audio_equipment synced")
