"""Initial data: the lab assistant account and a sample equipment catalogue."""
from datetime import date, datetime, timedelta

from .models import (ROLE_ASSISTANT, ROLE_STUDENT, STATUS_ISSUED, STATUS_REQUESTED,
                     Equipment, Loan, User, db)

SAMPLE_EQUIPMENT = [
    ("Arduino Uno R3 Kit", "Microcontroller", "LAB-ARD-01", "Board, USB cable, jumper wires", 10),
    ("Raspberry Pi 4 (4 GB)", "Single Board Computer", "LAB-RPI-01", "With 32 GB SD card and adapter", 4),
    ("ESP32 DevKit", "Microcontroller", "LAB-ESP-01", "Wi-Fi + Bluetooth board", 8),
    ("Digital Multimeter", "Measurement", "LAB-DMM-01", "Auto-ranging, with probes", 6),
    ("Breadboard (830 points)", "Prototyping", "LAB-BRD-01", "Full size solderless breadboard", 15),
    ("HC-SR04 Ultrasonic Sensor", "Sensor", "LAB-SEN-01", "Distance sensor 2 cm - 400 cm", 12),
    ("DHT11 Temperature Sensor", "Sensor", "LAB-SEN-02", "Temperature and humidity module", 12),
    ("Digital Storage Oscilloscope", "Measurement", "LAB-DSO-01", "2-channel, 50 MHz", 2),
    ("Soldering Station", "Tools", "LAB-SLD-01", "Temperature controlled, 60 W", 3),
]


def seed_admin(app):
    if User.query.filter_by(roll_no=app.config["ADMIN_ROLL"]).first():
        return
    admin = User(name="Lab Assistant", roll_no=app.config["ADMIN_ROLL"], role=ROLE_ASSISTANT)
    admin.set_password(app.config["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()


def seed_demo_data():
    if Equipment.query.first():
        return
    for name, category, code, desc, qty in SAMPLE_EQUIPMENT:
        db.session.add(Equipment(name=name, category=category, asset_code=code, description=desc, total_qty=qty))

    students = []
    for name, roll in [("Kushagra Mehta", "2401064"), ("Siddharth Maru", "2401060"), ("Varun Masand", "2401062")]:
        s = User(name=name, roll_no=roll, role=ROLE_STUDENT)
        s.set_password("student123")
        db.session.add(s)
        students.append(s)
    db.session.flush()

    by_code = {e.asset_code: e for e in Equipment.query.all()}
    now = datetime.now()
    # Two current loans, one of them past its due date, and one pending request.
    db.session.add_all([
        Loan(equipment=by_code["LAB-ARD-01"], user=students[0], quantity=1, days_requested=7,
             purpose="Mini project prototype", status=STATUS_ISSUED,
             requested_at=now - timedelta(days=3), issued_at=now - timedelta(days=3),
             due_date=date.today() + timedelta(days=4)),
        Loan(equipment=by_code["LAB-DMM-01"], user=students[1], quantity=1, days_requested=3,
             purpose="Circuit testing", status=STATUS_ISSUED,
             requested_at=now - timedelta(days=6), issued_at=now - timedelta(days=6),
             due_date=date.today() - timedelta(days=3)),
        Loan(equipment=by_code["LAB-RPI-01"], user=students[2], quantity=1, days_requested=5,
             purpose="IoT experiment", status=STATUS_REQUESTED, requested_at=now - timedelta(hours=2)),
    ])
    db.session.commit()
