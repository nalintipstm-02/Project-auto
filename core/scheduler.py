#scheduler.py
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor

from core.runtime_state import get_runtime_state
import core.device_controller as dc
from gui.gui_db_pro import get_device_status

# ================= CONFIG =================
COMMAND_COOLDOWN = 5
DELAY_OFF_MINUTES = 0

# ================= STATE =================
active_bookings = set()
last_command_time = {}
pending_room_off = {}   # room_id -> off_time
current_device_state = {}
active_booking_rooms = {}


scheduler_timer = None
scheduler_lock = threading.Lock()

executor = ThreadPoolExecutor(max_workers=20)

# ================= TIME =================
def parse_time(t):
    if isinstance(t, datetime):
        return t
    return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")

def now():
    return datetime.now()

def now_str():
    return now().strftime("%Y-%m-%d %H:%M:%S")


    
# ================= COOLDOWN =================
def can_send(node_id, action):
    key = (node_id, action)
    t = last_command_time.get(key)
    if not t:
        return True
    return (now() - t).total_seconds() >= COMMAND_COOLDOWN


def mark_sent(node_id, action):
    last_command_time[(node_id, action)] = now()

# ================= DEVICE CONTROL =================
def send_on(node_id, booking_id, runtime):

    if not can_send(node_id, "on"):
        return

    node = runtime["nodes"].get(node_id)
    if not node:
        return

    log_device(node_id, node["node_type"], "ON", booking_id)

    try:

        t = node["node_type"]

        if t == "led":
            handle_led(node_id, booking_id, "on", runtime)

        elif t == "projector":
            dc.projector_auto(node_id, "on", runtime, booking_id)

        elif t == "air_conditioner":
            dc.air_auto(node_id, "on", runtime, booking_id)

        elif t == "audio_equipment":
            dc.audio_auto(node_id, "on", runtime, booking_id)

        elif t == "computer":

            role = node.get("computer_role")

            if role == "student":
                return

            dc.computer_open_auto(node_id, runtime, booking_id)

        elif t == "door":
            dc.door_auto(node_id, "open", runtime, booking_id)

        mark_sent(node_id, "on")

    except Exception as e:
        print(f"[AUTO ERROR ON] node {node_id} : {e}")
        
def send_off(node_id, booking_id, runtime):

    if not can_send(node_id, "off"):
        return

    node = runtime["nodes"].get(node_id)
    if not node:
        return

    log_device(node_id, node["node_type"], "OFF", booking_id)

    try:

        t = node["node_type"]

        if t == "led":
            handle_led(node_id, booking_id, "off", runtime)

        elif t == "projector":
            dc.projector_auto(node_id, "off", runtime, booking_id)

        elif t == "air_conditioner":
            dc.air_auto(node_id, "off", runtime, booking_id)

        elif t == "audio_equipment":
            dc.audio_auto(node_id, "off", runtime, booking_id)

        elif t == "computer":
            dc.computer_off_auto(node_id, runtime, booking_id)

        elif t == "door":
            dc.door_auto(node_id, "close", runtime, booking_id)

        mark_sent(node_id, "off")

    except Exception as e:
        print(f"[AUTO ERROR OFF] node {node_id} : {e}")


def handle_led(node_id, booking_id, action, runtime):

    node = runtime["nodes"].get(node_id)
    if not node:
        return

    all_channels = runtime.get("device_channels", {}).get(node_id, [])

    if not all_channels:
        dc.led_auto(node_id, action, runtime, booking_id)
        return

    all_gpios = [
        ch["gpio"]
        for ch in all_channels
        if ch.get("is_active")
    ]

    if not all_gpios:
        return

    selected_channel_ids = []

    if booking_id:
        selected_channel_ids = (
            runtime
            .get("booking_led_channels", {})
            .get(booking_id, {})
            .get(node_id, [])
        )

    if not selected_channel_ids:

        dc.led_bulk_auto(node_id, all_gpios, action, runtime, booking_id)
        return

    selected_gpios = [
        ch["gpio"]
        for ch in all_channels
        if ch["channel_id"] in selected_channel_ids
        and ch.get("is_active")
    ]

    unselected_gpios = list(set(all_gpios) - set(selected_gpios))

    if action == "on":

        if selected_gpios:
            dc.led_bulk_auto(node_id, selected_gpios, "on", runtime, booking_id)

        if unselected_gpios:
            dc.led_bulk_auto(node_id, unselected_gpios, "off", runtime, booking_id)

    else:
        dc.led_bulk_auto(node_id, all_gpios, "off", runtime, booking_id)

def compute_booking_state(runtime, booking):

    room = runtime["rooms"][booking["room_id"]]
    result = {}

    for node_id in room["nodes"]:

        node = runtime["nodes"].get(node_id)
        if not node:
            continue

        node_type = node["node_type"]

        # ---------- LED ----------
        if node_type == "led":

            channels = runtime.get("device_channels", {}).get(node_id, [])

            # ---------- LED MULTI ----------
            if channels:

                selected = (
                    runtime
                    .get("booking_led_channels", {})
                    .get(booking["booking_id"], {})
                    .get(node_id, [])
                )

                result[node_id] = {
                    "type": "led_multi",
                    "channels": set(selected)
                }

            # ---------- LED SINGLE ----------
            else:

                if node_id in booking.get("nodes", []):
                    result[node_id] = {
                        "type": "led_single"
                    }

        # ---------- NORMAL ----------
        else:

            if node_id in booking.get("nodes", []):
                result[node_id] = {
                    "type": "normal"
                }

    return result



def get_actual_room_state(runtime, room_id):

    state = {}

    room = runtime["rooms"].get(room_id)
    if not room:
        return state

    for node_id in room.get("nodes", []):

        node = runtime["nodes"].get(node_id)
        if not node:
            continue

        node_type = node["node_type"]

        # ---------- LED ----------
        if node_type == "led":

            channels = runtime.get("device_channels", {}).get(node_id, [])

            # MULTI CHANNEL LED
            if channels:

                on_channels = []

                for ch in channels:

                    status = get_device_status(node_id, ch["channel_id"])

                    if status == "on":
                        on_channels.append(ch["channel_id"])

                if on_channels:
                    state[node_id] = {
                        "type": "led_multi",
                        "channels": set(on_channels)
                    }

            # SINGLE LED
            else:

                status = get_device_status(node_id, 0)

                if status == "on":
                    state[node_id] = {"type": "led_single"}

        # ---------- NORMAL DEVICE ----------
        else:

            status = get_device_status(node_id, 0)

            if status == "on":
                state[node_id] = {"type": "normal"}

    return state
    
    
def apply_state_diff(runtime, old_state, new_state, booking_id):

    nodes = set(old_state.keys()) | set(new_state.keys())

    for node_id in nodes:

        node = runtime["nodes"].get(node_id)
        if not node:
            continue

        node_type = node["node_type"]

        old = old_state.get(node_id)
        new = new_state.get(node_id)

        # ---------- LED ----------
        if node_type == "led":

            # ---------------- LED MULTI ----------------
            if new and new.get("type") == "led_multi":

                old_ch = set(old["channels"]) if old else set()
                new_ch = set(new["channels"])

                turn_on = new_ch - old_ch
                turn_off = old_ch - new_ch

                channels = runtime.get("device_channels", {}).get(node_id, [])

                def to_gpio(channel_ids):
                    return [
                        ch["gpio"]
                        for ch in channels
                        if ch["channel_id"] in channel_ids and ch.get("is_active")
                    ]

                on_gpios = to_gpio(turn_on)
                off_gpios = to_gpio(turn_off)

                if on_gpios:
                    executor.submit(dc.led_bulk_auto, node_id, on_gpios, "on", runtime, booking_id)

                if off_gpios:
                    executor.submit(dc.led_bulk_auto, node_id, off_gpios, "off", runtime, booking_id)

            # ---------------- LED SINGLE ----------------
            elif new and new.get("type") == "led_single" and not old:

                executor.submit(send_on, node_id, booking_id, runtime)

            elif old and not new:

                channels = runtime.get("device_channels", {}).get(node_id, [])

                all_gpios = [
                    ch["gpio"]
                    for ch in channels
                    if ch.get("is_active")
                ]

                if all_gpios:
                    executor.submit(dc.led_bulk_auto, node_id, all_gpios, "off", runtime, booking_id)
                else:
                    executor.submit(send_off, node_id, booking_id, runtime)


        # ---------- NORMAL ----------
        else:

            if old and not new:
                executor.submit(send_off, node_id, booking_id, runtime)

            elif new and not old:

                node = runtime["nodes"].get(node_id)

                if node and node["node_type"] == "computer":

                    role = node.get("computer_role")

                    if role == "student":
                        continue

                executor.submit(send_on, node_id, booking_id, runtime)

def turn_off_current_devices(runtime, room_id):

    global current_device_state

    room_state = current_device_state.get(room_id, {})

    for node_id, info in room_state.items():

        node = runtime["nodes"].get(node_id)
        if not node:
            continue

        node_type = node["node_type"]

        # ---------- LED ----------
        if node_type == "led":

            channels = runtime.get("device_channels", {}).get(node_id, [])

            # ---------- LED MULTI ----------
            if channels:

                gpios = [
                    ch["gpio"]
                    for ch in channels
                    if ch["channel_id"] in info.get("channels", [])
                    and ch.get("is_active")
                ]

                if gpios:
                    executor.submit(
                        dc.led_bulk_auto,
                        node_id,
                        gpios,
                        "off",
                        runtime
                    )

            # ---------- LED SINGLE ----------
            else:

                executor.submit(
                    send_off,
                    node_id,
                    None,
                    runtime
                )

        # ---------- NORMAL DEVICES ----------
        else:

            executor.submit(
                send_off,
                node_id,
                None,
                runtime
            )

    current_device_state[room_id] = {}

def turn_off_all_devices_in_room(runtime, room_id):

    room = runtime["rooms"].get(room_id)

    if not room:
        return

    for node_id in room.get("nodes", []):

        node = runtime["nodes"].get(node_id)

        if not node:
            continue

        node_type = node["node_type"]

        # ---------- LED ----------
        if node_type == "led":

            channels = runtime.get("device_channels", {}).get(node_id, [])

            # LED multi
            if channels:

                gpios = [
                    ch["gpio"]
                    for ch in channels
                    if ch.get("is_active")
                ]

                if gpios:
                    executor.submit(
                        dc.led_bulk_auto,
                        node_id,
                        gpios,
                        "off",
                        runtime
                    )

            # LED single
            else:

                executor.submit(
                    send_off,
                    node_id,
                    None,
                    runtime
                )

        # ---------- NORMAL ----------
        else:

            executor.submit(
                send_off,
                node_id,
                None,
                runtime
            )

    # clear state
    current_device_state[room_id] = {}


def print_summary_table(runtime):

    now_dt = now()
    print("\nSUMMARY CONTROL TABLE (Current & Future Bookings)\n")

    future_bookings = [
        b for b in runtime["bookings"]
        if b.get("status") == "approved"
        and parse_time(b["end_time"]) >= now_dt
    ]

    if not future_bookings:
        print("No current or future bookings\n")
        return

    for booking in future_bookings:

        room_id = booking["room_id"]
        room = runtime["rooms"].get(room_id)

        if not room:
            continue

        room_name = room["room_name"]
        start = parse_time(booking["start_time"])
        end = parse_time(booking["end_time"])

        print(f"=== Booking {booking['booking_id']} (Room {room_id} : {room_name}) ===")
        print(f"Time: {start}  ->  {end}")
        print("Node        | Action | Reason                  | Time")
        print("-" * 70)

        room_nodes = room.get("nodes", [])
        booking_nodes = set(booking.get("nodes", []))

        for node_id in room_nodes:

            node = runtime["nodes"].get(node_id)
            if not node:
                continue

            node_type = node.get("node_type")

            # =================================================
            # LED NODE
            # =================================================
            if node_type == "led":

                all_channels = runtime.get("device_channels", {}).get(node_id, [])

                # -------- LED SINGLE (????? channel) --------
                if not all_channels:

                    if node_id in booking_nodes:
                        action = "ON"
                        reason = "selected in booking"
                    else:
                        action = "OFF"
                        reason = "not selected in booking"

                    print(
                        f"{node_id:<12} | "
                        f"{action:<6} | "
                        f"{reason:<23} | "
                        f"{start.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                    continue

                # -------- LED MULTI CHANNEL --------
                selected_channels = (
                    runtime
                    .get("booking_led_channels", {})
                    .get(booking["booking_id"], {})
                    .get(node_id, [])
                )

                selected_channels = set(selected_channels)

                for ch in all_channels:

                    if not ch.get("is_active"):
                        continue

                    ch_id = ch["channel_id"]

                    if node_id in booking_nodes and ch_id in selected_channels:
                        action = "ON"
                        reason = "selected in booking"
                    else:
                        action = "OFF"
                        reason = "not selected in booking"

                    print(
                        f"{f'{node_id} CH{ch_id}':<12} | "
                        f"{action:<6} | "
                        f"{reason:<23} | "
                        f"{start.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                continue

            # =================================================
            # NORMAL DEVICE
            # =================================================
            if node_id in booking_nodes:
                action = "ON"
                reason = "selected in booking"
            else:
                action = "OFF"
                reason = "not selected in booking"

            print(
                f"{node_id:<12} | "
                f"{action:<6} | "
                f"{reason:<23} | "
                f"{start.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        print()
        
def log_device(node_id, name=None, action=None, booking_id=None):

    t = now().strftime("%H:%M:%S")

    name = name or "SYSTEM"
    action = action or ""

    if booking_id:
        print(f"[{t}] Booking {booking_id} | {name:<15} Node {node_id:<2} -> {action}")
    else:
        print(f"[{t}] {name:<15} Node {node_id:<2} -> {action}")
    
# ================= HELPERS =================
def is_last_booking_of_day(bookings, current_booking):
    room_id = current_booking["room_id"]
    booking_date = parse_time(current_booking["start_time"]).date()

    for b in bookings:
        if b["room_id"] != room_id:
            continue

        b_date = parse_time(b["start_time"]).date()
        if b_date != booking_date:
            continue

        if parse_time(b["start_time"]) > parse_time(current_booking["end_time"]):
            return False

    return True

def get_next_booking_immediately(bookings, current_booking):
    room_id = current_booking["room_id"]
    end_time = parse_time(current_booking["end_time"])

    for b in bookings:
        if b["room_id"] != room_id:
            continue

        if parse_time(b["start_time"]) == end_time:
            return b

    return None
# ================= SCHEDULER =================

def scheduler_loop():

    global scheduler_timer
    global current_device_state

    with scheduler_lock:

        try:

            runtime = get_runtime_state()

            if not runtime:
                schedule_next(30)
                return

            base_time = now()

            approved_bookings = [
                b for b in runtime["bookings"]
                if b.get("status") == "approved"
            ]

            bookings = sorted(
                approved_bookings,
                key=lambda b: parse_time(b["start_time"])
            )

            # ==================================================
            # EXIT BOOKINGS
            # ==================================================

            for bid in list(active_bookings):

                b = next((x for x in bookings if x["booking_id"] == bid), None)

                if not b:

                    rid = active_booking_rooms.get(bid)

                    if rid:

                        room = runtime["rooms"].get(rid)
                        room_name = room["room_name"] if room else rid

                        log_device(
                            f"[{now_str()}] CANCEL Booking {bid} (Room {room_name})"
                        )

                        turn_off_current_devices(runtime, rid)

                        current_device_state[rid] = {}

                    active_bookings.remove(bid)
                    active_booking_rooms.pop(bid, None)

                    continue

                end = parse_time(b["end_time"])

                if base_time >= end:

                    rid = b["room_id"]
                    room = runtime["rooms"][rid]
                    room_name = room["room_name"]

                    log_device(f"\n[{now_str()}] EXIT Booking {bid} (Room {room_name})")

                    next_booking = get_next_booking_immediately(bookings, b)

                    # ---------------- CONTINUE BOOKING ----------------

                    if next_booking:

                        log_device(
                            f"[{now_str()}] CONTINUE to Booking {next_booking['booking_id']}"
                        )

                        new_state = compute_booking_state(runtime, next_booking)

                        old_state = current_device_state.get(rid, {})

                        apply_state_diff(
                            runtime,
                            old_state,
                            new_state,
                            next_booking["booking_id"]
                        )

                        current_device_state[rid] = new_state

                    # ---------------- LAST BOOKING OF DAY ----------------

                    elif is_last_booking_of_day(bookings, b):

                        off_time = end + timedelta(minutes=DELAY_OFF_MINUTES)

                        pending_room_off[rid] = off_time

                        log_device(
                            f"[{now_str()}] Room {room_name} delay off scheduled at "
                            f"{off_time.strftime('%H:%M:%S')}"
                        )

                    # ---------------- NORMAL EXIT ----------------

                    else:

                        log_device(
                            f"[{now_str()}] Normal exit -> turning OFF devices in room {room_name}"
                        )

                        turn_off_current_devices(runtime, rid)

                    active_bookings.remove(bid)

            # ==================================================
            # ENTER BOOKINGS
            # ==================================================

            for b in bookings:

                bid = b["booking_id"]

                start = parse_time(b["start_time"])
                end = parse_time(b["end_time"])

                if start <= base_time < end and bid not in active_bookings:

                    room = runtime["rooms"][b["room_id"]]
                    room_name = room["room_name"]

                    log_device(
                        f"\n[{now_str()}] ENTER Booking {bid} (Room {room_name})"
                    )

                    new_state = compute_booking_state(runtime, b)

                    rid = b["room_id"]

                    old_state = current_device_state.get(rid)

                    if not old_state:
                        old_state = get_actual_room_state(runtime, rid)

                    apply_state_diff(
                        runtime,
                        old_state,
                        new_state,
                        bid
                    )

                    current_device_state[rid] = new_state

                    active_bookings.add(bid)
                    active_booking_rooms[bid] = rid

                    pending_room_off.pop(rid, None)

            # ==================================================
            # DELAY OFF
            # ==================================================

            for rid, off_time in list(pending_room_off.items()):

                if base_time >= off_time:

                    room = runtime["rooms"][rid]
                    room_name = room["room_name"]

                    log_device(
                        f"\n[{now_str()}] DELAY OFF Room {room_name} (ALL DEVICES)"
                    )

                    turn_off_all_devices_in_room(runtime, rid)

                    del pending_room_off[rid]

            # ==================================================
            # NEXT EVENT
            # ==================================================

            next_times = []

            for b in bookings:

                start = parse_time(b["start_time"])
                end = parse_time(b["end_time"])

                if start > base_time:
                    next_times.append(start)

                if end > base_time:
                    next_times.append(end)

            for off_time in pending_room_off.values():

                if off_time > base_time:
                    next_times.append(off_time)

            if next_times:

                next_time = min(next_times)

                sleep_seconds = (
                    next_time - base_time
                ).total_seconds()

                sleep_seconds = max(1, sleep_seconds)

            else:

                sleep_seconds = 3600

            log_device(f"[{now_str()}] Scheduler sleeping {sleep_seconds:.1f}s")

            schedule_next(sleep_seconds)

        except Exception as e:

            print(f"\n[{now_str()}] SCHEDULER ERROR\n", e)

            schedule_next(30)

# ================= TIMER =================
def schedule_next(seconds):
    global scheduler_timer

    if scheduler_timer:
        scheduler_timer.cancel()

    scheduler_timer = threading.Timer(seconds, scheduler_loop)
    scheduler_timer.daemon = True
    scheduler_timer.start()

# ================= WAKEUP =================
def wakeup_scheduler():
    global scheduler_timer
    print("\n[Scheduler] Wakeup called\n")

    if scheduler_timer:
        scheduler_timer.cancel()

    scheduler_loop()

# ================= START =================
def start_scheduler():
    print("\n[Scheduler] Clean scheduler started\n")
    scheduler_loop()
