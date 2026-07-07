import json
import os
import sys
from mcp.server.fastmcp import FastMCP

# Ensure the parent app directory is on the path so we can import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db_connection

mcp = FastMCP("aarogya-bharat-mcp")

@mcp.tool()
def get_doctors_by_specialty(specialty: str) -> str:
    """Get list of doctors in the directory by their specialty (e.g. General Medicine, Cardiology, Pediatrics, Dermatology).
    
    Args:
        specialty: The specialty name to filter by.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, specialty, hospital, availability, rating FROM doctors WHERE specialty LIKE ?", (f"%{specialty}%",))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return f"No doctors found with specialty '{specialty}'."
    
    results = []
    for r in rows:
        results.append({
            "name": r["name"],
            "specialty": r["specialty"],
            "hospital": r["hospital"],
            "availability": r["availability"],
            "rating": r["rating"]
        })
    return json.dumps(results, indent=2)

@mcp.tool()
def get_patient_medical_history(health_id: str) -> str:
    """Retrieve the lifelong medical records and history of the patient.
    
    Args:
        health_id: The unique patient health ID (e.g. HB-1234).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, record_type, doctor, diagnosis, notes FROM medical_records WHERE health_id = ? ORDER BY date DESC", (health_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return f"No medical records found for Health ID '{health_id}'."
    
    results = []
    for r in rows:
        results.append({
            "date": r["date"],
            "record_type": r["record_type"],
            "doctor": r["doctor"],
            "diagnosis": r["diagnosis"],
            "notes": r["notes"]
        })
    return json.dumps(results, indent=2)

@mcp.tool()
def book_appointment_slot(health_id: str, doctor_name: str, date: str, time_slot: str) -> str:
    """Book a new medical appointment slot for a patient with a doctor.
    
    Args:
        health_id: The unique patient health ID (e.g. HB-1234).
        doctor_name: The name of the doctor (e.g. Rajesh Kumar).
        date: Appointment date in YYYY-MM-DD format.
        time_slot: Time of the appointment (e.g. 10:30 AM).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if patient exists
    cursor.execute("SELECT name FROM patients WHERE health_id = ?", (health_id,))
    patient = cursor.fetchone()
    if not patient:
        conn.close()
        return f"Booking failed: Patient with Health ID '{health_id}' not registered."
        
    # Get doctor ID
    cursor.execute("SELECT id, hospital FROM doctors WHERE name LIKE ?", (f"%{doctor_name}%",))
    doctor = cursor.fetchone()
    if not doctor:
        conn.close()
        return f"Booking failed: Doctor '{doctor_name}' not found."
        
    doc_id = doctor["id"]
    hospital = doctor["hospital"]
    apt_id = f"APT-{hash(health_id + doctor_name + date + time_slot) % 10000}"
    
    cursor.execute(
        "INSERT INTO appointments (id, health_id, doctor_id, date, time_slot, status, details) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (apt_id, health_id, doc_id, date, time_slot, "booked", f"Consultation with Dr. {doctor_name} at {hospital}")
    )
    conn.commit()
    conn.close()
    
    return json.dumps({
        "status": "booked",
        "appointment_id": apt_id,
        "details": f"Confirmed booking for patient {patient['name']} with Dr. {doctor_name} on {date} at {time_slot}."
    })

@mcp.tool()
def get_medication_schedule(health_id: str) -> str:
    """Retrieve the medication list and schedule reminders for a patient.
    
    Args:
        health_id: The unique patient health ID (e.g. HB-1234).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, dosage, timing, instructions FROM medications WHERE health_id = ?", (health_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return f"No medications found for Health ID '{health_id}'."
        
    results = []
    for r in rows:
        results.append({
            "name": r["name"],
            "dosage": r["dosage"],
            "timing": r["timing"],
            "instructions": r["instructions"]
        })
    return json.dumps(results, indent=2)

@mcp.tool()
def get_vaccination_schedule(health_id: str) -> str:
    """Retrieve complete vaccination history and upcoming recommendations for a patient.
    
    Args:
        health_id: The unique patient health ID (e.g. HB-1234).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, age, status, importance FROM vaccinations WHERE health_id = ?", (health_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return f"No vaccination record found for Health ID '{health_id}'."
        
    results = []
    for r in rows:
        results.append({
            "name": r["name"],
            "age": r["age"],
            "status": r["status"],
            "importance": r["importance"]
        })
    return json.dumps(results, indent=2)

if __name__ == "__main__":
    mcp.run("stdio")
