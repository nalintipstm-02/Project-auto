import mysql.connector
from core.config import DB_CONFIG


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_all(sql, params=None):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    conn.close()
    return rows


def execute(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    conn.close()
