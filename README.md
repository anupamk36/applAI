# applAI

Technical README — applAI

Overview
- Monorepo containing a FastAPI `core-api` backend, a Vite/React `frontend`, ingestion `worker-ingest`, and automation tools in `automation/`.

Repository layout
- `core-api/` — Python FastAPI app (pyproject.toml, alembic migrations)
- `frontend/` — React + Vite frontend
- `worker-ingest/` — ingestion workers and adapters
- `automation/` — Node automation tools and Playwright scripts (screenshots under `local-screenshots/`)

Quickstart (macOS)

1) Backend (`core-api`)

Install dependencies (uses Poetry / pip as appropriate):

```bash
cd core-api
# If using poetry
poetry install
# or with pip/virtualenv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt || pip install .
```

Run migrations:

```bash
cd core-api
alembic upgrade head
```

Run the API (example using Uvicorn):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Environment variables
- The repository uses a `.env` file per service (for example `core-api/.env`). The `.env` file is intentionally excluded from source control. Create `core-api/.env` from the project-specific template or set the required variables in your environment.

Example `.env` entries (do NOT commit secrets):

```
DATABASE_URL=postgresql://user:pass@localhost:5432/applai
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=replace-with-secure-secret
```

2) Frontend

```bash
cd frontend
npm install
npm run dev
```

3) Worker / Ingest

```bash
cd worker-ingest
poetry install
python -m ingest.run
```

4) Automation

```bash
cd automation/apps/apply-runner
npm install
# run automation scripts or playwright flows
```

Screenshots / Images
The repo contains sample screenshots used by automation under:

- `automation/apps/apply-runner/local-screenshots/`

Examples (embedded):

![apply-runner-1](automation/apps/apply-runner/local-screenshots/1786713257836-loaded.png)
![apply-runner-2](automation/apps/apply-runner/local-screenshots/1786714777737-loaded.png)

Notes on commits & pushing
- The SSH remote `origin` can be set to SSH or HTTPS. If you prefer HTTPS:

```bash
git remote set-url origin https://github.com/anupamk36/applAI.git
```

- `.env` files are listed in `.gitignore` and should not be committed. If a `.env` accidentally became tracked, remove it from the index with:

```bash
git rm --cached core-api/.env
```

Development tips
- Use the repository `pyproject.toml` and `package.json` files to discover precise dependency lists and dev scripts.
- Run linters and formatters in each subproject (e.g., `eslint`, `prettier`, `ruff`, `black`) before committing.

Contact
- For repo-specific questions, reach out to the maintainer/author.
