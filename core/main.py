# main.py

import time
import threading
import datetime

from core.runtime_state import load_runtime_state, get_runtime_state, reload_runtime_state
from core.scheduler import scheduler_loop, wakeup_scheduler, print_summary_table
from core.mqtt_sync_listener import start_mqtt_listener
from core.device_state import init_device_status

# ================== SYNC MODULES ==================
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

from core.config import CLUSTER_ID


# ================= FULL SYNC =================
def full_sync():

    print("\n===== FULL API SYNC START =====\n")

    sync_building(CLUSTER_ID)
    sync_cluster(CLUSTER_ID)
    sync_building_detail(CLUSTER_ID)
    sync_room(CLUSTER_ID)
    sync_cluster_detail(CLUSTER_ID)
    sync_node(CLUSTER_ID)
    sync_installation(CLUSTER_ID)

    sync_bookings(CLUSTER_ID)
    sync_booking_node_map(CLUSTER_ID)

    sync_config_led(CLUSTER_ID)
    sync_config_computer(CLUSTER_ID)
    sync_config_air(CLUSTER_ID)
    sync_config_projector(CLUSTER_ID)
    sync_config_audio_equipment(CLUSTER_ID)
    sync_config_door(CLUSTER_ID)

    sync_device_channel(CLUSTER_ID)
    
    sync_booking_led_channel(CLUSTER_ID)

    print("\n===== FULL API SYNC DONE =====\n")


# ================= MIDNIGHT SYNC (NO WHILE LOOP) =================
def schedule_midnight_sync():

    now = datetime.datetime.now()

    tomorrow = now + datetime.timedelta(days=1)

    midnight = datetime.datetime(
        tomorrow.year,
        tomorrow.month,
        tomorrow.day,
        0,
        0,
        0
    )

    seconds = (midnight - now).total_seconds()

    print(f"[MIDNIGHT SYNC] next sync in {seconds:.0f} seconds")

    def run():

        print("\n[MIDNIGHT SYNC] START\n")

        try:

            full_sync()

            reload_runtime_state()

            wakeup_scheduler()

            print("[MIDNIGHT SYNC] DONE\n")

        except Exception as e:

            print("[MIDNIGHT SYNC ERROR]", e)

        # schedule next midnight again
        schedule_midnight_sync()

    threading.Timer(seconds, run).start()


# ================= MAIN =================
def main():

    print("Start RPi Service")

    # ===== FIRST SYNC =====
    try:

        full_sync()

        wakeup_scheduler()

    except Exception as e: 

        print("? Sync failed:", e)
        print("? Running in OFFLINE MODE")

    # ===== LOAD LOCAL DATABASE =====
    try:
        load_runtime_state()
        print("STEP 1 OK")

        init_device_status()
        print("STEP 2 OK")

        state = get_runtime_state()
        print("STEP 3 OK")

        print_summary_table(state)
        print("STEP 4 OK")

        start_mqtt_listener()
        print("STEP 5 OK")

        scheduler_loop()
        print("STEP 6 OK")

        schedule_midnight_sync()
        print("STEP 7 OK")

        threading.Event().wait()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("? Failed to build runtime:", e)

if __name__ == "__main__":
    main()
