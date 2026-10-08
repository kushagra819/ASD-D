"""LabLend - Lab Equipment Issue & Return Tracker."""
import os

from flask import Flask

from .metrics import init_metrics
from .models import db
from .seed import seed_admin, seed_demo_data


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///lablend.db"),
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        ADMIN_ROLL=os.environ.get("ADMIN_ROLL", "labadmin"),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", "admin123"),
        SEED_DEMO_DATA=os.environ.get("SEED_DEMO_DATA", "true").lower() == "true",
        APP_VERSION=os.environ.get("APP_VERSION", "1.0.0"),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    init_metrics(app)

    from .routes import admin_bp, api_bp, auth_bp, student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        seed_admin(app)
        if app.config["SEED_DEMO_DATA"]:
            seed_demo_data()

    return app
