# Phase 8: 모니터링 (FR-4.1~4.2)

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고.

## 목표

상태별 주문 건수 집계와 시료별 재고 상태 판정 기능을 완성해 메뉴 `[4] 모니터링`이 SPEC.md §5 예시 화면대로 동작하게 한다.

## 선행 조건

Phase 3(계산 모듈 — `pending_demand`, `stock_status` 재사용), Phase 6(승인/거절로 다양한 상태의 주문이 존재해야 의미 있는 검증 가능) 완료.

## 작업 범위

- `services/monitoring_service.py`: `order_status_counts()`(RESERVED/CONFIRMED/PRODUCING/RELEASE 집계, REJECTED 제외), `stock_report()`(시료별 재고 + 상태, `calculations.pending_demand`/`stock_status` 재사용).
- `views/monitoring_view.py`, `controllers/monitoring_controller.py` 구현(하위 메뉴: `[1] 주문량 확인 [2] 재고량 확인 [0] 뒤로`).

## 비작업 범위

- 출고 처리 — Phase 9.
- 메인 메뉴 요약 정보 계산(생산라인 대기 건수 등) — Phase 10에서 재사용.

## 수정하거나 생성할 파일

```
src/sampleorder/services/monitoring_service.py
src/sampleorder/views/monitoring_view.py
src/sampleorder/controllers/monitoring_controller.py
tests/test_monitoring_service.py
```

## 구현 단계

1. `order_status_counts()`: `OrderRepository.list_all()`에서 REJECTED를 제외하고 나머지 4개 상태별 개수 집계(SPEC.md §5.2).
2. `stock_report()`: `SampleRepository.list_all()` 각 시료에 대해 `calculations.pending_demand(orders, sample_id)` → `calculations.stock_status(stock, pending_demand)` 호출, 결과 리스트 반환.
3. `monitoring_view.py`: SPEC.md §5.2/5.3 표 형식 출력.
4. `monitoring_controller.py`: 하위 메뉴 디스패치.

## 검증 방법

- 자동: `pytest tests/test_monitoring_service.py`.
- 수동: `python main.py` → `[4] 모니터링` → 두 하위 메뉴 모두 SPEC.md §5 예시 화면과 일치 확인.

## 테스트 계획

- `order_status_counts()`: REJECTED 상태 주문이 있어도 집계에서 제외됨을 확인.
- `stock_report()`: 고갈(`stock<=0`)/부족(`stock<pending_demand`)/여유(그 외) 3구간이 정확히 판정됨을 확인, 특히 `RESERVED+PRODUCING+CONFIRMED`만 대기 수요에 포함되고 `REJECTED`/`RELEASE`는 제외됨을 확인.

## 완료 조건

- [ ] `tests/test_monitoring_service.py` 전체 통과.
- [ ] 수동 시나리오가 SPEC.md §5와 일치.
- [ ] `monitoring_service.py`가 `calculations.py`의 함수만 재사용하고 판정 로직을 자체 재구현하지 않음.
