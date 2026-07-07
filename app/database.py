import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "aarogya_bharat.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        health_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        contact TEXT,
        email TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        hospital TEXT NOT NULL,
        availability TEXT NOT NULL,
        rating REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        health_id TEXT NOT NULL,
        doctor_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time_slot TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT,
        FOREIGN KEY (health_id) REFERENCES patients(health_id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medical_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        health_id TEXT NOT NULL,
        date TEXT NOT NULL,
        record_type TEXT NOT NULL,
        doctor TEXT NOT NULL,
        diagnosis TEXT,
        notes TEXT,
        FOREIGN KEY (health_id) REFERENCES patients(health_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        health_id TEXT NOT NULL,
        name TEXT NOT NULL,
        dosage TEXT NOT NULL,
        timing TEXT NOT NULL,
        instructions TEXT,
        FOREIGN KEY (health_id) REFERENCES patients(health_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vaccinations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        health_id TEXT NOT NULL,
        name TEXT NOT NULL,
        age TEXT NOT NULL,
        status TEXT NOT NULL,
        importance TEXT,
        FOREIGN KEY (health_id) REFERENCES patients(health_id)
    )
    """)
    
    # Seed mock data if empty
    cursor.execute("SELECT COUNT(*) FROM doctors")
    if cursor.fetchone()[0] == 0:
        # Seed Doctors
        doctors_data = [
            ("Rajesh Kumar", "General Medicine", "AIIMS Delhi", "Mon-Fri 9AM-1PM", 4.8),
            ("Ananya Sharma", "Cardiology", "Apollo Hospital Chennai", "Tue-Thu 2PM-5PM", 4.9),
            ("Siddharth Patel", "Pediatrics", "KIMS Hyderabad", "Mon-Sat 10AM-2PM", 4.7),
            ("Priyanka Sen", "Dermatology", "Manipal Hospital Bengaluru", "Wed-Fri 4PM-7PM", 4.6),
            ("Amit Verma", "General Medicine", "Fortis Hospital Mumbai", "Mon-Wed 11AM-3PM", 4.5),
        ]
        cursor.executemany("INSERT INTO doctors (name, specialty, hospital, availability, rating) VALUES (?, ?, ?, ?, ?)", doctors_data)
        
        # Seed default Patient
        cursor.execute("INSERT INTO patients (health_id, name, age, gender, contact, email) VALUES (?, ?, ?, ?, ?, ?)",
                       ("HB-1234", "Ramesh Dev", 35, "Male", "9876543210", "ramesh@aarogyabharat.in"))
        
        # Seed initial appointments
        cursor.execute("INSERT INTO appointments (id, health_id, doctor_id, date, time_slot, status, details) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ("APT-101", "HB-1234", 1, "2026-07-10", "10:30 AM", "booked", "General physical examination consultation"))
                       
        # Seed initial medical records
        records_data = [
            ("HB-1234", "2026-06-01", "Prescription", "Rajesh Kumar", "Common Cold", "Amoxicillin 500mg, Paracetamol 650mg"),
            ("HB-1234", "2026-05-15", "Lab Report", "Rajesh Kumar", "Routine Blood Test", "CBC counts normal. Hemoglobin: 14.2 g/dL"),
        ]
        cursor.executemany("INSERT INTO medical_records (health_id, date, record_type, doctor, diagnosis, notes) VALUES (?, ?, ?, ?, ?, ?)", records_data)
        
        # Seed medications
        meds_data = [
            ("HB-1234", "Paracetamol 650mg", "1 tablet", "Three times a day", "After meals, only if fever > 100 F"),
            ("HB-1234", "Atorvastatin 10mg", "1 tablet", "Once daily at night", "For cholesterol management"),
        ]
        cursor.executemany("INSERT INTO medications (health_id, name, dosage, timing, instructions) VALUES (?, ?, ?, ?, ?)", meds_data)
        
        # Seed vaccinations
        vacs_data = [
            ("HB-1234", "COVID-19 Booster", "Adult", "completed", "Highly recommended to prevent severe respiratory illness"),
            ("HB-1234", "Influenza", "Annual", "due", "Annual shot recommended before winter season"),
        ]
        cursor.executemany("INSERT INTO vaccinations (health_id, name, age, status, importance) VALUES (?, ?, ?, ?, ?)", vacs_data)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
