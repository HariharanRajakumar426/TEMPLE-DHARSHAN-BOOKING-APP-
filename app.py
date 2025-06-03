from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.secret_key = 'your-secret-key'

def init_db():
    conn = sqlite3.connect('darshan.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookings 
                 (id INTEGER PRIMARY KEY, user_id INTEGER, temple TEXT, date TEXT, slot TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS temples 
                 (id INTEGER PRIMARY KEY, name TEXT, location TEXT)''')
    
    # Insert sample temples if not exist
    c.execute("SELECT COUNT(*) FROM temples")
    if c.fetchone()[0] == 0:
        temples = [
            ('Sri Venkateswara Temple', 'Tirupati'),
            ('Meenakshi Temple', 'Madurai'),
            ('Ramanathaswamy Temple', 'Rameswaram')
        ]
        c.executemany("INSERT INTO temples (name, location) VALUES (?, ?)", temples)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        conn = sqlite3.connect('darshan.db')
        c = conn.cursor()
        c.execute("SELECT name, location FROM temples")
        temples = c.fetchall()
        conn.close()
        return render_template('index.html', temples=temples)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        name = request.form['name']
        
        conn = sqlite3.connect('darshan.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, name) VALUES (?, ?, ?)",
                     (username, password, name))
            conn.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists!')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = sqlite3.connect('darshan.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM users WHERE username = ? AND password = ?",
                 (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            flash('Login successful!')
            return redirect(url_for('index'))
        flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Logged out successfully!')
    return redirect(url_for('login'))

@app.route('/book', methods=['POST'])
def book():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    temple = request.form['temple']
    date = request.form['date']
    slot = request.form['slot']
    
    conn = sqlite3.connect('darshan.db')
    c = conn.cursor()
    
    # Check if slot is available
    c.execute("SELECT COUNT(*) FROM bookings WHERE temple = ? AND date = ? AND slot = ?",
             (temple, date, slot))
    if c.fetchone()[0] > 0:
        flash('This slot is already booked!')
    else:
        c.execute("INSERT INTO bookings (user_id, temple, date, slot) VALUES (?, ?, ?, ?)",
                 (session['user_id'], temple, date, slot))
        conn.commit()
        flash('Booking confirmed!')
    
    conn.close()
    return redirect(url_for('index'))

@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('darshan.db')
    c = conn.cursor()
    c.execute("SELECT temple, date, slot FROM bookings WHERE user_id = ?",
             (session['user_id'],))
    bookings = c.fetchall()
    conn.close()
    
    return render_template('bookings.html', bookings=bookings)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)