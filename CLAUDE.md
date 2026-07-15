# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Docs structure

```
docs/
├── PRD.md                              # Background/goals/scope/FRs·NFRs/acceptance criteria — "what and why" to build
├── SPEC.md                             # Per-menu screen I/O, validation messages, formulas — "what shows on screen"
├── ARCHITECTURE.md                     # Layering/directory structure/PoC reuse mapping/sequences/persistence·exception·test strategy
├── adr/                                # Decisions that are hard to reverse or affect the whole system
│   ├── ADR-0001-JSON파일기반영속성.md
│   ├── ADR-0002-계층형MVC구조채택.md
│   ├── ADR-0003-생산진행상태갱신방식.md
│   └── ADR-0004-승인시점재고예약.md
└── plans/
    └── active/                         # In-progress implementation plans (move to completed/ etc. once done)
        ├── 000-overview.md             # Overall plan goals/scope/shared risks·rollback/phase index
        └── 001~013-phase*.md           # One executable unit per phase (goal/files/steps/verification/tests/done criteria)
```

Cross-document precedence: if formulas or status values disagree across documents, SPEC.md is the source of truth (ARCHITECTURE.md §9). Add new ADRs as `docs/adr/ADR-NNNN-title.md`; write new implementation plans as one overview file plus one file per phase under `docs/plans/active/`.

## Commit discipline

When a small unit (e.g. one phase, one document, one function/module) is done, commit it before moving on to the next unit; never let several units pile up before committing. If unsure, ask the user whether to commit before proceeding. Don't batch unrelated changes into a single commit — commit as soon as each small, self-contained unit of work is finished.

## Commit messages

Before running `git commit`, follow the `committing-with-care` skill (`.claude/skills/committing-with-care/SKILL.md`): English Conventional Commits title, Korean body that leads with **what changed** (required) and may add **why** (optional).

## Stock remaining rate

Do not implement a stock "remaining rate" (잔여율).

## Docs consistency check

Whenever a unit of work finishes, check the docs under `docs/` (PRD.md, SPEC.md, ARCHITECTURE.md, etc.) for any drift from the code/design just changed. If drift is found, update the affected document immediately.
