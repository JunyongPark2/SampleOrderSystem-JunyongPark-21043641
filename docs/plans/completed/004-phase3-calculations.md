# Phase 3: 계산 공식 단일 모듈

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고. SPEC.md §8 Single Source of Truth 준수.

## 목표

부족분/실생산량/총생산시간/대기 수요/재고 상태 5개 공식을 순수 함수로 한 모듈에만 구현해, 이후 모든 Service(승인 판정, 생산라인, 모니터링)가 동일한 구현을 공유하도록 강제한다.

## 선행 조건

Phase 1(도메인 모델) 완료. Phase 2와는 독립적이지만, 순서상 Phase 2 이후 진행.

## 작업 범위

- `services/calculations.py`에 SPEC.md §8 표의 5개 공식 구현:
  - `shortage(quantity, stock) -> int`
  - `actual_yield(shortage, yield_rate) -> int` (`ceil` 적용)
  - `total_production_time(avg_production_time, actual_yield) -> float`
  - `pending_demand(orders, sample_id) -> int` (RESERVED+PRODUCING+CONFIRMED 합)
  - `stock_status(stock, pending_demand) -> Literal["고갈","부족","여유"]`

## 비작업 범위

- 이 함수들을 호출하는 Service(주문 승인/생산라인/모니터링) 자체 — Phase 6, 7, 8에서 구현.

## 수정하거나 생성할 파일

```
src/sampleorder/services/calculations.py
tests/test_calculations.py
```

## 구현 단계

1. `shortage(quantity, stock)`: `max(quantity - stock, 0)` — 음수 방지(재고 초과분은 0으로 처리).
2. `actual_yield(shortage, yield_rate)`: `math.ceil(shortage / yield_rate)`, `shortage == 0`이면 `0` 반환.
3. `total_production_time(avg_production_time, actual_yield)`: 단순 곱셈.
4. `pending_demand(orders, sample_id)`: `sample_id`가 일치하고 상태가 `{RESERVED, PRODUCING, CONFIRMED}`인 주문의 `quantity` 합.
5. `stock_status(stock, pending_demand)`: `stock <= 0` → "고갈", `stock < pending_demand` → "부족", 그 외 "여유"(SPEC.md §5.3 표 순서 그대로 판정 — 고갈을 먼저 체크).

## 검증 방법

`pytest tests/test_calculations.py` 전체 통과.

## 테스트 계획

- `shortage`: `quantity < stock`(음수 방지), `quantity == stock`(0), `quantity > stock`(양수).
- `actual_yield`: `yield_rate == 1.0`(부족분과 동일), `yield_rate` 소수(올림 발생 케이스, 예: 부족분 170/수율 0.92 → 185.86.. → 186), `shortage == 0`.
- `total_production_time`: 단순 곱셈 검증.
- `pending_demand`: REJECTED/RELEASE 상태 주문이 합산에서 제외되는지 확인.
- `stock_status`: 3구간 경계값(`stock=0`, `stock=pending_demand-1`, `stock=pending_demand`) 모두 확인.

## 완료 조건

- [x] `tests/test_calculations.py` 전체 통과, 특히 `ceil` 올림 경계값 케이스 포함.
- [x] 이후 Phase 6/7/8의 Service들이 이 모듈을 import만 하고 자체 계산식을 재구현하지 않음(코드 리뷰 체크 항목) — Phase 6/7/8 구현 시 계속 확인 예정.

## 진행 기록

- `services/calculations.py`에 `shortage/actual_yield/total_production_time/pending_demand/stock_status` 5개 순수 함수 구현. `stock_status`는 고갈(`STOCK_DEPLETED`)을 가장 먼저 체크(SPEC.md §5.3 판정 순서 그대로).
- **SPEC.md 예시 화면 수치와의 불일치 확인**: SPEC.md §4.2/§6.1 예시 화면(`실생산량 206 ea / 165 min`, `실생산량 54 ea`)은 §8 공식(`ceil(부족분/수율)`)으로 재계산하면 각각 185/54.34→55가 나와 예시 숫자와 어긋난다. SPEC.md §0/§8이 "화면 레이아웃은 예시일 뿐이며 계산식이 Single Source of Truth"라고 명시하므로, 예시 숫자가 아니라 §8 공식 그대로 구현했다. 예시 화면 수치는 PDF에서 옮기며 생긴 오타로 추정되며, PDF 원본과 대조가 필요하면 별도 확인 필요(SPEC.md 자체는 수정하지 않음 — 공식이 정본이라는 문서 방침을 그대로 따름).
- `tests/test_calculations.py` 10개 테스트(부족분 3구간, 실생산량 3케이스, 총생산시간, 대기수요 상태 필터, 재고상태 3구간 경계값) 작성 및 통과: `pytest tests/test_calculations.py -q` → 10 passed.
