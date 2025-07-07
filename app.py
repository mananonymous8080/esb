from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from email_helper import send_booking_email 
import random
import re
import os
from dotenv import load_dotenv
from dbHelper import get_connection, fetch_slots_by_query, insert_slot, fetch_predefined_slots, fetch_booked_slots, insert_predefined_slot, mark_slot_deleted, delete_predefined_slot_by_id, mark_slot_paid, mark_slot_done

load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

ADMIN_LOGIN_PASSWORD = os.environ["ADMIN_LOGIN_PASSWORD"]
UPI_ID = os.environ["UPI_ID"]

@app.route('/')
def index():
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    expected_sum = num1 + num2
    return render_template('index.html', num1=num1, num2=num2, expected_sum=expected_sum)

@app.route('/load_predefined_slots')
def load_predefined_slots():
    predefined_slots = fetch_predefined_slots()
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    expected_sum = num1 + num2
    return render_template('components/predefined_slots_container.html',
                           predefined_slots=predefined_slots,
                           num1=num1, num2=num2, expected_sum=expected_sum)

@app.route('/book_slot', methods=['POST'])
def book_slot():
    if request.form.get("website"):
        print(f"[BOT BLOCKED - Honeypot] | IP: {request.remote_addr}")
        return redirect(request.referrer)

    user_agent = request.headers.get('User-Agent', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if "python" in user_agent.lower() or "curl" in user_agent.lower():
        print(f"[BLOCKED] | IP: {ip} | User-Agent: {user_agent}")
        return "Denied", 403

    user_answer = request.form.get("captcha_answer")
    expected_sum = request.form.get("captcha_sum")
    try:
        if int(user_answer) != int(expected_sum):
            flash("Incorrect CAPTCHA.", "danger")
            return redirect(request.referrer)
    except:
        flash("Invalid CAPTCHA input.", "danger")
        return redirect(request.referrer)

    mobile = request.form.get('mobile', '')
    email = request.form.get('email', '')
    name = request.form.get('name', '')

    if not re.match(r"^\d{10}$", mobile):
        flash("Invalid mobile number", "danger")
        return redirect(request.referrer)
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash("Invalid email address", "danger")
        return redirect(request.referrer)
    if not name.strip():
        flash("Name is required", "danger")
        return redirect(request.referrer)

    data = {
        'name': name.strip(),
        'mobile': mobile,
        'email': email,
        'service_type': request.form.get('service_type'),
        'service_name': request.form.get('service_name'),
        'description': request.form.get('description') or '',
        'service_date': request.form.get('service_date') or None,
        'service_time': request.form.get('service_time') or None
    }

    insert_slot(data)

    send_booking_email(**data)
    flash("Slot registered successfully! Please complete payment for confirmation.")
    return redirect(url_for('search_slots', query=data['mobile'] or data['email']))

@app.route('/search', methods=['GET'])
def search_slots():
    query = request.args.get('query')
    results = fetch_slots_by_query(query)
    return render_template('search_results.html', results=results, query=query, upi_id=UPI_ID)

@app.route('/health')
def health_check():
    return 'OK', 200

############ ADMIN ROUTES ############

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
        flash("Access denied.")
        return redirect(url_for('admin_login'))
    return render_template('admin.html')

@app.route('/admin/load_data')
def load_admin_data():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    predefined_html = render_template('admin_partials/predefined_cards.html',
                                      predefined_slots=fetch_predefined_slots())
    booked_html = render_template('admin_partials/booked_cards.html',
                                  booked_slots=fetch_booked_slots())
    return jsonify({
        'predefined_html': predefined_html,
        'booked_html': booked_html
    })

@app.route('/admin/add_predefined', methods=['POST'])
def add_predefined():
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('admin_login'))
    insert_predefined_slot(request.form.get('service_type'), request.form.get('service_name'), request.form.get('service_date') or None, request.form.get('service_time') or None, request.form.get('description') or None)
    flash("Predefined slot added successfully.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_slot/<int:slot_id>')
def delete_slot(slot_id):
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('admin_login'))
    mark_slot_deleted(slot_id)
    flash("Slot marked as deleted.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_predefined/<int:slot_id>')
def delete_predefined(slot_id):
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('admin_login'))
    delete_predefined_slot_by_id(slot_id)
    flash("Predefined slot deleted.")
    return redirect(url_for('admin_dashboard'))

@app.route('/mark_as_paid', methods=['POST'])
def mark_as_paid():
    slot_id = request.form.get('slot_id')
    payment_amount = request.form.get('payment_amount')
    if slot_id and payment_amount:
        mark_slot_paid(slot_id, payment_amount)
        flash("Payment marked as PAID.")
    else:
        flash("Failed to update payment status.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/mark_as_done', methods=['POST'])
def mark_as_done():
    if not session.get('is_admin'):
        flash("Access denied.")
        return redirect(url_for('admin_login'))

    slot_id = request.form.get('slot_id')
    mark_slot_done(slot_id)
    flash("Slot marked as completed.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash("Logged out successfully.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
