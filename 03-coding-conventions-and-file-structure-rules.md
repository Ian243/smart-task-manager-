# Coding Conventions & File-Structure Ground Rules

**Status: BINDING.** Every session building this project — whether it's me or a coding agent picking this up later — follows this document for *how* code gets written and organized, regardless of which phase of the implementation plan is being worked on. This is separate from `02-finalized-architecture-and-implementation-plan.md`, which governs *what* gets built and in what order; this doc governs *how* the code itself is structured and written.

---

## 1. File Consolidation Principle (the core rule)

**Default to fewer files.** Splitting code into many small files feels organized but actually makes it harder for a human or coding agent to build a mental model of the system — they have to jump between files to see how pieces relate. A new file is only justified when at least one of these is true:

1. **It's a genuinely separate runnable/deployable unit** (e.g. `main.py` vs. a migration script) — not just "a different topic."
2. **It would otherwise cause a circular import** that can't be reasonably avoided by reordering.
3. **The combined file would exceed ~300–400 lines** and mixing concerns would hurt readability more than a top-level comment/section-divider would.
4. **The code is genuinely reused independently** across multiple unrelated features (e.g. a shared utility imported by both the auth module and the AI module).

**None of these is "each database table gets its own file" or "each API endpoint gets its own file" by default.** Small, related pieces belong together in one file with clear internal sections, not scattered across a directory.

### Applying this to the current codebase (Phase 0/1)
**Status: DONE.** The 7 original one-per-entity model files have been consolidated into 2:
- `models/user.py` — `User` model only (the one entity every other table depends on; auth logic will grow around it independently)
- `models/task_domain.py` — `Task`, `Comment`, `ActivityLog`, `Attachment`, `RecurringTaskTemplate`, `NotificationLog` together, since they're all small, all task-domain, and are never meaningfully used without each other

Re-verified after consolidation: `configure_mappers()` passes, all 7 tables still register on `Base.metadata`, FastAPI app still imports cleanly. Use this same judgment (group by domain, not by table) for `schemas/`, `routers/`, and `services/` as they're built in later phases — e.g. expect `routers/tasks.py` to hold task CRUD + comments + attachments endpoints together rather than three separate router files, unless one of them grows past the ~300–400 line threshold.

---

## 5. Handoff Expectations for an Autonomous Coding Agent

This project may be handed to an autonomous coding agent (e.g. Google Antigravity) to build out remaining phases with minimal supervision. A few things that matter specifically for that mode of work, on top of everything above:

- **Read `02-finalized-architecture-and-implementation-plan.md` first, in full**, before starting any phase — it contains the scope policy, tech stack, architecture, ERD-equivalent entity list, API surface, and the per-phase Definition of Done. Do not re-derive architecture decisions that are already made there.
- **Treat the "Definition of Done" checklist in that doc as a hard gate**, not a suggestion — a phase isn't complete until every box is checked, including the regression check (`configure_mappers()` / app import) and manual endpoint verification.
- **n8n workflows (Phase 6) must be provisioned via n8n's REST API or JSON import, not via simulated UI clicking** — export the resulting workflow definitions into `n8n/workflows/*.json` in the repo so they're reproducible and reviewable like any other code artifact.
- **Do not introduce new top-level folders or restructure the existing layout** (`core/`, `models/`, `schemas/`, `routers/`, `services/`) without a clear justification tied to Rule 1 above — if unsure, keep new code inside the existing structure.
- **When a model changes, generate the Alembic migration in the same unit of work**, and sanity-check it (e.g. compile the DDL, as was done for the initial migration) rather than assuming `--autogenerate` got it perfectly right.
- **Stop and flag rather than guess** if a requirement in the DPR/finalized doc seems ambiguous or contradicted by something already built — this project has already had several rounds of scope refinement, so an apparent contradiction is more likely a signal to check than an invitation to improvise.

---

## 2. Inline Comments Rule

Every future file must be written so a coding agent (or a human) picking it up cold can understand *why* a piece of code exists, not just *what* it does — the code already shows *what*; comments should carry information the code can't.

**Required:**
- **One-line module header** at the top of every file: what lives here, and — if it was consolidated per Rule 1 — a one-line note of what's grouped and why.
- **Docstring on every class and function** stating its purpose and any non-obvious behavior (e.g. "raises X if Y", "assumes caller already validated Z"). Docstrings state *intent*, not a restatement of the signature.
- **Inline `#` comments at every non-obvious decision point** — anywhere the "why" isn't obvious from the code itself. Concretely: business-rule choices (e.g. why a field is nullable), trade-offs made under time constraints, anything that looks like it could be "simplified" but isn't for a specific reason, and any spot a future change is likely to need care (e.g. "changing this enum requires a matching Alembic migration").
- **`# TODO:` markers** for anything intentionally incomplete or deferred to a later phase, so a coding agent doesn't mistake a stub for a bug.

**Not required / to avoid:**
- Comments that just restate the line below it (`# increment counter` above `counter += 1`) — this is noise, not signal, and this project already leans toward being over-commented in the *useful* direction rather than the mechanical direction.
- Comments duplicating what a docstring already says.

**Style already in use and to keep:** the models built so far include comments like *"Soft delete — rows are flagged, not removed, so activity history survives 'deletion'"* — that's the right level: short, explains the *why*, sits right next to the relevant line. Keep matching that style.

---

## 3. Naming & Structure Conventions

- `snake_case` for files, functions, variables. `PascalCase` for classes.
- Routers stay thin — they parse the request, call a service function, return the response. No business logic in a router.
- Services hold the actual logic and are the layer both REST routes *and* the future AI agent call into — this is what keeps one source of truth for business rules (already decided in the finalized architecture doc; restated here because it's a direct consequence of the file-consolidation rule: services should be grouped by domain the same way models are, not one-function-per-file).
- Config/secrets never hardcoded — always via `app/core/config.py` and environment variables.
- Every new model change ships with its Alembic migration in the same piece of work, not deferred.

---

## 4. What This Means Going Forward

Before starting each new phase, quickly check: *does this phase's code fit in the existing files, or does it genuinely need a new one, per Rule 1?* Default answer is "it fits" unless one of the four justifications clearly applies. When in doubt, ask rather than defaulting to a new file.
