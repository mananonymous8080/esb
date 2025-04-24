import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import os
from email_helper import send_booking_email 

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for flash and session

# Environment variables for DB config
DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_NAME = os.environ["DB_NAME"]
DB_PORT = int(os.environ["DB_PORT"])
ADMIN_LOGIN_PASSWORD = os.environ["ADMIN_LOGIN_PASSWORD"]

# Configure pymysql as MySQLdb
pymysql.install_as_MySQLdb()
import MySQLdb

# Helper function to get a fresh DB connection
def get_connection():
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        port=DB_PORT,
        ssl={"ssl": {}}  # Update with CA cert for TiDB if needed
    )

@app.route('/')
def index():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM predefined_slots")
    predefined_slots = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', predefined_slots=predefined_slots)

@app.route('/book', methods=['POST'])
def book_slot():
    name = request.form.get('name')
    mobile = request.form.get('mobile')
    email = request.form.get('email')
    exam_name = request.form.get('exam_name')
    exam_date = request.form.get('exam_date')
    exam_time = request.form.get('exam_time')

    conn = get_connection()
    cur = conn.cursor()
    query = "INSERT INTO slots (name, mobile, email, exam_name, exam_date, exam_time) VALUES (%s, %s, %s, %s, %s, %s)"
    cur.execute(query, (name, mobile, email, exam_name, exam_date, exam_time))
    conn.commit()
    cur.close()
    conn.close()

    # ✅ Send email after booking
    send_booking_email(name, email, mobile, exam_name, exam_date, exam_time)
    
    flash("Slot booked successfully! We will connect you shortly.")
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_LOGIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Incorrect admin password.")
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        flash("Access denied. Please log in as admin.")
        return redirect(url_for('admin_login'))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM slots")
    booked_slots = cur.fetchall()
    cur.execute("SELECT * FROM predefined_slots")
    predefined_slots = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', booked_slots=booked_slots, predefined_slots=predefined_slots)

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash("Logged out successfully.")
    return redirect(url_for('index'))

@app.route('/admin/add_predefined', methods=['POST'])
def add_predefined():
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('admin_login'))

    exam_name = request.form.get('exam_name')
    exam_date = request.form.get('exam_date')
    exam_time = request.form.get('exam_time')

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO predefined_slots (exam_name, exam_date, exam_time) VALUES (%s, %s, %s)",
                (exam_name, exam_date, exam_time))
    conn.commit()
    cur.close()
    conn.close()
    flash("Predefined slot added successfully.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_slot/<int:slot_id>')
def delete_slot(slot_id):
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('admin_login'))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM slots WHERE id = %s", (slot_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Booking deleted successfully.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_predefined/<int:slot_id>')
def delete_predefined(slot_id):
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('admin_login'))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM predefined_slots WHERE id = %s", (slot_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Predefined slot deleted successfully.")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
