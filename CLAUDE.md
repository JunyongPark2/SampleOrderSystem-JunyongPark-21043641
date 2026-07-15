# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commit messages

Before running `git commit`, follow the `committing-with-care` skill (`.claude/skills/committing-with-care/SKILL.md`): English Conventional Commits title, Korean body that leads with **what changed** (required) and may add **why** (optional).

## Commit discipline

Commit after each small, self-contained unit of work is finished, rather than batching unrelated changes into a single commit.

## 재고 잔여율

재고 "잔여율"은 구현하지 않는다.

## Docs 정합성 확인

작업이 끝날 때마다 `docs/` 하위 문서(PRD.md, SPEC.md, ARCHITECTURE.md 등)를 확인하여 방금 변경한 코드/설계와 괴리가 생긴 부분이 없는지 점검한다. 괴리가 발견되면 즉시 해당 문서를 갱신한다.
