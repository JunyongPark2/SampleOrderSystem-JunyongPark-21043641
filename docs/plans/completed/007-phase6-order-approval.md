# Phase 6: 주문 승인/거절 + 생산라인 연동 (FR-3.1~3.3, FR-5.2)

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고. ARCHITECTURE.md §4.1 시퀀스 참고.

## 목표

`RESERVED` 주문 목록 조회, 승인(재고 충분/부족 자동 분기), 거절 기능을 완성하고, 재고 부족 시 생산라인 큐에 등록(enqueue)까지 연결한다. 생산 완료 처리 자체는 Phase 7에서 다룬다.

## 선행 조건

Phase 3(계산 모듈), Phase 5(주문 접수) 완료.

## 작업 범위

- `order_service.py`(기존 파일에 추가): `list_reserved_orders()`, `preview_approval(order_id)`(계산 미리보기), `confirm_approval(order_id, preview)`, `reject_order(order_id)`.
- `production_service.py`(신규): FIFO 큐 자료구조 + `enqueue(order_id, sample_id, shortage, actual_yield, total_time, started_at)`. 완료 처리(`advance`)는 이 Phase에서 구현하지 않음.
- `views/approval_view.py`, `controllers/approval_controller.py` 구현.

## 비작업 범위

- 생산 완료 처리(`advance`), 진행률 표시, 대기 큐 화면 — Phase 7.
- 출고 처리 — Phase 9.

## 수정하거나 생성할 파일

```
src/sampleorder/services/order_service.py        (확장)
src/sampleorder/services/production_service.py    (신규, enqueue만)
src/sampleorder/views/approval_view.py
src/sampleorder/controllers/approval_controller.py
tests/test_order_service.py                        (승인/거절 케이스 추가)
tests/test_production_service.py                   (신규, enqueue만)
```

## 구현 단계

1. `list_reserved_orders()`: `OrderRepository.list_by_status(RESERVED)`.
2. `preview_approval(order_id)`: `calculations.shortage`로 재고 비교, 부족 시 `calculations.actual_yield`/`total_production_time`까지 계산해 반환(ARCHITECTURE.md §4.1의 `ApprovalPreview`).
3. `confirm_approval(order_id, preview)`: 재고 충분 → `status=CONFIRMED`; 재고 부족 → `status=PRODUCING` + `production_service.enqueue(...)` 호출.
4. `reject_order(order_id)`: 즉시 `status=REJECTED`.
5. `production_service.py`: 큐를 `collections.deque`(또는 리스트)로 소유, `enqueue()`만 우선 구현(완료 처리는 다음 Phase).
6. `approval_view.py`: SPEC.md §4 예시 화면(재고 충분/부족 두 케이스) 구현, `Y`/`N` 확인.
7. `approval_controller.py`: 목록 비어있을 시 안내 후 메인 메뉴 복귀(SPEC.md §4.1).

## 검증 방법

- 자동: `pytest tests/test_order_service.py tests/test_production_service.py`.
- 수동: `python main.py` → `[3] 주문 승인/거절` → 재고 충분/부족 두 시나리오 모두 SPEC.md §4 예시 화면과 일치하는지 확인.

## 테스트 계획

- 재고 충분(`stock >= quantity`): 승인 시 즉시 `CONFIRMED`, 재고는 이 시점에 차감되지 않음(출고 시 차감, FR-6.1).
- 재고 부족(`stock < quantity`): 승인 확인 화면에 부족분/실생산량/총생산시간이 정확히 표시, `Y` 선택 시 `PRODUCING` + 큐 등록, `N` 선택 시 `RESERVED` 유지(거절과 다른 흐름, SPEC.md §4.2).
- 거절: 즉시 `REJECTED`, 이후 이 주문이 모니터링/생산라인/출고 어디에도 노출되지 않음(다음 Phase들에서 재확인).
- 목록이 비어있을 때 안내 메시지 확인.

## 완료 조건

- [x] `tests/test_order_service.py`, `tests/test_production_service.py`(enqueue 부분) 전체 통과.
- [x] 수동 시나리오(재고 충분/부족/거절)가 SPEC.md §4와 일치.

## 진행 기록

- `clock.py`: `NowFn` 타입과 `utc_now()`(timezone-aware) 기본 시간 소스 정의(NFR-4, DataMonitor DI 패턴).
- `services/production_service.py`(신규): `QueueItem` dataclass + `ProductionService.enqueue()` — 큐가 비어있던 상태에서 등록되는 첫 항목만 `started_at`을 즉시 설정하고, 그 외에는 `None`으로 두어 Phase 7의 `advance()`가 앞 항목 완료 시 다음 항목 `started_at`을 설정하도록 설계(ARCHITECTURE.md §4.2).
- `services/order_service.py` 확장: `ApprovalPreview` dataclass(`kind`=SUFFICIENT/SHORTAGE), `list_reserved_orders/preview_approval/confirm_approval/reject_order`. `OrderService` 생성자에 `production_service`를 3번째 인자로 추가(재고 부족 승인 시 큐 등록에 필요).
- `views/approval_view.py`, `controllers/approval_controller.py`: SPEC.md §4 흐름 그대로 — 번호 선택 후 1차 Y/N(Y=승인 분기, N=즉시 거절), 승인이 부족 케이스면 2차 Y/N(Y=PRODUCING+큐 등록, N=RESERVED 유지, 거절과는 다른 흐름).
- 수동 스모크 테스트 중 주문번호가 길어 표 컬럼이 밀리는 문제를 발견해 `approval_view.py`의 컬럼 폭을 조정(주문번호 20자 폭 등)했다 — 계획에 없던 사소한 표시 버그 수정.
- 테스트: `pytest tests/test_order_service.py tests/test_production_service.py -q` → 13 passed. 전체 스위트 `pytest -q` → 47 passed.
- 수동 시나리오: 재고 부족 케이스(승인→Y→Y)로 `PRODUCING` 전환 + 큐 등록(`queue length: 1`) 확인, 거절 케이스(N)로 즉시 `REJECTED` 전환 확인. 재고 충분 케이스는 자동 테스트로 커버.
