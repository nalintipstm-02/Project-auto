import json
import threading
import paho.mqtt.client as mqtt
import time

from core.config import CLUSTER_ID
from core.runtime_state import reload_runtime_state, get_runtime_state
from core.scheduler import wakeup_scheduler,print_summary_table


# ===== IMPORT SYNC FUNCTIONS =====
from core.sync.sync_building import sync_building
from core.sync.sync_building_detail import sync_building_detail
from core.sync.sync_cluster import sync_cluster
from core.sync.sync_cluster_detail import sync_cluster_detail
from core.sync.sync_room import sync_room
from core.sync.sync_node import sync_node
from core.sync.sync_installation import sync_installation
from core.sync.sync_bookings import sync_bookings
from core.sync.sync_booking_node_map import sync_booking_node_map
from core.sync.sync_config_led import sync_config_led
from core.sync.sync_config_computer import sync_config_computer
from core.sync.sync_config_air import sync_config_air
from core.sync.sync_config_projector import sync_config_projector
from core.sync.sync_config_audio_equipment import sync_config_audio_equipment
from core.sync.sync_config_door import sync_config_door
from core.sync.sync_device_channel import sync_device_channel
from core.sync.sync_booking_led_channel import sync_booking_led_channel


MQTT_BROKER = "192.168.1.101"
MQTT_PORT = 1883
MQTT_TOPIC = "sync/event"

sync_lock = threading.Lock()


# ===============================
# TABLE -> FUNCTION MAP
# ===============================
def run_sync(table_name):

    print(f"\n[MQTT SYNC] Table changed: {table_name}\n")

    if table_name == "building":
        sync_building(CLUSTER_ID)

    elif table_name == "building_detail":
        sync_building_detail(CLUSTER_ID)

    elif table_name == "cluster":
        sync_cluster(CLUSTER_ID)

    elif table_name == "cluster_detail":
        sync_cluster_detail(CLUSTER_ID)

    elif table_name == "room":
        sync_room(CLUSTER_ID)

    elif table_name == "node":
        sync_node(CLUSTER_ID)

    elif table_name == "installation_node":
        sync_installation(CLUSTER_ID)

    elif table_name == "booking_bundle":
        time.sleep(0.3)
        sync_bookings(CLUSTER_ID)
        sync_booking_node_map(CLUSTER_ID)
        sync_booking_led_channel(CLUSTER_ID)

    elif table_name == "config_led":
        sync_config_led(CLUSTER_ID)

    elif table_name == "config_computer":
        sync_config_computer(CLUSTER_ID)

    elif table_name == "config_air":
        sync_config_air(CLUSTER_ID)

    elif table_name == "config_projector":
        sync_config_projector(CLUSTER_ID)

    elif table_name == "config_audio_equipment":
        sync_config_audio_equipment(CLUSTER_ID)

    elif table_name == "config_door":
        sync_config_door(CLUSTER_ID)
        
    elif table_name == "device_channel":
        sync_device_channel(CLUSTER_ID)
        
    elif table_name == "api_update":

        print("[MQTT SYNC] FULL API UPDATE")
        
        from core.main import full_sync

        full_sync()


    else:
        print(f"[MQTT SYNC] Unknown table: {table_name}")
        return

    print("[MQTT SYNC] DB updated")

    reload_runtime_state()
    state = get_runtime_state()
    print_summary_table(state)
    wakeup_scheduler()

    print("[MQTT SYNC] Runtime reloaded + Scheduler awakened\n")


# ===============================
# MQTT CALLBACKS
# ===============================
def on_connect(client, userdata, flags, rc):
    print("[MQTT] Connected with result code", rc)
    client.subscribe(MQTT_TOPIC)
    print(f"[MQTT] Subscribed to {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print("RAW MQTT PAYLOAD:", payload)

        data = json.loads(payload)

        table = data.get("table")
        event = data.get("event")

        print(f"[MQTT] Table: {table}, Event: {event}")

        if not table:
            print("[MQTT] No table field in payload")
            return

        # sync
        with sync_lock:
            run_sync(table)

    except Exception as e:
        print("[MQTT ERROR]", e)


def start_mqtt_listener():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    print("[MQTT] Listening for sync events...")
    client.loop_start()
