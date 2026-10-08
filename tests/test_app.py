from datetime import date, timedelta

from app.models import STATUS_ISSUED, STATUS_REJECTED, STATUS_RETURNED, Equipment, Loan, db
from tests.conftest import login


def request_arduino(client, quantity=1, days=7):
    return client.post("/equipment/1/request", data={"quantity": quantity, "days": days, "purpose": "test"},
                       follow_redirects=True)


# ---------------------------------------------------------------- health & api
def test_health_endpoint_reports_database_up(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "UP"
    assert res.get_json()["database"] == "CONNECTED"


def test_api_lists_equipment_with_availability(client):
    data = client.get("/api/equipment").get_json()
    assert data[0]["asset_code"] == "LAB-ARD-01"
    assert data[0]["available_qty"] == 2


# ---------------------------------------------------------------- auth
def test_unauthenticated_user_is_redirected_to_login(client):
    res = client.get("/equipment")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_student_can_register_and_login(client):
    res = client.post("/register", data={"name": "New Student", "roll_no": "2401500", "password": "secret1"},
                      follow_redirects=True)
    assert b"Registration successful" in res.data
    res = login(client, "2401500", "secret1")
    assert b"Browse equipment" in res.data


def test_duplicate_roll_number_is_rejected(client):
    res = client.post("/register", data={"name": "Dup", "roll_no": "2401999", "password": "secret1"},
                      follow_redirects=True)
    assert b"already registered" in res.data


def test_wrong_password_is_rejected(client):
    res = login(client, "2401999", "wrong-password")
    assert b"Invalid roll number or password" in res.data


def test_student_cannot_open_assistant_pages(student):
    assert student.get("/admin/").status_code == 403


# ---------------------------------------------------------------- loan workflow
def test_student_can_request_equipment(student, app):
    res = request_arduino(student)
    assert b"sent to the lab assistant" in res.data
    with app.app_context():
        assert Loan.query.count() == 1


def test_request_more_than_available_is_rejected(student, app):
    res = request_arduino(student, quantity=5)
    assert b"Only 2 unit(s)" in res.data
    with app.app_context():
        assert Loan.query.count() == 0


def test_loan_period_is_limited(student):
    res = request_arduino(student, days=30)
    assert b"Loan period must be between" in res.data


def test_student_active_loan_limit(student, app):
    with app.app_context():
        db.session.add(Equipment(name="Breadboard", category="Prototyping", asset_code="LAB-BRD-01", total_qty=10))
        db.session.commit()
    for _ in range(3):
        student.post("/equipment/2/request", data={"quantity": 1, "days": 3})
    res = student.post("/equipment/2/request", data={"quantity": 1, "days": 3}, follow_redirects=True)
    assert b"at most 3 active" in res.data


def test_assistant_approval_issues_item_and_reduces_availability(student, assistant, app):
    request_arduino(student, quantity=2, days=5)
    res = assistant.post("/admin/loans/1/approve", follow_redirects=True)
    assert b"Issued Arduino Uno R3 Kit" in res.data
    with app.app_context():
        loan = db.session.get(Loan, 1)
        assert loan.status == STATUS_ISSUED
        assert loan.due_date == date.today() + timedelta(days=5)
        assert db.session.get(Equipment, 1).available_qty == 0


def test_cannot_approve_when_stock_is_exhausted(student, assistant, app):
    request_arduino(student, quantity=2)
    request_arduino(student, quantity=1)
    assistant.post("/admin/loans/1/approve")
    res = assistant.post("/admin/loans/2/approve", follow_redirects=True)
    assert b"Not enough" in res.data


def test_assistant_can_reject_request(student, assistant, app):
    request_arduino(student)
    assistant.post("/admin/loans/1/reject")
    with app.app_context():
        assert db.session.get(Loan, 1).status == STATUS_REJECTED


def test_return_restores_availability(student, assistant, app):
    request_arduino(student, quantity=2)
    assistant.post("/admin/loans/1/approve")
    assistant.post("/admin/loans/1/return")
    with app.app_context():
        assert db.session.get(Loan, 1).status == STATUS_RETURNED
        assert db.session.get(Equipment, 1).available_qty == 2


def test_loan_past_due_date_is_flagged_overdue(student, assistant, app):
    request_arduino(student)
    assistant.post("/admin/loans/1/approve")
    with app.app_context():
        loan = db.session.get(Loan, 1)
        loan.due_date = date.today() - timedelta(days=2)
        db.session.commit()
        assert loan.is_overdue and loan.days_overdue == 2
    assert assistant.get("/api/stats").get_json()["overdue_loans"] == 1


# ---------------------------------------------------------------- equipment management
def test_assistant_can_add_equipment(assistant, app):
    res = assistant.post("/admin/equipment", data={"name": "ESP32 DevKit", "category": "Microcontroller",
                                                   "asset_code": "lab-esp-01", "total_qty": 4},
                         follow_redirects=True)
    assert b"ESP32 DevKit added" in res.data
    with app.app_context():
        assert Equipment.query.filter_by(asset_code="LAB-ESP-01").one().total_qty == 4


def test_quantity_cannot_drop_below_issued_units(student, assistant):
    request_arduino(student, quantity=2)
    assistant.post("/admin/loans/1/approve")
    res = assistant.post("/admin/equipment/1/update", data={"total_qty": 1}, follow_redirects=True)
    assert b"cannot be below" in res.data


# ---------------------------------------------------------------- monitoring
def test_metrics_endpoint_exposes_lablend_metrics(student, assistant, client):
    request_arduino(student)
    assistant.post("/admin/loans/1/approve")
    body = client.get("/metrics").data.decode()
    assert 'lablend_equipment_units{state="issued"} 1.0' in body
    assert 'lablend_loans{status="overdue"} 0.0' in body
    assert "lablend_loans_issued_total 1.0" in body
    assert "flask_http_request_total" in body


# ---------------------------------------------------------------- csv export
def test_assistant_can_export_loans_as_csv(student, assistant):
    request_arduino(student, quantity=2)
    assistant.post("/admin/loans/1/approve")
    res = assistant.get("/admin/loans/export.csv")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert "attachment; filename=lablend-loans-" in res.headers["Content-Disposition"]
    lines = res.data.decode().strip().splitlines()
    assert lines[0].startswith("Loan ID,Student,Roll No,Equipment")
    assert "Test Student,2401999,Arduino Uno R3 Kit,LAB-ARD-01,2" in lines[1]
    assert lines[1].split(",")[-2] == "ISSUED"


def test_csv_export_respects_status_filter(student, assistant):
    request_arduino(student)
    lines = assistant.get("/admin/loans/export.csv?status=RETURNED").data.decode().strip().splitlines()
    assert len(lines) == 1  # header only


def test_student_cannot_export_loans(student):
    assert student.get("/admin/loans/export.csv").status_code == 403
