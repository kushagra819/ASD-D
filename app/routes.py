"""HTTP routes: authentication, student pages, lab-assistant pages and JSON API."""
import csv
import io
from datetime import date
from functools import wraps

from flask import (Blueprint, Response, abort, current_app, flash, g, jsonify,
                   redirect, render_template, request, session, url_for)
from sqlalchemy import text

from .metrics import count
from .models import (MAX_ACTIVE_LOANS_PER_STUDENT, MAX_LOAN_DAYS, ROLE_STUDENT,
                     STATUS_ISSUED, STATUS_REJECTED, STATUS_REQUESTED, Equipment,
                     Loan, User, db)

auth_bp = Blueprint("auth", __name__)
student_bp = Blueprint("student", __name__)
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
api_bp = Blueprint("api", __name__)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
@auth_bp.before_app_request
def load_user():
    uid = session.get("user_id")
    g.user = db.session.get(User, uid) if uid else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def assistant_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not g.user.is_assistant:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def dashboard_stats():
    equipment = Equipment.query.all()
    issued_loans = Loan.query.filter_by(status=STATUS_ISSUED).all()
    total = sum(e.total_qty for e in equipment)
    issued = sum(l.quantity for l in issued_loans)
    return {
        "items": len(equipment),
        "total_units": total,
        "issued_units": issued,
        "available_units": total - issued,
        "pending_requests": Loan.query.filter_by(status=STATUS_REQUESTED).count(),
        "overdue_loans": sum(1 for l in issued_loans if l.is_overdue),
    }


# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------
@auth_bp.route("/")
def index():
    if g.user is None:
        return redirect(url_for("auth.login"))
    return redirect(url_for("admin.dashboard" if g.user.is_assistant else "student.catalogue"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(roll_no=request.form.get("roll_no", "").strip()).first()
        if user and user.check_password(request.form.get("password", "")):
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("auth.index"))
        flash("Invalid roll number or password.", "error")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        password = request.form.get("password", "")
        if not name or not roll_no or len(password) < 6:
            flash("Name and roll number are required; password must be at least 6 characters.", "error")
        elif User.query.filter_by(roll_no=roll_no).first():
            flash("This roll number is already registered.", "error")
        else:
            user = User(name=name, roll_no=roll_no, role=ROLE_STUDENT)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


# --------------------------------------------------------------------------
# Student
# --------------------------------------------------------------------------
@student_bp.route("/equipment")
@login_required
def catalogue():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    query = Equipment.query
    if q:
        query = query.filter(Equipment.name.ilike(f"%{q}%"))
    if category:
        query = query.filter_by(category=category)
    categories = [c for (c,) in db.session.query(Equipment.category).distinct().order_by(Equipment.category)]
    return render_template("student/catalogue.html", equipment=query.order_by(Equipment.name).all(),
                           categories=categories, q=q, category=category, max_days=MAX_LOAN_DAYS)


@student_bp.route("/equipment/<int:equipment_id>/request", methods=["POST"])
@login_required
def request_equipment(equipment_id):
    item = db.get_or_404(Equipment, equipment_id)
    try:
        quantity = int(request.form.get("quantity", 1))
        days = int(request.form.get("days", 7))
    except ValueError:
        quantity, days = 0, 0

    if g.user.active_loan_count() >= MAX_ACTIVE_LOANS_PER_STUDENT:
        flash(f"You can have at most {MAX_ACTIVE_LOANS_PER_STUDENT} active requests/loans.", "error")
    elif quantity < 1 or quantity > item.available_qty:
        flash(f"Only {item.available_qty} unit(s) of {item.name} are available.", "error")
    elif days < 1 or days > MAX_LOAN_DAYS:
        flash(f"Loan period must be between 1 and {MAX_LOAN_DAYS} days.", "error")
    else:
        db.session.add(Loan(equipment=item, user=g.user, quantity=quantity, days_requested=days,
                            purpose=request.form.get("purpose", "").strip()[:200]))
        db.session.commit()
        count(current_app, "requests")
        flash(f"Request for {item.name} sent to the lab assistant.", "success")
    return redirect(url_for("student.catalogue"))


@student_bp.route("/my-loans")
@login_required
def my_loans():
    loans = g.user.loans.order_by(Loan.requested_at.desc()).all()
    return render_template("student/my_loans.html", loans=loans)


# --------------------------------------------------------------------------
# Lab assistant
# --------------------------------------------------------------------------
@admin_bp.route("/")
@assistant_required
def dashboard():
    pending = Loan.query.filter_by(status=STATUS_REQUESTED).order_by(Loan.requested_at).all()
    issued = Loan.query.filter_by(status=STATUS_ISSUED).order_by(Loan.due_date).all()
    overdue = [l for l in issued if l.is_overdue]
    return render_template("admin/dashboard.html", stats=dashboard_stats(),
                           pending=pending, issued=issued, overdue=overdue)


@admin_bp.route("/equipment", methods=["GET", "POST"])
@assistant_required
def equipment():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("asset_code", "").strip().upper()
        category = request.form.get("category", "").strip()
        try:
            qty = int(request.form.get("total_qty", 0))
        except ValueError:
            qty = 0
        if not name or not code or not category or qty < 1:
            flash("Name, category, asset code and a quantity of at least 1 are required.", "error")
        elif Equipment.query.filter_by(asset_code=code).first():
            flash(f"Asset code {code} already exists.", "error")
        else:
            db.session.add(Equipment(name=name, category=category, asset_code=code, total_qty=qty,
                                     description=request.form.get("description", "").strip()))
            db.session.commit()
            flash(f"{name} added to the catalogue.", "success")
        return redirect(url_for("admin.equipment"))
    return render_template("admin/equipment.html", equipment=Equipment.query.order_by(Equipment.name).all())


@admin_bp.route("/equipment/<int:equipment_id>/update", methods=["POST"])
@assistant_required
def update_equipment(equipment_id):
    item = db.get_or_404(Equipment, equipment_id)
    try:
        qty = int(request.form.get("total_qty", item.total_qty))
    except ValueError:
        qty = -1
    if qty < item.issued_qty or qty < 1:
        flash(f"Quantity cannot be below the {item.issued_qty} unit(s) currently issued.", "error")
    else:
        item.total_qty = qty
        db.session.commit()
        flash(f"{item.name} quantity updated to {qty}.", "success")
    return redirect(url_for("admin.equipment"))


@admin_bp.route("/equipment/<int:equipment_id>/delete", methods=["POST"])
@assistant_required
def delete_equipment(equipment_id):
    item = db.get_or_404(Equipment, equipment_id)
    if item.loans.count():
        flash(f"{item.name} has loan history and cannot be deleted.", "error")
    else:
        db.session.delete(item)
        db.session.commit()
        flash(f"{item.name} removed from the catalogue.", "success")
    return redirect(url_for("admin.equipment"))


def filtered_loans():
    status = request.args.get("status", "")
    query = Loan.query
    if status:
        query = query.filter_by(status=status)
    return status, query.order_by(Loan.requested_at.desc()).all()


@admin_bp.route("/loans")
@assistant_required
def loans():
    status, rows = filtered_loans()
    return render_template("admin/loans.html", loans=rows, status=status)


@admin_bp.route("/loans/export.csv")
@assistant_required
def export_loans():
    _, rows = filtered_loans()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Loan ID", "Student", "Roll No", "Equipment", "Asset Code", "Quantity",
                     "Requested", "Issued", "Due Date", "Returned", "Status", "Days Overdue"])
    fmt = lambda d: d.strftime("%Y-%m-%d") if d else ""
    for l in rows:
        writer.writerow([l.id, l.user.name, l.user.roll_no, l.equipment.name, l.equipment.asset_code, l.quantity,
                         fmt(l.requested_at), fmt(l.issued_at), fmt(l.due_date), fmt(l.returned_at),
                         l.display_status, l.days_overdue])
    filename = f"lablend-loans-{date.today():%Y%m%d}.csv"
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})


@admin_bp.route("/loans/<int:loan_id>/approve", methods=["POST"])
@assistant_required
def approve_loan(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    if loan.status != STATUS_REQUESTED:
        flash("Only pending requests can be approved.", "error")
    elif loan.quantity > loan.equipment.available_qty:
        flash(f"Not enough {loan.equipment.name} available to issue.", "error")
    else:
        loan.issue()
        db.session.commit()
        count(current_app, "issued")
        flash(f"Issued {loan.equipment.name} to {loan.user.name}, due {loan.due_date:%d %b %Y}.", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/loans/<int:loan_id>/reject", methods=["POST"])
@assistant_required
def reject_loan(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    if loan.status != STATUS_REQUESTED:
        flash("Only pending requests can be rejected.", "error")
    else:
        loan.status = STATUS_REJECTED
        db.session.commit()
        flash(f"Request from {loan.user.name} rejected.", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/loans/<int:loan_id>/return", methods=["POST"])
@assistant_required
def return_loan(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    if loan.status != STATUS_ISSUED:
        flash("Only issued items can be returned.", "error")
    else:
        loan.mark_returned()
        db.session.commit()
        count(current_app, "returned")
        flash(f"{loan.equipment.name} returned by {loan.user.name}.", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))


# --------------------------------------------------------------------------
# JSON API + health check
# --------------------------------------------------------------------------
@api_bp.route("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(status="UP", database="CONNECTED", version=current_app.config["APP_VERSION"])
    except Exception:
        return jsonify(status="DOWN", database="DISCONNECTED"), 503


@api_bp.route("/api/equipment")
def api_equipment():
    return jsonify([e.to_dict() for e in Equipment.query.order_by(Equipment.name)])


@api_bp.route("/api/stats")
def api_stats():
    return jsonify(dashboard_stats())
