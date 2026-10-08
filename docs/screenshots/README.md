# Screenshots from the test run

These were captured on 08 Oct 2026 from a real run of this repository in the build environment
(Linux, Docker 29). The browser images are LabLend, Prometheus, Grafana and Jenkins pages.
The `cli_*` images show the actual terminal output saved in `docs/evidence/`.

Jenkins here is the `jenkinsci/blueocean` image (Jenkins 2.346.3 with Pipeline, Git and Blue Ocean
pre-installed), because the build network could not download plugins. It ran the real `Jenkinsfile`
against `https://github.com/kushagra819/ASD-D.git` (branch `main`). On your laptop, `jenkins/` builds a
current Jenkins LTS instead. Full console logs of builds #1–#4 are in `docs/evidence/jenkins_build_*.txt`.

Not possible from the build environment (take these yourselves, see `docs/LAB_GUIDE.md`):
GitHub web pages (the network blocks GitHub's stylesheet host) and Jira (needs your Atlassian account).

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
| 20_jenkins_dashboard.png | Jenkins dashboard with the LabLend-CI-CD job | 4 |
| 21_jenkins_job_build_history.png | Job page with build history #1–#4 | 4, 5 |
| 21b_jenkins_job_configuration.png | Job configuration: GitHub repo, `*/main`, SCM polling, Jenkinsfile | 4, 5 |
| 22_jenkins_blueocean_activity.png | Blue Ocean: #1 manual, #2 after PR #1 merge, #3 failed, #4 after revert | 4, 5 |
| 23_jenkins_blueocean_build4_success.png | Build #4 pipeline graph: all six stages green | 4, 5 |
| 24_jenkins_blueocean_build3_failed.png | Build #3: Unit Tests failed, image build and deploy skipped | 4 |
| 25_jenkins_build2_console_scm_trigger.png | Build #2 console: "Started by an SCM change", PR #1 merge commit | 5 |
| 26_jenkins_build4_test_results.png | JUnit test report: 22 tests passed | 4 |
| 27_jenkins_build3_test_failure.png | JUnit report of build #3 with the failing test | 4 |
| 32_lablend_all_loans_csv_button.png | All Loans with the new Download CSV button (v1.0.4 deployed by Jenkins) | 5 |
| 33_cli_git_main_pr_merge_and_revert.png | `main`: PR #1 merge, breaking change, `git revert` | 1 |
| 34_cli_csv_export.png | Downloaded CSV export | App |
