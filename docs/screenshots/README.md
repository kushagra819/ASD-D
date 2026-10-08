# Screenshots from the test run

These were captured on 08 Oct 2026 from a real run of this repository in the build environment
(Linux, Docker 29). The browser images are LabLend, Prometheus and Grafana pages.
The `cli_*` images show the actual terminal output saved in `docs/evidence/`.
Jenkins and Jira screenshots must be taken on your own laptop/account (see `docs/LAB_GUIDE.md`).

| File | What it shows | Experiment |
|---|---|---|
| 01_lablend_login.png | Login page | App |
| 02_student_browse_equipment.png | Student catalogue with live availability | App |
| 03_student_request_sent.png | Student requests 2 × ESP32 DevKit | App |
| 04_student_my_loans.png | Student's loans and statuses | App |
| 05_admin_dashboard.png | Lab assistant dashboard: pending, issued, overdue | App |
| 06_admin_request_approved.png | Request approved and issued with due date | App |
| 07_admin_equipment.png | Equipment management | App |
| 08_admin_all_loans.png | Full loan history | App |
| 09_health_endpoint.png | `/health` → UP, database CONNECTED | 3, 5 |
| 10_prometheus_targets.png | Prometheus targets lablend, node, prometheus UP | 7 |
| 11_prometheus_graph_lablend_loans.png | PromQL `lablend_loans` | 7 |
| 11b_prometheus_graph_http_requests.png | PromQL request rate by status | 7 |
| 12_grafana_dashboard.png | Grafana dashboard: app + CPU/memory/disk | 7 |
| 13_metrics_endpoint.png | Raw `/metrics` output | 7 |
| 14_cli_docker_build_images.png | `docker build`, `docker images`, `docker run` | 2 |
| 15_cli_docker_container_lifecycle.png | `docker ps/logs/stop/start/rm` | 2 |
| 16_cli_docker_compose.png | Compose services, volumes, network, logs | 3 |
| 17_cli_pytest.png | 19 unit tests passing | 4 |
| 18_cli_pipeline_stages.png | Jenkinsfile stage commands run in a container from the Jenkins image (no Jenkins UI) | 4, 5 |
| 19_cli_git_history.png | Feature branches merged with `--no-ff` | 1 |
