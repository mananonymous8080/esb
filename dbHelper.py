
import os
import pymysql
from dotenv import load_dotenv

load_dotenv(override=True)

# Environment variables
DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_NAME = os.environ["DB_NAME"]
DB_PORT = int(os.environ["DB_PORT"])

# Configure pymysql as MySQLdb
pymysql.install_as_MySQLdb()
import MySQLdb

def get_connection():
    conn = MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        port=DB_PORT,
        ssl={"ssl": {}}
    )
    ensure_tables_exist(conn)
    return conn

def ensure_tables_exist(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            mobile VARCHAR(10),
            email VARCHAR(255),
            service_type VARCHAR(255),
            service_name VARCHAR(255),
            description TEXT,
            service_date DATE,
            service_time TIME,
            payment_status VARCHAR(20),
            paid_amount DECIMAL(10, 2),
            status VARCHAR(50)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predefined_slots (
            id INT AUTO_INCREMENT PRIMARY KEY,
            service_type VARCHAR(255),
            service_name VARCHAR(255),
            description TEXT,
            service_date DATE,
            service_time TIME
        )
    """)
    conn.commit()
    cur.close()

def fetch_predefined_slots():
    conn = get_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("SELECT * FROM predefined_slots")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def fetch_booked_slots():
    conn = get_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("SELECT * FROM slots WHERE status IS NULL OR status = ''")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def fetch_slots_by_query(query):
    conn = get_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("""
        SELECT * FROM slots 
        WHERE mobile LIKE %s OR email LIKE %s
    """, (f"%{query}%", f"%{query}%"))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def insert_slot(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO slots 
        (name, mobile, email, service_type, service_name, description, service_date, service_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, tuple(data.values()))
    conn.commit()
    cur.close()
    conn.close()

def insert_predefined_slot(service_type, service_name, service_date, service_time, description):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predefined_slots (service_type, service_name, service_date, service_time, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (service_type, service_name, service_date, service_time, description))
    conn.commit()
    cur.close()
    conn.close()

def mark_slot_deleted(slot_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE slots SET status = 'deleted' WHERE id = %s", (slot_id,))
    conn.commit()
    cur.close()
    conn.close()

def delete_predefined_slot_by_id(slot_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM predefined_slots WHERE id = %s", (slot_id,))
    conn.commit()
    cur.close()
    conn.close()

def mark_slot_paid(slot_id, amount):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE slots SET payment_status = 'PAID', paid_amount = %s WHERE id = %s", (amount, slot_id))
    conn.commit()
    cur.close()
    conn.close()

def mark_slot_done(slot_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE slots SET status = 'completed' WHERE id = %s", (slot_id,))
    conn.commit()
    cur.close()
    conn.close()
