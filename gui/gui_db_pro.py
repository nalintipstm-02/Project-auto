#gui_db_pro.py
import mysql.connector
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "user": "user1",
    "password": "password1234",
    "database": "Project"
}



def query(sql, params=None):

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)

    cur.execute(sql, params or ())
    rows = cur.fetchall()

    conn.close()

    return rows


def query_one(sql, params=None):

    r = query(sql, params)

    if r:
        return r[0]

    return None

def query_all(sql, params=None):

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)

    cur.execute(sql, params or ())
    rows = cur.fetchall()

    conn.close()
    return rows
# ===============================
# ROOMS
# ===============================

def get_rooms():

    return query("""
        SELECT
            room_id id,
            room_name name
        FROM Room
        ORDER BY room_name
    """)


# ===============================
# BOOKINGS
# ===============================

def get_current_booking(room):

    now = datetime.now()

    return query_one("""
        SELECT start_time,end_time
        FROM bookings
        WHERE room_id=%s
        AND start_time<=%s
        AND end_time>=%s
        AND status='approved'
    """,(room,now,now))


def get_future_bookings(room_id):

    return query("""
        SELECT start_time,end_time,status
        FROM bookings
        WHERE room_id=%s
        AND DATE(start_time) >= CURDATE()
        ORDER BY start_time
    """,(room_id,))

def get_devices_by_room(room_id):

    return query("""
        SELECT
            n.node_id,
            n.node_name,
            n.node_type,
            n.computer_role
        FROM Node n
        JOIN Installation_Node i
        ON n.node_id = i.node_id
        WHERE i.room_id=%s
        AND n.node_status='active'
        ORDER BY n.node_id
    """,(room_id,))

def get_device_status(node_id, channel=0):

    r = query_one("""
        SELECT status
        FROM device_status
        WHERE node_id=%s
        AND channel=%s
    """,(node_id,channel))

    if r:
        return r["status"]

    return "off"
