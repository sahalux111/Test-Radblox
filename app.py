
from flask import Flask, render_template, request, redirect, url_for, session
from db_config import get_db_connection
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Adjust time to IST
IST_OFFSET = timedelta(hours=5, minutes=30)

def convert_to_ist(utc_time):
    return utc_time + IST_OFFSET

# Background thread to ping app every 15 seconds (for Render)
def ping_app():
    while True:
        with app.test_request_context('/'):
            pass
        time.sleep(15)

threading.Thread(target=ping_app).start()

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials'

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_role = session['role']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if user_role == 'admin':
        cursor.execute("SELECT * FROM users WHERE role = 'doctor'")
        doctors = cursor.fetchall()
        return render_template('admin_control.html', doctors=doctors)

    elif user_role == 'qa':
        cursor.execute("SELECT * FROM availability WHERE role = 'doctor'")
        doctors_availability = cursor.fetchall()
        return render_template('qa_dashboard.html', doctors=doctors_availability)

    elif user_role == 'doctor':
        user_id = session['user_id']
        cursor.execute("SELECT * FROM availability WHERE user_id = %s AND role = 'doctor'", (user_id,))
        availability = cursor.fetchall()
        cursor.execute("SELECT * FROM breaks WHERE doctor_id = %s", (user_id,))
        breaks = cursor.fetchall()
        return render_template('doctor_dashboard.html', availability=availability, breaks=breaks)

    conn.close()
    return 'Unauthorized access'

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/set_availability', methods=['POST'])
def set_availability():
    user_id = session['user_id']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    role = session['role']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO availability (user_id, start_time, end_time, role) VALUES (%s, %s, %s, %s)",
        (user_id, start_time, end_time, role)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

@app.route('/set_break', methods=['POST'])
def set_break():
    if session['role'] != 'admin':
        return 'Unauthorized access'

    doctor_id = request.form['doctor_id']
    start_time = request.form['start_time']
    end_time = request.form['end_time']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO breaks (doctor_id, start_time, end_time) VALUES (%s, %s, %s)",
        (doctor_id, start_time, end_time)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
