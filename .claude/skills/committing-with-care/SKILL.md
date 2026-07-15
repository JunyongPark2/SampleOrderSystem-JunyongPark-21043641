---
name: committing-with-care
description: Use when writing a git commit message in this project, before running git commit
---

# Committing With Care

## Overview

Every commit message in this project has two parts: an English Conventional Commits title, and a Korean body. The body must state **무엇을 바꿨는지(what)**; **왜 바꿨는지(why)** is optional extra context.

## Format

```
<type>: <English summary, imperative mood>

<한국어로 작성한 "무엇을 바꿨는지" (필수)>
<한국어로 작성한 "왜 바꿨는지" (선택)>
```

**Title (English):**
- Use a Conventional Commits type: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`
- Imperative mood, no trailing period
- Example: `fix: reject zero-total orders in validator`

**Body (Korean):**
- **필수**: 무엇을 바꿨는지 (변경된 동작/로직을 한국어로 명확히 서술)
- **선택**: 왜 바꿨는지 (배경이 되는 버그, 요청, 제약이 있다면 덧붙인다)
- 왜에 대한 설명만 쓰고 무엇을 바꿨는지가 빠지면 안 된다
- **개조식 명사형 종결**: 각 항목은 `~했다`, `~있었다` 같은 서술형 종결어미 대신 `~변경`, `~추가`, `~수정`처럼 명사형으로 끝낸다
- **여러 항목이면 bullet(`-`)으로 분리**: 무엇을 바꿨는지가 두 가지 이상이거나, 무엇+왜가 각각 별개 항목이면 한 문단으로 이어 쓰지 말고 항목마다 줄을 나눠 `-`로 시작한다. 항목이 하나뿐이면 bullet 없이 한 줄로 쓴다.

## Example

Single item:
```
fix: reject zero-total orders in validator

주문 총액이 0 이하일 때도 에러를 던지도록 조건을 `< 0`에서 `<= 0`으로 변경.
```

Multiple items:
```
fix: cap coupon discounts and prevent negative order totals

- 쿠폰 할인 금액에 `coupon.maxAmount` 상한 적용
- 상한 적용 후에도 할인액이 소계를 초과하면 최종 금액이 0 미만으로 내려가지 않도록 하한 추가
- 마케팅팀의 할인 한도 설정 요청과, 일부 쿠폰이 마이너스 주문 총액을 만들어 인보이스 처리가 깨지던 문제 수정
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| Title with no type prefix (`Fix validator to reject...`) | Prefix with `fix:`, `feat:`, etc. |
| Body written in English | Write the body in Korean |
| Body only explains why, never states what changed | Lead with a clear sentence describing the change itself |
| Body sentences end in `~했다`/`~있었다` (서술형) | End with a noun form instead: `~변경`, `~추가`, `~수정` |
| Multiple items crammed into one paragraph | Split each item onto its own `-` bullet line |
