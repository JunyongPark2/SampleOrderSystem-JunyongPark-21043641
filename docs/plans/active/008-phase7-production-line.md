# Phase 7: 생산라인 FIFO 시뮬레이션 (FR-5.1, 5.3~5.5)

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고. ADR-0003(생산 진행 상태 갱신 방식), ARCHITECTURE.md §4.2 시퀀스 근거.

## 목표

`production_service.py`의 `advance(now_fn)`(완료 처리), 현재 처리 중 항목의 진행률/완료 예정 시각, FIFO 대기 큐 표시까지 완성해 메뉴 `[5] 생산라인 조회`를 SPEC.md §6 예시 화면대로 동작시킨다.

## 선행 조건

Phase 6(주문 승인 + `production_service.enqueue`) 완료.

## 작업 범위

- `clock.py`: `now_fn` 기본값(`datetime.utcnow` 등) 정의, DataMonitor `clock_now` DI 패턴 재사용.
- `production_service.py`(기존 파일 확장): `advance(now_fn)`(큐 맨 앞 완료 처리 루프), `current_item(now_fn)`(진행률/완료 예정 시각), `pending_queue()`(대기 큐, 누적 완료 시각 계산).
- `views/production_view.py`, `controllers/production_controller.py` 구현.

## 비작업 범위

- 모니터링/출고 — Phase 8, 9.
- 메인 메뉴에서 `advance()`를 호출하는 통합 지점 — Phase 10(각 메뉴 진입 지점 연결).

## 수정하거나 생성할 파일

```
src/sampleorder/clock.py
src/sampleorder/services/production_service.py   (확장)
src/sampleorder/views/production_view.py
src/sampleorder/controllers/production_controller.py
tests/test_production_service.py                  (완료 처리/진행률 케이스 추가)
```

## 구현 단계

1. `clock.py`: `now_fn: Callable[[], datetime] = datetime.utcnow` 타입/기본값 정의.
2. `advance(now_fn)`: `while queue and elapsed(queue[0], now_fn()) >= queue[0].total_time:` 루프 — `SampleRepository.update(stock += actual_yield)`, `OrderRepository.update(status=CONFIRMED)`, `queue.popleft()`, 다음 항목 `started_at = now_fn()` 재설정(ARCHITECTURE.md §4.2).
3. `current_item(now_fn)`: `진행률 = min(1.0, 경과시간/총생산시간)`, `완료_예정_시각 = 시작_시각 + 총생산시간`(SPEC.md §6.1 공식).
4. `pending_queue()`: FIFO 순서대로, 각 항목의 "예상 완료"는 앞선 모든 항목의 총생산시간 누적 + 자신의 총생산시간(SPEC.md §6.3).
5. `production_view.py`: 현재 처리 중(진행률 바, 완료 예정 시각) + 대기 큐 표(순번/주문번호/시료명/주문량/부족분/실생산량/예상 완료) 출력(SPEC.md §6).
6. `production_controller.py`: 메뉴 진입 시 반드시 `production_service.advance(now_fn())` 먼저 호출 후 화면 표시.

## 검증 방법

- 자동: `pytest tests/test_production_service.py`.
- 수동: `python main.py` → `[5] 생산라인 조회` → SPEC.md §6 예시 화면(현재 처리 중 + 대기 큐)과 형식 일치 확인. 고정 `now_fn`을 임시로 주입해 진행률 계산이 의도대로 나오는지 확인 후 되돌림.

## 테스트 계획

- 경과시간 < 총생산시간: `advance()` 호출해도 상태 변화 없음, 큐 그대로 유지.
- 경과시간 >= 총생산시간: 재고 증가, 주문 `PRODUCING → CONFIRMED`, 큐에서 제거, 다음 항목 `started_at` 갱신.
- 여러 항목이 동시에 완료 조건을 만족하는 경우(오랫동안 메뉴 미진입 시뮬레이션): `while` 루프가 모두 처리하는지 확인.
- 진행률: 0%, 50%, 100%(이상 시 1.0으로 클램프) 경계값.
- 대기 큐의 "예상 완료" 누적 계산이 FIFO 순서와 일치하는지 확인.

## 완료 조건

- [ ] `tests/test_production_service.py` 전체 통과(enqueue + advance + 진행률 + 대기 큐).
- [ ] 수동 시나리오가 SPEC.md §6과 일치.
- [ ] `now_fn`을 교체하는 것만으로 테스트에서 시간 흐름을 결정론적으로 재현 가능함을 확인(NFR-4).
