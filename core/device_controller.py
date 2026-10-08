import time
import requests
import paho.mqtt.client as mqtt
import broadlink
import json
from datetime import datetime
from core.device_state import update_device_status


def now():
    return datetime.now()


def now_str():
    return now().strftime("%Y-%m-%d %H:%M:%S")


# =========================
# LOGGER
# =========================

def log_action(node_id, action, device_type, booking_id=None):

    t = now_str()

    if booking_id:
        print(f"[{t}] BOOKING {booking_id} | {device_type} Node {node_id} -> {action.upper()}")
    else:
        print(f"[{t}] MANUAL | {device_type} Node {node_id} -> {action.upper()}")


def log_info(msg):
    print(f"[{now_str()}] INFO | {msg}")


def log_error(device, node_id, err):
    print(f"[{now_str()}] ERROR | {device} Node {node_id} | {err}")



DELAY_COMPUTER_OFF = 0



WEB_URL = "http://192.168.1.100/NNN/B/update_status.php"


# =========================
# WEB STATUS
# =========================

def send_status_to_web(node_id, channel, status):

    try:

        data = {
            "node_id": node_id,
            "channel": channel,
            "status": status
        }

        response = requests.post(WEB_URL, data=data, timeout=5)

        log_info(f"WEB RESPONSE node:{node_id} channel:{channel} status:{status}")
        log_info(f"Status Code: {response.status_code}")
        log_info(f"Response: {response.text}")

    except Exception as e:
        log_error("WEB", node_id, e)


# =========================
# LED
# =========================

def led_auto(node_id, action, runtime, booking_id=None):

    node = runtime["nodes"].get(node_id)

    if not node:
        log_error("LED", node_id, "Node not found")
        return False

    config = node.get("config", {})

    broker = config.get("mqtt_broker")
    port = config.get("mqtt_port")

    command = config.get("command_led_on") if action == "on" else config.get("command_led_off")

    if not broker or not port or not command:
        log_error("LED", node_id, "Config incomplete")
        return False

    try:

        client = mqtt.Client()
        client.connect(broker, int(port), 60)
        client.publish(str(node_id), command)
        client.disconnect()

        log_action(node_id, action, "LED", booking_id)

        update_device_status(node_id, None, action)
        send_status_to_web(node_id, 0, action)

        return True

    except Exception as e:
        log_error("LED", node_id, e)
        return False

def led_bulk_auto(node_id, gpios, action, runtime, booking_id=None):

    node = runtime["nodes"].get(node_id)

    if not node:
        log_error("LED", node_id, "Node not found")
        return False

    config = node.get("config", {})

    broker = config.get("mqtt_broker")
    port = config.get("mqtt_port")

    device_channels = runtime.get("device_channels", {}).get(node_id, [])

    payload = json.dumps({
        "action": action,
        "gpios": [str(g) for g in gpios]
    })

    try:

        client = mqtt.Client()
        client.connect(broker, int(port), 60)
        client.publish(str(node_id), payload)
        client.disconnect()

        log_action(node_id, action, f"LED GPIO {gpios}", booking_id)

        for ch in device_channels:

            if ch["gpio"] in gpios:

                update_device_status(node_id, ch["channel_id"], action)
                send_status_to_web(node_id, ch["channel_id"], action)

        return True

    except Exception as e:
        log_error("LED BULK", node_id, e)
        return False


# =========================
# PROJECTOR
# =========================

def projector_auto(node_id, action, runtime, booking_id=None):

    node = runtime["nodes"].get(node_id)

    if not node:
        log_error("PROJECTOR", node_id, "Node not found")
        return False

    config = node.get("config", {})

    rm_ip = config.get("rm_pro_ip")
    rm_mac = config.get("rm_pro_mac")

    command = config.get("ir_command_pro_on") if action == "on" else config.get("ir_command_pro_off")

    if not rm_ip or not rm_mac or not command:
        log_error("PROJECTOR", node_id, "Config incomplete")
        return False

    try:
        device = broadlink.gendevice(
            0x2712,
            (rm_ip, 80),
            bytes.fromhex(rm_mac.replace(":", ""))
        )

        device.auth()
        device.send_data(bytes.fromhex(command))

        log_action(node_id, action, "PROJECTOR", booking_id)

        update_device_status(node_id, None, action)
        send_status_to_web(node_id, 0, action)

        return True

    except Exception as e:
        log_error("PROJECTOR", node_id, e)
        return False


# =========================
# AIR
# =========================

def air_auto(node_id, action, runtime, booking_id=None):

    node = runtime["nodes"].get(node_id)

    if not node:
        log_error("AIR", node_id, "Node not found")
        return False

    config = node.get("config", {})

    rm_ip = config.get("rm_air_ip")
    rm_mac = config.get("rm_air_mac")

    command = config.get("ir_command_air_on") if action == "on" else config.get("ir_command_air_off")

    if not rm_ip or not rm_mac or not command:
        log_error("AIR", node_id, "Config incomplete")
        return False

    try:

        device = broadlink.gendevice(
            0x2712,
            (rm_ip, 80),
            bytes.fromhex(rm_mac.replace(":", ""))
        )

        device.auth()
        device.send_data(bytes.fromhex(command))

        log_action(node_id, action, "AIR", booking_id)

        update_device_status(node_id, None, action)
        send_status_to_web(node_id, 0, action)

        return True

    except Exception as e:
        log_error("AIR", node_id, e)
        return False


# =========================
# AUDIO
# =========================

def audio_auto(node_id, action, runtime, booking_id=None):

    node = runtime["nodes"].get(node_id)

    if not node:
        log_error("AUDIO", node_id, "Node not found")
        return False

    config = node.get("config", {})

    broker = config.get("mqtt_broker")
    port = config.get("mqtt_port")

    command = config.get("command_audio_on") if action == "on" else config.get("command_audio_off")

    if not broker or not port or not command:
        log_error("AUDIO", node_id, "Config incomplete")
        return False

#    if action == "on":
#        log_info(f"AUDIO Node {node_id} waiting {DELAY_AUDIO_ON}s before ON")
#        time.sleep(DELAY_AUDIO_ON)

    try:

        client = mqtt.Client()
        client.connect(broker, int(port), 60)
        client.publish(str(node_id), command)
        client.disconnect()

        log_action(node_id, action, "AUDIO", booking_id)

        update_device_status(node_id, None, action)
        send_status_to_web(node_id, 0, action)

        return True

    except Exception as e:
        log_error("AUDIO", node_id, e)
        return False


# =========================
# COMPUTER ON
# =========================

def computer_open_auto(node_id, runtime, booking_id=None):

    node = runtime["nodes"].get(node_id)

    if not node:
        log_error("COMPUTER", node_id, "Node not found")
        return False

    config = node.get("config", {})

    broker = config.get("mqtt_broker")
    port = config.get("mqtt_port")
    command = config.get("command_com_on")

    if not broker or not port or not command:
        log_error("COMPUTER", node_id, "ON config incomplete")
        return False

    try:

        client = mqtt.Client()
        client.connect(broker, int(port), 60)
        client.publish(str(node_id), command)
        client.disconnect()

        log_action(node_id, "on", "COMPUTER", booking_id)

        update_device_status(node_id, None, "on")
        send_status_to_web(node_id, 0, "on")

        return True

    except Exception as e:
        log_error("COMPUTER", node_id, e)
        return False


# =========================
# COMPUTER OFF
# =========================

def computer_power_cut(node_id, runtime):

    node = runtime["nodes"].get(node_id)
    if not node:
        return False

    config = node.get("config", {})
    broker = config.get("mqtt_broker")
    port = config.get("mqtt_port")

    if not broker or not port:
        return False

    try:
        client = mqtt.Client()
        client.connect(broker, int(port), 60)
        client.publish(str(node_id), "off")
        client.disconnect()

        log_info(f"Relay power OFF for computer Node {node_id}")
        return True

    except Exception as e:
        log_error("COMPUTER POWER CUT", node_id, e)
        return False
        
        

def computer_off_auto(node_id, runtime, booking_id=None):

    node = runtime["nodes"].get(node_id)

    if not node:
        log_error("COMPUTER", node_id, "Node not found")
        return False

    config = node.get("config", {})

    ip = config.get("ip_address")
    port = config.get("port_off")
    command_http = config.get("command_com_off")

    broker = config.get("mqtt_broker")
    mqtt_port = config.get("mqtt_port")
    log_info(f"Node {node_id} config={config}")

    role = node.get("computer_role", "student")   # teacher / student
    log_info(f"Node {node_id} role={role}")

    if not ip or not port or not command_http:
        log_error("COMPUTER", node_id, "OFF config incomplete")
        return False

    url = f"http://{ip}:{port}/shutdown"
    data = {"command": command_http}

    http_success = False

    try:

        # =========================
        # DELAY BEFORE HTTP
        # =========================
        log_info(f"COMPUTER Node {node_id} waiting {DELAY_COMPUTER_OFF}s before HTTP OFF")
        time.sleep(DELAY_COMPUTER_OFF)

        # =========================
        # HTTP SHUTDOWN
        # =========================
        log_info(f"HTTP OFF Computer Node {node_id} -> {url}")

        response = requests.post(url, data=data, timeout=5)

        if response.status_code == 200:
            http_success = True
            log_action(node_id, "off", "COMPUTER", booking_id)

        else:
            log_error("COMPUTER", node_id, f"HTTP {response.status_code} {response.text}")

    except Exception as e:
        log_error("COMPUTER HTTP", node_id, e)

    # =========================
    # MQTT POWER CUT (teacher only)
    # =========================
    if role == "teacher" and broker and mqtt_port:

        try:

            remaining_delay = 55

            log_info(f"Waiting {remaining_delay}s before MQTT OFF Node {node_id}")
            time.sleep(remaining_delay)

            client = mqtt.Client()
            client.connect(broker, int(mqtt_port), 60)

            client.publish(str(node_id), command_http)

            client.disconnect()

            log_info(f"MQTT OFF sent to Node {node_id}")

        except Exception as e:
            log_error("COMPUTER MQTT-OFF", node_id, e)

    # =========================
    # UPDATE STATUS
    # =========================
    update_device_status(node_id, None, "off")
    send_status_to_web(node_id, 0, "off")

    return http_success


# =========================
# DOOR
# =========================

def door_auto(node_id, action, runtime, booking_id=None):

    node = runtime["nodes"].get(node_id)

    if not node:
        log_error("DOOR", node_id, "Node not found")
        return False

    config = node.get("config", {})

    broker = config.get("mqtt_broker")
    port = config.get("mqtt_port")

    command = config.get("command_door_open") if action in ["on", "open"] else config.get("command_door_close")

    if not broker or not port or not command:
        log_error("DOOR", node_id, "Config incomplete")
        return False

    try:

        client = mqtt.Client()
        client.connect(broker, int(port), 60)
        client.publish(str(node_id), command)
        client.disconnect()

        log_action(node_id, action, "DOOR", booking_id)

        if action in ["open", "on"]:
            update_device_status(node_id, None, "on")
            send_status_to_web(node_id, 0, "on")
        else:
            update_device_status(node_id, None, "off")
            send_status_to_web(node_id, 0, "off")

        return True

    except Exception as e:
        log_error("DOOR", node_id, e)
        return False


# =========================
# GENERIC CONTROL
# =========================

def control_device(node_id, action, runtime, booking_id=None):

    node = runtime["nodes"].get(node_id)

    if not node:
        log_error("CONTROL", node_id, "Node not found")
        return False

    node_type = node.get("node_type")

    if node_type == "projector":
        return projector_auto(node_id, action, runtime, booking_id)

    elif node_type == "air_conditioner":
        return air_auto(node_id, action, runtime, booking_id)

    elif node_type == "audio_equipment":
        return audio_auto(node_id, action, runtime, booking_id)

    elif node_type == "computer":
        if action == "on":
            return computer_open_auto(node_id, runtime, booking_id)
        else:
            return computer_off_auto(node_id, runtime, booking_id)

    elif node_type == "door":
        return door_auto(node_id, action, runtime, booking_id)

    elif node_type == "led":
        return led_auto(node_id, action, runtime, booking_id)

    else:
        log_error("CONTROL", node_id, f"Unknown device type: {node_type}")
        return False
