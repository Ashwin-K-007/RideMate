import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_NAME = "ridemate.db"

def init_db():
    """Initializes the SQLite database and seeds initial data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            vehicle_model TEXT NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            ride_time TEXT NOT NULL,
            seats_available INTEGER NOT NULL,
            price_per_seat INTEGER NOT NULL
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM rides")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO rides (driver_name, phone, vehicle_type, vehicle_model, origin, destination, ride_time, seats_available, price_per_seat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',)
    
    conn.commit()s
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/rides', methods=['GET'])
def get_rides():
    origin_query = request.args.get('origin', '').lower()
    dest_query = request.args.get('dest', '').lower()
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM rides WHERE seats_available > 0"
    params = []
    
    if origin_query:
        query += " AND LOWER(origin) LIKE ?"
        params.append(f"%{origin_query}%")
    if dest_query:
        query += " AND LOWER(destination) LIKE ?"
        params.append(f"%{dest_query}%")
        
    query += " ORDER BY id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    rides = [dict(row) for row in rows]
    conn.close()
    
    return jsonify(rides)

@app.route('/api/rides', methods=['POST'])
def create_ride():
    data = request.json
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO rides (driver_name, phone, vehicle_type, vehicle_model, origin, destination, ride_time, seats_available, price_per_seat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['driver_name'],
            data['phone'],
            data['vehicle_type'],
            data['vehicle_model'],
            data['origin'],
            data['destination'],
            data['ride_time'],
            int(data['seats_available']),
            int(data['price_per_seat'])
        ))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Ride posted successfully!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/book/<int:ride_id>', methods=['POST'])
def book_ride(ride_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT seats_available FROM rides WHERE id = ?", (ride_id,))
        row = cursor.fetchone()
        
        if not row or row[0] <= 0:
            conn.close()
            return jsonify({"status": "error", "message": "No seats available."}), 400
            
        cursor.execute("UPDATE rides SET seats_available = seats_available - 1 WHERE id = ?", (ride_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": "Seat booked! Contact the driver to confirm."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    init_db()
    print("🚀 RideMate server running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)