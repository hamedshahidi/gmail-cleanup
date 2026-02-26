# Task013 — Monorepo Task Runner (Taskfile)

## Phase
Phase 5 — Quality & Confidence (Developer Experience)

## Goal
Add a root-level Taskfile (`task`) to orchestrate common repo workflows across Python + Node.

We keep:
- Python workflow intact (pytest, uvicorn)
- Next.js workflow intact (npm scripts in apps/web)

We add a single entry point:
- `task test` → run backend tests + web build + web e2e tests
- `task build:web` → build web
- `task dev:api` / `task dev:web` → run servers
- `task dev:all` → run API + web concurrently in one command
- `task pw:install` → install Playwright browsers

## Requirements
- Add `Taskfile.yml` at repo root using the EXACT content specified below.
- Do NOT require secrets.
- Do NOT call Google endpoints in any test path.
- Keep CLI untouched.
- Keep existing npm scripts untouched.
- Update `docs/development-plan.md` to include Task013 and mark it Completed after verification.
- Update documentation minimally (root README and/or apps/web README) to mention `task` usage + Playwright browser install helper.

## EXACT Taskfile.yml Content

Create `Taskfile.yml` at repo root with this exact content:

```yaml
version: "3"

tasks:
  # ----------------------------
  # Dev
  # ----------------------------
  dev:
    desc: Run API and Web dev servers concurrently
    deps: [dev:api, dev:web]
    cmds:
      - echo "Use 'task dev:api' and 'task dev:web' in separate terminals, or run 'task dev:all' for one-command concurrency."

  # One-command concurrency using background processes.
  # Works in many environments, but if it behaves oddly on Windows,
  # use two terminals with dev:api and dev:web.
  dev:all:
    desc: Run API and Web dev servers concurrently (single command)
    cmds:
      - |
        bash -lc '
          set -e
          (task dev:api) &
          (task dev:web) &
          wait
        '

  dev:api:
    desc: Run FastAPI dev server (reload)
    cmds:
      - bash -lc 'PYTHONPATH=apps/api uvicorn app.main:app --reload --host 127.0.0.1 --port 8000'

  dev:web:
    desc: Run Next.js dev server
    dir: apps/web
    cmds:
      - npm run dev

  # ----------------------------
  # Build
  # ----------------------------
  build:
    desc: Build web (Next.js)
    deps: [build:web]

  build:web:
    desc: Build Next.js app
    dir: apps/web
    cmds:
      - npm run build

  # ----------------------------
  # Test
  # ----------------------------
  test:
    desc: Run backend tests + web build + web e2e tests
    deps: [test:api, test:web:build, test:web:e2e]

  test:api:
    desc: Run Python tests (no Google endpoints)
    cmds:
      - python -m pytest -q

  test:web:
    desc: Run all web checks
    deps: [test:web:build, test:web:e2e]

  test:web:build:
    desc: Build Next.js app
    dir: apps/web
    cmds:
      - npm run build

  test:web:e2e:
    desc: Run Playwright E2E tests (mocked /api/*)
    dir: apps/web
    cmds:
      - npm run test:e2e

  # ----------------------------
  # Helpers
  # ----------------------------
  pw:install:
    desc: Install Playwright browsers for apps/web
    dir: apps/web
    cmds:
      - npx playwright install
