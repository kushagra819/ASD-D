"""Prometheus metrics for LabLend.

HTTP metrics (request count, latency) come from prometheus-flask-exporter.
Business metrics (units issued, overdue loans, pending requests) are read
from the database every time Prometheus scrapes /metrics.
"""
from prometheus_client import CollectorRegistry, Counter
from prometheus_client.core import GaugeMetricFamily
from prometheus_flask_exporter import PrometheusMetrics

from .models import STATUS_ISSUED, STATUS_REQUESTED, Equipment, Loan


class LabLendCollector:
    def __init__(self, app):
        self.app = app

    def collect(self):
        with self.app.app_context():
            equipment = Equipment.query.all()
            total = sum(e.total_qty for e in equipment)
            issued = sum(e.issued_qty for e in equipment)
            issued_loans = Loan.query.filter_by(status=STATUS_ISSUED).all()
            overdue = sum(1 for l in issued_loans if l.is_overdue)
            pending = Loan.query.filter_by(status=STATUS_REQUESTED).count()

        units = GaugeMetricFamily("lablend_equipment_units", "Lab equipment units by state", labels=["state"])
        units.add_metric(["total"], total)
        units.add_metric(["issued"], issued)
        units.add_metric(["available"], total - issued)
        yield units

        loans = GaugeMetricFamily("lablend_loans", "Current loans by status", labels=["status"])
        loans.add_metric(["requested"], pending)
        loans.add_metric(["issued"], len(issued_loans))
        loans.add_metric(["overdue"], overdue)
        yield loans

        yield GaugeMetricFamily("lablend_equipment_items", "Distinct equipment items in catalogue", value=len(equipment))


def init_metrics(app):
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(app, registry=registry, group_by="endpoint")
    metrics.info("lablend_app_info", "LabLend application info", version=app.config["APP_VERSION"])
    registry.register(LabLendCollector(app))

    app.extensions["lablend_counters"] = {
        "requests": Counter("lablend_loan_requests", "Loan requests raised by students", registry=registry),
        "issued": Counter("lablend_loans_issued", "Loans issued by the lab assistant", registry=registry),
        "returned": Counter("lablend_loans_returned", "Loans returned to the lab", registry=registry),
    }
    return metrics


def count(app, name):
    app.extensions["lablend_counters"][name].inc()
