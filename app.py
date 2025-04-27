import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, session
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
UPI_ID = os.environ["UPI_ID"]

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
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("SELECT * FROM predefined_slots")
    predefined_slots = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', predefined_slots=predefined_slots)



@app.route('/book', methods=['POST'])
def book_slot():
    # Collect all fields cleanly
    data = {
        'name': request.form.get('name'),
        'mobile': request.form.get('mobile'),
        'email': request.form.get('email'),
        'service_type': request.form.get('service_type'),
        'service_name': request.form.get('service_name'),
        'description': request.form.get('description') or '',
        'service_date': request.form.get('service_date') or None,
        'service_time': request.form.get('service_time') or None
    }

    # Database insert
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
        INSERT INTO slots 
        (name, mobile, email, service_type, service_name, description, service_date, service_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cur.execute(query, tuple(data.values()))
    
    conn.commit()
    cur.close()
    conn.close()

    # ✅ Send email after booking
    send_booking_email(
        name=data['name'],
        email=data['email'],
        mobile=data['mobile'],
        service_type=data['service_type'],
        service_name=data['service_name'],
        service_date=data['service_date'],
        service_time=data['service_time'],
        description=data['description']
    )
    
    flash("Slot registered successfully! 🚀 Please complete payment for confirmation. We'll contact you soon.")
    return redirect(url_for('search_slots', query=data['mobile'] or data['email']))




@app.route('/search', methods=['GET'])
def search_slots():
    query = request.args.get('query')
    conn = get_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    cur.execute("""
        SELECT * FROM slots 
        WHERE mobile LIKE %s OR email LIKE %s
    """, (f"%{query}%", f"%{query}%"))

    results = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('search_results.html', results=results, query=query, upi_id=UPI_ID)





@app.route('/health')
def health_check():
    return 'OK', 200


################# ADMIN ##################



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
    cur = conn.cursor(pymysql.cursors.DictCursor)  
    cur.execute("SELECT * FROM slots WHERE status IS NULL OR status = ''")
    booked_slots = cur.fetchall()
    cur.execute("SELECT * FROM predefined_slots")
    predefined_slots = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', booked_slots=booked_slots, predefined_slots=predefined_slots)



@app.route('/admin/add_predefined', methods=['POST'])
def add_predefined():
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('admin_login'))

    service_type = request.form.get('service_type')
    service_name = request.form.get('service_name')
    service_date = request.form.get('service_date') or None
    service_time = request.form.get('service_time') or None
    description = request.form.get('description') or None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predefined_slots (service_type, service_name, service_date, service_time, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (service_type, service_name, service_date, service_time, description))
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
    # Instead of DELETE, we UPDATE the status
    cur.execute("UPDATE slots SET status = 'deleted' WHERE id = %s", (slot_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Slot marked as deleted successfully.")
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


@app.route('/mark_as_paid', methods=['POST'])
def mark_as_paid():
    slot_id = request.form.get('slot_id')
    payment_amount = request.form.get('payment_amount')
    print(slot_id, payment_amount)
    if slot_id and payment_amount:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE slots SET payment_status = 'PAID', paid_amount = %s WHERE id = %s", (payment_amount, slot_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Payment status updated successfully.")
    else:
        flash("Failed to update payment status.")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/mark_as_done', methods=['POST'])
def mark_as_done():
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('admin_login'))

    slot_id = request.form.get('slot_id')

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE slots SET status = %s WHERE id = %s", ('completed', slot_id))
    conn.commit()
    cur.close()
    conn.close()
    flash("Slot marked as done and moved to Completed  successfully.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash("Logged out successfully.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
