#build_runtime_memory.py
from core.db import fetch_all
from datetime import datetime


def build_runtime_memory():
    runtime = {
        "buildings": {},
        "clusters": {},
        "rooms": {},
        "nodes": {},
        "bookings": [],
        "booking_node_map": {},
        "node_state": {},
        "device_channels": {},
        "booking_led_channels": {}
    }

    print("== Build Runtime Memory ==")
    now = datetime.now()

    # 1. Load Building
    buildings = fetch_all("SELECT * FROM Building")
    for b in buildings:
        runtime["buildings"][b["building_id"]] = dict(b)

    # 2. Load Cluster
    clusters = fetch_all("SELECT * FROM Cluster")
    for c in clusters:
        runtime["clusters"][c["cluster_id"]] = dict(c)

    # 3. Building_detail
    building_details = fetch_all("SELECT * FROM Building_detail")
    for bd in building_details:
        building_id = bd["building_id"]
        cluster_id = bd["cluster_id"]

        runtime["buildings"][building_id].setdefault("clusters", {})
        runtime["buildings"][building_id]["clusters"][cluster_id] = runtime["clusters"][cluster_id]

    # 4. Load Room
    rooms = fetch_all("SELECT * FROM Room")
    for r in rooms:
        runtime["rooms"][r["room_id"]] = {
            "room_name": r["room_name"],
            "nodes": []
        }

    # 5. Cluster_detail
    cluster_details = fetch_all("SELECT * FROM Cluster_Detail")
    for cd in cluster_details:
        cluster_id = cd["cluster_id"]
        room_id = cd["room_id"]

        runtime["clusters"][cluster_id].setdefault("rooms", {})
        runtime["clusters"][cluster_id]["rooms"][room_id] = runtime["rooms"][room_id]


    # 6. Load Node
    nodes = fetch_all("""
        SELECT * FROM Node
        WHERE node_status = 'active'
    """)

    for n in nodes:
        runtime["nodes"][n["node_id"]] = {
            "node_id": n["node_id"],
            "node_type": n["node_type"],
            "computer_role": n.get("computer_role"),
            "node_info": dict(n),
            "config": {}
        }

        runtime["node_state"][n["node_id"]] = "OFF"

    # 7. Installation_Node
    installations = fetch_all("SELECT * FROM Installation_Node")
    for ins in installations:
        runtime["rooms"][ins["room_id"]]["nodes"].append(ins["node_id"])

    # 8. Load Config tables
    def load_config(table):
        rows = fetch_all(f"SELECT * FROM {table}")
        return {r["node_id"]: dict(r) for r in rows}

    config_led = load_config("config_led")
    config_computer = load_config("config_computer")
    config_air = load_config("config_air")
    config_projector = load_config("config_projector")
    config_audio = load_config("config_audio_equipment")
    config_door = load_config("config_door")

    for node_id, node in runtime["nodes"].items():
        t = node["node_type"]
        if t == "led":
            node["config"] = config_led.get(node_id, {})
        elif t == "computer":
            node["config"] = config_computer.get(node_id, {})
        elif t == "air_conditioner":
            node["config"] = config_air.get(node_id, {})
        elif t == "projector":
            node["config"] = config_projector.get(node_id, {})
        elif t == "audio_equipment":
            node["config"] = config_audio.get(node_id, {})
        elif t == "door":
            node["config"] = config_door.get(node_id, {})
            
    # 9. device_channel
    channels = fetch_all("SELECT * FROM device_channel")

    for ch in channels:
        node_id = ch["node_id"]

        runtime["device_channels"].setdefault(node_id, [])
        runtime["device_channels"][node_id].append({
            "channel_id": ch["id"],
            "device_type":ch["device_type"],
            "gpio": ch["gpio"],
            "name": ch["name"],
            "is_active": ch["is_active"]
        })
    # 10 Load Bookings (current + future)
    bookings = fetch_all("SELECT * FROM bookings")
    for b in bookings:
        if b["end_time"] < now:
            continue

        runtime["bookings"].append({
            "booking_id": b["booking_id"],
            "room_id": b["room_id"],
            "start_time": b["start_time"],
            "end_time": b["end_time"],
            "status": b["status"],
            "nodes": []
        })

    # 11 Booking node map
    maps = fetch_all("SELECT * FROM cluster_booking_node_map")
    for m in maps:
        runtime["booking_node_map"].setdefault(m["booking_id"], []).append(m["node_id"])

    for booking in runtime["bookings"]:
        booking["nodes"] = runtime["booking_node_map"].get(booking["booking_id"], [])

    print("== Runtime Memory Ready ==")
    
    # 12 booking_led_channel
    led_maps = fetch_all("SELECT * FROM booking_led_channel")

    for m in led_maps:
        runtime["booking_led_channels"].setdefault(m["booking_id"], {})
        runtime["booking_led_channels"][m["booking_id"]].setdefault(m["node_id"], [])
        runtime["booking_led_channels"][m["booking_id"]][m["node_id"]].append(m["channel_id"])
        
    return runtime



    
