# LabLend — 1-hour lab guide (commands + screenshots to take)

Everything below runs on your own laptop, so the screenshots are your real evidence.
Commands work in PowerShell, Command Prompt, Git Bash or a Linux/macOS terminal.
Needed: **Docker Desktop (running)** and **Git**. Use full-screen windows for screenshots.

Screenshots already taken from a test run of the same project are in `docs/screenshots/`.
You can compare yours against them.

---

## Exp 1 — Git & GitHub (≈15 min)

```bash
git clone https://github.com/kushagra819/ASD-D.git
cd ASD-D
git log --oneline --graph --all
git branch -a
```
📸 `git log --oneline --graph` (shows feature branches merged into the main line)

**Each member makes one real change on their own branch**, from their own laptop / GitHub account:

```bash
git config user.name "Your Name"
git config user.email "you@example.com"
git checkout -b feature/<your-name>-change
# edit a file (ideas below), then:
git add .
git commit -m "LL-<jira id>: <what you changed>"
git push -u origin feature/<your-name>-change
```
Change ideas (one each):
* **Kushagra:** in `app/templates/login.html`, add a 4th bullet to the list, e.g. `<li>Request history for every student</li>`.
* **Siddharth:** in `app/templates/base.html`, change the footer text, e.g. add "Thadomal Shahani Engineering College".
* **Varun:** in `app/models.py`, change `MAX_LOAN_DAYS = 14` to `21`.

Then open a **Pull Request** on GitHub for each branch and merge it.
📸 GitHub repo page, 📸 a Pull Request, 📸 `git log --oneline --graph` after merging

Rollback demo (one person):
```bash
git revert HEAD --no-edit      # undo the last commit with a new commit
git log --oneline -3
git push
```
📸 revert in `git log`

---

## Exp 2 — Docker (≈10 min)

```bash
docker --version
docker build -t lablend .
docker images
docker run -d -p 5001:5000 --name lablend-single lablend
docker ps
docker logs lablend-single
```
Open http://localhost:5001 → 📸 login page served from the container
```bash
docker stop lablend-single
docker start lablend-single
docker inspect lablend-single
docker rm -f lablend-single
```
📸 `docker build`, `docker images`, `docker ps`, `docker logs`

---

## Exp 3 — Docker Compose (≈10 min)

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs web
```
📸 `docker compose up`, 📸 `docker compose ps` (5 services: web, db, prometheus, node-exporter, grafana), 📸 Docker Desktop → Containers

Open http://localhost:5000:
* Log in as student **2401064 / student123** → 📸 *Browse equipment*. Request an item → 📸 *My Loans*
* Log out, log in as **labadmin / admin123** → 📸 *Dashboard* (pending + overdue), approve the request → 📸
* 📸 *Equipment* page, 📸 *All Loans* page
* http://localhost:5000/health → 📸 `{"status":"UP","database":"CONNECTED"}`

Persistence check: `docker compose down` then `docker compose up -d`. Your loan is still there because of the `pgdata` volume.

---

## Exp 4 & 5 — Jenkins CI/CD + automated deployment (≈15 min)

The repo must be **public** (GitHub → Settings → Change visibility) or Jenkins can't clone it.
The job builds the `main` branch. To build another branch, set `LABLEND_BRANCH` first, e.g.
`$env:LABLEND_BRANCH="my-branch"` (PowerShell) or `export LABLEND_BRANCH=my-branch` (bash).

```bash
cd jenkins
docker compose up -d --build      # first time downloads Jenkins plugins: 3-5 minutes
cd ..
```
Open http://localhost:8080 → log in **admin / admin123** → job **LabLend-CI-CD** is already there.
Click **Build Now**.

📸 Job page with **Stage View** (Checkout → Build Test Image → Unit Tests → Build Docker Image → Deploy → Smoke Test)
📸 **Console Output** (pytest `19 passed`, `docker compose up`, `LabLend is UP after deployment`)
📸 **Test Result** (19 tests) and **Build History**

**Automatic deployment (Exp 5):** make any small change, commit and push to `main`.
Within 2 minutes Jenkins starts a new build by itself (SCM polling). After it finishes,
http://localhost:5000/health shows `"version": "1.0.<build number>"` → 📸 build triggered by SCM change + new version.

(Optional webhook instead of polling: run `ngrok http 8080`. In GitHub → Settings → Webhooks, add
`https://<ngrok-url>/github-webhook/` with content type `application/json`.)

---

## Exp 6 — Agile with Jira (≈15 min)

1. Create a free account at https://www.atlassian.com/software/jira and create a **Scrum** project
   named **LabLend** (key `LL`).
2. Import the backlog: ⚙ **Settings → System → External System Import → CSV**, upload
   `jira/LabLend_Jira_Import.csv`. Map the columns: *Issue ID → Issue Id*, *Parent ID → Parent Id*,
   *Issue Type*, *Summary*, *Description*, *Priority*, *Story Points → Story point estimate*, *Labels*.
   (If CSV import isn't available on your plan, create the 5 epics and a few stories by hand from the CSV.)
3. **Backlog:** create *Sprint 1*, *Sprint 2*, *Sprint 3*. Drag issues into them by their label
   (`sprint-1`, `sprint-2`, `sprint-3`). Start **Sprint 1**.
4. **Board:** move cards To Do → In Progress → Done.
5. **Dependencies:** open *"Approve or reject requests"* → Link issue → **is blocked by**
   *"Request equipment for a number of days"*. Do the same for *"Create Jenkins pipeline"* **is blocked by** *"Write pytest unit tests"*.

📸 Backlog with sprints, 📸 Board, 📸 Epics/Timeline view, 📸 an issue showing its "blocked by" link, 📸 sprint report / burndown (if available)

---

## Exp 7 — Monitoring (≈5 min)

* http://localhost:9090/targets → 📸 `lablend`, `node`, `prometheus` all **UP**
* http://localhost:9090/graph, run `lablend_loans` and `rate(flask_http_request_total[1m])` → 📸
* http://localhost:3000 (admin / admin) → dashboard **LabLend – Application & Server Monitoring** → 📸
  (app status, overdue loans, request rate, CPU, memory, disk)
* http://localhost:5000/metrics → 📸 raw metrics

Use the app for a minute (login, requests) so the graphs have data.

---

## Clean up

```bash
docker compose down            # stop the app stack
cd jenkins && docker compose down
```
