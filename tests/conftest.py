import pytest

from app import create_app
from app.models import Equipment, User, db


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SEED_DEMO_DATA": False,
        "ADMIN_ROLL": "labadmin",
        "ADMIN_PASSWORD": "admin123",
        "SECRET_KEY": "test",
    })
    with app.app_context():
        db.session.add(Equipment(name="Arduino Uno R3 Kit", category="Microcontroller",
                                 asset_code="LAB-ARD-01", total_qty=2))
        student = User(name="Test Student", roll_no="2401999", role="student")
        student.set_password("student123")
        db.session.add(student)
        db.session.commit()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, roll_no, password):
    return client.post("/login", data={"roll_no": roll_no, "password": password}, follow_redirects=True)


@pytest.fixture
def student(client):
    login(client, "2401999", "student123")
    return client


@pytest.fixture
def assistant(app):
    c = app.test_client()
    login(c, "labadmin", "admin123")
    return c
