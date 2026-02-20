# Task 002: Scaffold monorepo structure (apps/api, apps/web, packages/core)

## Goal
Introduce cloud-shaped structure without breaking current CLI.

## Constraints
- Keep existing CLI entry point working: gmail-cleanup = gmail_cleanup.cli:app
- Do not move existing gmail_cleanup package yet (only add new folders)
- No secrets added

## Work
1) Create:
   - apps/api (FastAPI skeleton)
   - apps/web (Next.js skeleton placeholder, minimal)
   - packages/core (placeholder for extracted core operations)
2) Add minimal READMEs in each folder describing purpose.
3) Add root docs/architecture.md describing the target architecture (UI -> API -> core -> Gmail).

## Acceptance criteria
- Repo has new folders and docs
- Existing CLI still runs unchanged
