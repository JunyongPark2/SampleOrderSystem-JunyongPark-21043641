# Plan 017: 승인 시점 재고 예약 도입 (출고 시 재고 음수화 버그 수정)

> 근거 문서: [`PRD.md`](../../PRD.md) FR-3.2/FR-4.2/FR-6.1~6.2, [`SPEC.md`](../../SPEC.md) §4.2/§5.3/§6.2, [`ARCHITECTURE.md`](../../ARCHITECTURE.md) §1(레이어 구조), `docs/adr/ADR-0003-생산진행상태갱신방식.md`.
> 상태: 계획 단계 — 아직 구현을 시작하지 않았다.
>
> `docs/plans/completed/`의 기존 번호(000~016)와 겹치지 않도록 이 계획은 017번을 사용한다.

## 배경 (버그 재현)

동일 시료(`S-001`, 초기 `stock=60`)에 대해 다음 순서로 진행하면 `sample.stock`이 음수가 된다.

1. 주문 A(수량 100) 승인 → `preview_approval`이 `shortage = 100 - 60 = 40`으로 판정, `PRODUCING` 전환 및 생산 큐 등록. 이때 `stock`은 여전히 60 (`src/sampleorder/services/order_service.py:86-101`).
2. 주문 B(수량 60, 같은 시료) 승인 → `preview_approval`이 여전히 raw `stock=60`만 보고 `shortage = 60 - 60 = 0`으로 **SUFFICIENT** 판정 → 즉시 `CONFIRMED`. A가 이미 확보하기로 되어 있던 60을 B가 중복으로 확보받는다.
3. B 출고(`ShippingService.release`, `src/sampleorder/services/shipping_service.py:24-29`) → `stock = 60 - 60 = 0`.
4. A의 생산 완료(`ProductionService.advance`, `src/sampleorder/services/production_service.py:106-118`) → `stock = 0 + 40 = 40`, A `CONFIRMED` 전환.
5. A 출고 → `stock = 40 - 100 = -60`. **재고 음수 발생.**

근본 원인은 두 가지다.

- `OrderService.preview_approval`/`confirm_approval`이 **다른 주문이 이미 확보(승인)한 수량을 전혀 고려하지 않고** raw `sample.stock`만으로 재고 충분/부족을 판정한다. 즉 "재고 예약" 개념이 없다.
- `ShippingService.release`가 차감 전 `sample.stock >= order.quantity` 여부를 전혀 검증하지 않아, 위 1의 결과로 재고가 실제로 부족해진 상태에서도 조건 없이 차감해 음수를 그대로 저장한다.

## 사용자 결정 사항

**승인 시점에 재고를 예약한다.** FIFO(선입선출) 원칙과 일치시킨다 — 먼저 승인된 주문이 그 시점의 가용 재고를 먼저 차지하고, 나중에 승인 판정을 받는 주문은 이미 선점된 수량을 제외한 나머지만 "가용 재고"로 본다.

다만 `SPEC.md:157`/`PRD.md:130`에 이미 명시된 불변식 **"재고는 승인 시점에 차감하지 않는다(차감은 출고 시, FR-6.1)"**는 유지한다 — `sample.stock` 필드 자체의 실제 차감/증가 시점(승인 시 변화 없음 · 생산 완료 시 `+=` · 출고 시 `-=`)은 이번 작업으로 바꾸지 않는다. 대신 "예약"은 **저장되는 새 필드가 아니라, 이미 `CONFIRMED`/`PRODUCING` 상태로 전환된 주문들의 `quantity` 합을 그때그때 계산하는 파생값**으로 구현한다. 이렇게 하면:

- `Sample`/`samples.json` 스키마 변경, 데이터 마이그레이션이 전혀 필요 없다.
- "재고 예약"은 이미 검증받은(승인된) 주문에 대해서만 성립하고, 아직 승인 여부가 결정되지 않은 `RESERVED` 상태 주문은 예약분에 포함하지 않는다 — 승인 전 주문이 재고를 선점하면 나중 승인 심사가 불필요하게 보수적으로 막히기 때문.

`src/sampleorder/services/calculations.py`에 이미 같은 패턴이 존재한다: `pending_demand(orders, sample_id)`가 특정 상태 주문들의 `quantity` 합을 계산하고, `MonitoringService.stock_report()`(FR-4.2)가 이를 소비한다. 이번 작업은 같은 계산 패턴을 대상 상태만 다르게 하나 더 추가하는 것이다.

| 함수 | 대상 상태 | 용도 | 의미 |
|---|---|---|---|
| `pending_demand` (기존, 변경 없음) | `RESERVED + PRODUCING + CONFIRMED` | FR-4.2 모니터링 "재고 상태" 표시 | 아직 승인 여부가 결정되지 않은 주문까지 포함한 전망(forward-looking) 지표 |
| `reserved_qty` (신규) | `PRODUCING + CONFIRMED` | FR-3.2 승인 판정 시 가용 재고 계산 | 이미 승인되어 물리적 재고 소비가 확정된 커밋(committed) 지표 |

두 지표는 목적이 다르므로 하나로 통합하지 않는다.

## 선행 조건

없음(기존 완료된 Phase 0~12 위에서 진행하는 버그 수정). `pending_demand`/`ApprovalPreview`/`ShippingService` 등 기존 코드를 그대로 확장한다.

## 작업 범위

- `calculations.py`에 예약 재고 계산 함수(`reserved_qty`, `available_stock`) 추가.
- `OrderService.preview_approval`이 예약 재고를 반영하도록 수정.
- `ShippingService.release()`에 재고 부족 방어 검증 추가 + `ShippingController`/`ShippingView`의 에러 처리.
- PRD.md/SPEC.md/ARCHITECTURE.md 갱신, 신규 ADR-0004 작성.

## 비작업 범위

- `Sample`/`samples.json` 스키마 변경(새 필드 추가) — 예약은 파생값으로만 구현.
- FR-4.2 모니터링의 `pending_demand`/`stock_status` 로직 변경 — 기존 동작 유지.
- 동시성 제어(락, 트랜잭션) — PRD.md §3 Out of Scope 그대로 유지, 단일 프로세스 순차 처리 전제.
- 이미 손상된(음수) 운영 데이터의 복구 스크립트 — 별도로 필요 시 사용자 확인 후 진행.

## 수정하거나 생성할 파일

```
src/sampleorder/services/calculations.py     (확장)
src/sampleorder/services/order_service.py    (확장)
src/sampleorder/services/shipping_service.py (확장)
src/sampleorder/controllers/shipping_controller.py (확장, 필요 시)
src/sampleorder/views/shipping_view.py       (확장, 필요 시)
tests/test_calculations.py                   (케이스 추가)
tests/test_order_service.py                  (케이스 추가)
tests/test_shipping_service.py               (케이스 추가)
docs/PRD.md / docs/SPEC.md / docs/ARCHITECTURE.md (드리프트 발견 시 갱신)
docs/adr/ADR-0004-*.md                       (신규)
```

## 구현 단계

1. `calculations.py`: `_RESERVED_STATUSES = {CONFIRMED, PRODUCING}` 정의, `reserved_qty(orders, sample_id)`(대상 상태·시료의 `quantity` 합)와 `available_stock(stock, reserved_qty)`(`max(stock - reserved_qty, 0)`, 음수 클램프) 추가. `pending_demand()`는 수정하지 않는다.
2. `OrderService.preview_approval(order_id)`: 대상 주문 자신을 제외한 같은 `sample_id`의 전체 주문을 `order_repo.list_all()`로 가져와 `reserved_qty()` 계산 → `available_stock()`으로 가용 재고를 구해 기존 `calculations.shortage(order.quantity, available)`에 전달. `sample.stock`은 화면 표시용으로 그대로 유지(SPEC.md §4.2 "현재 재고" 문구 변경 없음). `confirm_approval`/`ProductionService`는 변경하지 않는다.
3. `ShippingService.release()`: 차감 전 `sample.stock >= order.quantity` 검증 추가, 부족 시 명시적 예외(예: `InsufficientStockError`) 발생시키고 `stock`은 변경하지 않는다.
4. `ShippingController`/`ShippingView`: 위 예외를 사용자 메시지로 변환해 출력.
5. PRD.md/SPEC.md/ARCHITECTURE.md에서 이번 변경(가용 재고 기반 승인 판정, 출고 방어 검증)과 관련된 서술을 확인해 드리프트 발견 시 갱신, `docs/adr/ADR-0004-*.md` 신규 작성 — "예약은 파생값이며 저장 필드가 아니다", `reserved_qty` vs `pending_demand` 목적 차이를 기록.

작은 단위(계산 함수 → 승인 판정 수정 → 출고 방어 검증 → 문서/ADR)마다 커밋한다(CLAUDE.md 커밋 규율).

## 검증 방법

- 자동: `.venv/bin/python -m pytest -q` 전체 통과.
- 수동: `python main.py`로 배경 절 시나리오(A 100 → B 60) 재현 — 시료 재고 60으로 등록 → A 주문(수량 100) 승인(부족분 40, `PRODUCING`) → B 주문(수량 60) 승인 시도 시 "재고 부족" 분기로 안내되는지 확인(수정 전에는 "재고 충분"으로 바로 `CONFIRMED`).

## 테스트 계획

- `reserved_qty`가 `CONFIRMED`/`PRODUCING` 상태 주문의 수량만 합산하고 `RESERVED`/`RELEASE`/`REJECTED`나 다른 시료는 제외하는지.
- `available_stock`이 예약량이 재고보다 많을 때 0으로 클램프되는지.
- `preview_approval`이 다른 주문이 이미 확보한 수량을 제외하고 판정하는지(A 100 승인 후 B 60 승인 시 SHORTAGE로 판정), 아직 `RESERVED`(미승인) 상태 주문은 예약분에 포함하지 않는지.
- 기존 `preview_approval`/`confirm_approval` 테스트(다른 주문 없는 단순 케이스)가 `reserved_qty=0`으로 회귀 없이 그대로 통과하는지.
- `ShippingService.release()`가 재고 부족 상태에서 예외를 던지고 `stock`을 변경하지 않는지, 기존 정상 출고 테스트가 회귀 없이 통과하는지.

## 완료 조건

- [ ] `.venv/bin/python -m pytest -q` 전체 통과.
- [ ] 배경 절의 재현 시나리오(A 100 → B 60 → B 출고 → A 생산완료 → A 출고)를 `python main.py`로 수동 재현했을 때, B 승인 시점에 재고 부족(`PRODUCING`)으로 정확히 분기되고, 최종적으로 `sample.stock`이 음수가 되지 않음을 확인.
- [ ] PRD.md/SPEC.md/ARCHITECTURE.md, 신규 ADR-0004에 이번 결정이 반영됨.
- [ ] 작업 단위별로 커밋 완료.
