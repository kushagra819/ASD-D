"""Database models for LabLend: users, lab equipment and loans."""
from datetime import date, datetime, timedelta

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

ROLE_STUDENT = "student"
ROLE_ASSISTANT = "assistant"

# Loan lifecycle: REQUESTED -> ISSUED -> RETURNED   (or REQUESTED -> REJECTED)
STATUS_REQUESTED = "REQUESTED"
STATUS_ISSUED = "ISSUED"
STATUS_RETURNED = "RETURNED"
STATUS_REJECTED = "REJECTED"
ACTIVE_STATUSES = (STATUS_REQUESTED, STATUS_ISSUED)

MAX_ACTIVE_LOANS_PER_STUDENT = 5
MAX_LOAN_DAYS = 14


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_STUDENT)

    loans = db.relationship("Loan", back_populates="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_assistant(self):
        return self.role == ROLE_ASSISTANT

    def active_loan_count(self):
        return self.loans.filter(Loan.status.in_(ACTIVE_STATUSES)).count()


class Equipment(db.Model):
    __tablename__ = "equipment"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    asset_code = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.String(255), default="")
    total_qty = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)

    loans = db.relationship("Loan", back_populates="equipment", lazy="dynamic")

    @property
    def issued_qty(self):
        return sum(l.quantity for l in self.loans.filter_by(status=STATUS_ISSUED))

    @property
    def available_qty(self):
        return self.total_qty - self.issued_qty

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "asset_code": self.asset_code,
            "total_qty": self.total_qty,
            "issued_qty": self.issued_qty,
            "available_qty": self.available_qty,
        }


class Loan(db.Model):
    __tablename__ = "loans"

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    days_requested = db.Column(db.Integer, nullable=False, default=7)
    purpose = db.Column(db.String(200), default="")
    status = db.Column(db.String(20), nullable=False, default=STATUS_REQUESTED)
    requested_at = db.Column(db.DateTime, default=datetime.now)
    issued_at = db.Column(db.DateTime)
    due_date = db.Column(db.Date)
    returned_at = db.Column(db.DateTime)

    equipment = db.relationship("Equipment", back_populates="loans")
    user = db.relationship("User", back_populates="loans")

    @property
    def is_overdue(self):
        return self.status == STATUS_ISSUED and self.due_date is not None and self.due_date < date.today()

    @property
    def days_overdue(self):
        return (date.today() - self.due_date).days if self.is_overdue else 0

    @property
    def display_status(self):
        return "OVERDUE" if self.is_overdue else self.status

    def issue(self):
        self.status = STATUS_ISSUED
        self.issued_at = datetime.now()
        self.due_date = date.today() + timedelta(days=self.days_requested)

    def mark_returned(self):
        self.status = STATUS_RETURNED
        self.returned_at = datetime.now()
