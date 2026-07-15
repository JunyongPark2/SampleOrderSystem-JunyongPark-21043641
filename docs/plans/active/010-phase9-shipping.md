# Phase 9: 출고 처리 (FR-6.1~6.2)

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고.

## 목표

`CONFIRMED` 상태 주문의 출고 처리(재고 차감 + 상태 전환)를 완성해 메뉴 `[6] 출고 처리`가 SPEC.md §7 예시 화면대로 동작하게 한다.

## 선행 조건

Phase 6(승인 — `CONFIRMED` 상태 주문 생성 경로 필요) 완료.

## 작업 범위

- `services/shipping_service.py`: `list_confirmed_orders()`, `release(order_id, now_fn)`(재고 차감, 상태 전환, 처리일시 기록).
- `views/shipping_view.py`, `controllers/shipping_controller.py` 구현.

## 비작업 범위

- 승인/생산/모니터링 — 이미 완료된 이전 Phase.
- 메인 메뉴 통합 — Phase 10.

## 수정하거나 생성할 파일

```
src/sampleorder/services/shipping_service.py
src/sampleorder/views/shipping_view.py
src/sampleorder/controllers/shipping_controller.py
tests/test_shipping_service.py
```

## 구현 단계

1. `list_confirmed_orders()`: `OrderRepository.list_by_status(CONFIRMED)`.
2. `release(order_id, now_fn)`: `SampleRepository.update(stock -= quantity)`, `OrderRepository.update(status=RELEASE)`, `processed_at=now_fn()` 반환(SPEC.md §7.2).
3. `shipping_view.py`: 목록 표시(SPEC.md §7.1), 선택 즉시 실행(Y/N 확인 없음), 결과 화면(SPEC.md §7.2).
4. `shipping_controller.py`: 목록 비어있을 시 안내 메시지(SPEC.md §7.1) 후 메인 메뉴 복귀.

## 검증 방법

- 자동: `pytest tests/test_shipping_service.py`.
- 수동: `python main.py` → `[6] 출고 처리` → SPEC.md §7 예시 화면과 일치 확인(Y/N 확인 없이 즉시 처리되는지 포함).

## 테스트 계획

- 출고 시 재고가 정확히 `quantity`만큼 차감되는지 확인.
- 상태가 `CONFIRMED → RELEASE`로 전환되는지 확인.
- 목록이 비어있을 때 "출고 가능한 주문이 없습니다." 메시지 확인.
- `CONFIRMED`가 아닌 주문(`RESERVED` 등)은 목록에 노출되지 않는지 확인.

## 완료 조건

- [ ] `tests/test_shipping_service.py` 전체 통과.
- [ ] 수동 시나리오가 SPEC.md §7과 일치.
