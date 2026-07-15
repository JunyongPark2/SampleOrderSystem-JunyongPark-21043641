# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This repository currently contains only planning documents (`docs/PRD.md`, this file) — no source code, `requirements.txt`, or `pyproject.toml` exist yet. The Python package layout, module responsibilities, and commands below reflect the **planned** architecture from the PRD, not code that exists today. When you start implementing, create the scaffolding described in "Architecture" and set up `pytest` per NFR-8 in the PRD.

## Commit discipline

- Follow the `committing-with-care` skill (`.claude/skills/committing-with-care/SKILL.md`) for every commit message: English Conventional Commits title, Korean body that leads with **what changed** (required) and may add **why** (optional).
- Commit after each small, self-contained unit of work (e.g., one repository class, one service function with its tests, one view) rather than batching unrelated changes into a single commit. This keeps history reviewable against the PRD's acceptance criteria (Section 9) and commit-history evaluation criterion (Section 2, Goal 5).

## Commands

No build/lint/test tooling exists yet. Once the project is scaffolded per the architecture below, the expected workflow (per PRD NFR-8) is:

```bash
pip install -r requirements.txt   # or per pyproject.toml, once created
pytest                             # run full test suite
pytest tests/path/to/test_x.py::test_name   # run a single test
python main.py                     # run the console app
```

Use `tmp_path` fixtures for any test that touches JSON persistence — never let tests write to the real `data/` directory (see DataPersistence's `conftest.py` pattern referenced in the PRD).

## Architecture (planned)

This is a console-based Python inventory/order-management system for a semiconductor sample fab ("S-Semi"), built by integrating four validated PoC repos (`ConsoleMVC`, `DataPersistence`, `DataMonitor`, `DummyDataGenerator` — sibling directories in the same workspace) rather than starting from scratch. See `docs/PRD.md` Section 7 for the full planned tree; the key structural decisions:

- **MVC with a services layer**: Controllers dispatch View ↔ Service calls but must not contain business logic themselves (stock/approval/production math lives in `services/`). This is a deliberate deviation from a plain MVC PoC skeleton, done specifically so business logic is unit-testable without console I/O (NFR-4).
- **JSON file persistence via atomic replace**: `json_store.py` writes to a temp file and `os.replace`s it into place (`data/samples.json`, `data/orders.json`) so a crash mid-write can't corrupt state (NFR-3). No SQLite/external DB — deliberately out of scope.
- **Single production line, FIFO**: Only one production line is modeled; queue order follows approval order and completion is computed from `production_start_time + total_production_time`, not a live background scheduler. Progress must be recomputed on each menu entry (or an explicit time-advance trigger) using an injectable time source (NFR-4), not `datetime.now()` called ad hoc — this is what makes production-line logic testable.
- **Single console process**: no multi-user access, no role-based login, no file locking — the two operator roles (주문 담당자 / 생산 담당자) share one menu tree in one process.

### Domain model and state machine

`Sample` (`sample_id`, `name`, `avg_production_time`, `yield_rate`, `stock`) and `Order` (`order_id`, `sample_id`, `customer_name`, `quantity`, `status`, `created_at`) are the two entities; see PRD Section 8 for exact dataclass shapes.

Order status transitions (PRD Section 4.3) are the core invariant the whole system enforces:

```
RESERVED --(reject)--> REJECTED                      # terminal, excluded from monitoring/production entirely
RESERVED --(approve, stock sufficient)--> CONFIRMED
RESERVED --(approve, stock insufficient)--> PRODUCING
PRODUCING --(production complete)--> CONFIRMED
CONFIRMED --(shipped)--> RELEASE
```

Key derived calculations that must live in the service layer (not views/controllers), since they're the parts of the PoCs that didn't exist yet and are core to correctness:

- **Shortfall handling on approval** (FR-3.2): if `stock < quantity`, shortfall = `quantity - stock`, actual production qty = `ceil(shortfall / yield_rate)`, total production time = `avg_production_time * actual_qty`. Stock is *not* decremented at approval time — only at shipment (FR-6.2).
- **Stock status for monitoring** (FR-4.2): judged against "pending demand" = sum of `RESERVED + PRODUCING + CONFIRMED` quantities for that sample (not against total orders) — 고갈 (`stock <= 0`) / 부족 (`stock < pending demand`) / 여유 (otherwise).
- **Console alignment for Korean text**: list/dashboard rendering must account for full-width character display width (`unicodedata.east_asian_width`), per DataMonitor's `render.py` pattern (NFR-5) — plain `str.ljust`/`rjust` will misalign Korean text.

Full functional requirements (FR-1.x through FR-6.x) and acceptance criteria are in `docs/PRD.md` Sections 5 and 9 — read them before implementing a given menu feature, since the PDF spec (`[CRA_AI] Day3_개인과제_반도체시료관리_r1 2.pdf`) is the ground truth the PRD was derived from.
