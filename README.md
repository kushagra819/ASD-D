# LabLend — Lab Equipment Issue & Return Tracker

LabLend replaces the paper register used to lend lab equipment (Arduino kits, sensors,
multimeters, Raspberry Pis…) to students. Students request equipment online, the lab
assistant approves and issues it, and overdue returns are flagged automatically.

The project is the ASD&D (Agile Software Development & DevOps) mini project. One application is
carried through every lab experiment: Git/GitHub → Docker → Docker Compose → Jenkins CI/CD →
Agile/Jira → Monitoring.

## Features

| Role | What they can do |
|---|---|
| Student | Register / log in with roll number, browse and search equipment with live availability, request items for 1–14 days, view own loans and due dates |
| Lab assistant | Dashboard (available, issued, pending, overdue), approve / reject requests, mark returns, add equipment, change stock, full loan history |

Business rules: at most 3 active requests/loans per student, loan period 1–14 days, stock is
re-checked at approval, quantity can't go below units issued, items past the due date show as **OVERDUE**.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask, SQLAlchemy, Gunicorn |
| Frontend | Jinja2 templates, HTML, CSS |
| Database | PostgreSQL 16 (SQLite for local dev/tests) |
| Tests | pytest (19 tests) |
| Containers | Docker (multi-stage), Docker Compose |
| CI/CD | Jenkins (pipeline as code + configuration as code) |
| Monitoring | Prometheus, Grafana, node-exporter |
| Agile | Jira (CSV import in `jira/`) |

## Run it

```bash
docker compose up -d --build
docker compose ps
```

| Service | URL | Login |
|---|---|---|
| LabLend | http://localhost:5000 | lab assistant `labadmin` / `admin123`; students `2401064`, `2401060`, `2401062` / `student123` |
| Prometheus | http://localhost:9090 | – |
| Grafana | http://localhost:3000 | `admin` / `admin` |
| node-exporter | http://localhost:9100/metrics | – |

Stop with `docker compose down` (add `-v` to also delete the database volume).

### Without Docker (development)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v
python wsgi.py                                         # http://localhost:5000 (SQLite)
```

## Jenkins (one command)

```bash
cd jenkins
docker compose up -d --build
```

Open http://localhost:8080 and log in as `admin` / `admin123`. The **LabLend-CI-CD** job is created
automatically from `jenkins/casc.yaml`. It polls GitHub every 2 minutes and also accepts GitHub webhooks.
Click **Build Now** for the first run.

Pipeline stages (`Jenkinsfile`): Checkout → Build Test Image → Unit Tests (JUnit report) →
Build Docker Image → Deploy (Docker Compose) → Smoke Test (`/health`).

The repository must be public for Jenkins to clone it without credentials. For a private repository,
add a GitHub token under *Manage Jenkins → Credentials* and select it in the job's SCM settings.
To use a different repo or branch, set `LABLEND_REPO_URL` / `LABLEND_BRANCH` before `docker compose up`.

## Monitoring

* `GET /metrics` exposes HTTP metrics (`flask_http_request_total`, request duration histogram) and
  business metrics: `lablend_equipment_units{state=total|issued|available}`,
  `lablend_loans{status=requested|issued|overdue}`, `lablend_loans_issued_total`, `lablend_loans_returned_total`.
* Prometheus scrapes the app (`web:5000`), node-exporter (`node-exporter:9100`) and itself.
* Grafana opens on the **LabLend – Application & Server Monitoring** dashboard: app status, overdue
  loans, pending requests, units issued vs available, request rate, p95 latency, CPU, memory and disk.

Useful PromQL:

```
lablend_loans{status="overdue"}
sum by (status) (rate(flask_http_request_total[1m]))
100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[1m])))
100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
```

## Experiment mapping

| Exp | Topic | Where in this repo |
|---|---|---|
| 1 | Git & GitHub | commit history, feature branches merged with `--no-ff` |
| 2 | Docker | `Dockerfile` (test + production stages) |
| 3 | Docker Compose | `docker-compose.yml` (web, db, prometheus, node-exporter, grafana) |
| 4 | Jenkins CI | `Jenkinsfile`, `jenkins/` |
| 5 | Automated deployment | Jenkins *Build Docker Image* + *Deploy* + *Smoke Test* stages |
| 6 | Agile / Jira | `jira/LabLend_Jira_Import.csv` (5 epics, 18 stories/tasks) |
| 7 | Monitoring | `app/metrics.py`, `monitoring/` |

## Project structure

```
app/                 Flask application (models, routes, metrics, templates, static)
tests/               pytest test suite
monitoring/          Prometheus config and Grafana dashboard (built into images)
jenkins/             Jenkins image, plugins and configuration-as-code
jira/                Jira CSV import (epics, stories, tasks)
docs/                Lab guide and screenshots
Dockerfile           Multi-stage image for the app
docker-compose.yml   Full stack
Jenkinsfile          CI/CD pipeline
```

## Team

Kushagra Mehta (2401064) · Siddharth Maru (2401060) · Varun Masand (2401062)
