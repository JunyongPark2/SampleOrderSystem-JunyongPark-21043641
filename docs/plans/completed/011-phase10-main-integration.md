# Phase 10: 메인 메뉴 통합 및 진입점

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고. ADR-0003 후속 영향(진입 지점마다 `advance()` 호출 누락 위험) 주의.

## 목표

지금까지 만든 모든 하위 컨트롤러(시료/주문/승인/생산/모니터링/출고)를 `MainController`에 연결하고, `main.py`에서 전체 의존성을 조립해 애플리케이션을 처음부터 끝까지 실행 가능하게 만든다. 이 Phase 완료 시점이 PRD.md §9 인수 기준을 처음으로 end-to-end 재현할 수 있는 지점이다.

## 선행 조건

Phase 4~9(모든 하위 기능) 완료.

## 작업 범위

- `controllers/main_controller.py`: ConsoleMVC `MainController` 패턴(메뉴 키 → 하위 컨트롤러 메서드 딕셔너리, `run()` 루프, 잘못된 입력 처리).
- `views/main_view.py`: 요약 정보(등록 시료 종수/총 재고/전체 주문 건수/생산라인 대기 건수, SPEC.md §1) 표시.
- `main.py`: `build_main_controller()` — 모든 Repository/Service/Controller 조립 후 `run()` 호출.
- 메뉴 4/5/6 진입 지점(및 필요 시 메인 메뉴 자체)에서 `production_service.advance(now_fn())`를 먼저 호출하도록 연결(ADR-0003).

## 비작업 범위

- 신규 비즈니스 로직 없음 — 순수 조립/배선(wiring) 작업.
- 더미 데이터 생성 — Phase 11.

## 수정하거나 생성할 파일

```
src/sampleorder/controllers/main_controller.py
src/sampleorder/views/main_view.py
main.py                                          (완성)
tests/test_main_controller_smoke.py
```

## 구현 단계

1. `main_view.py`: 요약 정보 계산은 Service에 위임(직접 계산 금지 — ARCHITECTURE.md 계층 원칙), 화면 출력만 담당.
2. `main_controller.py`: `self._actions = {"1": sample_controller.handle, "2": order_controller.handle, ...}`, `run()` 루프에서 `"0"` 종료, 미등록 키는 SPEC.md §0 공통 문구.
3. 메뉴 4/5/6에 해당하는 컨트롤러 진입 직전에 `production_service.advance(now_fn())` 호출 지점을 명시적으로 배치(각 하위 컨트롤러 내부 또는 `main_controller`의 디스패치 래퍼에서 — 택1 후 이 문서에 실제 위치를 기록).
4. `main.py`: `JsonFileStore` 2개(샘플/주문) 생성 → Repository 2개 → Service 5개 → View/Controller 조립 → `MainController(...).run()`.

## 검증 방법

- 자동: `pytest tests/test_main_controller_smoke.py`.
- 수동: `python main.py`로 메뉴 1~6, 0을 한 바퀴 수동 조작. 이 시점에 PRD.md §9 인수 기준 10개 항목을 전부 한 번씩 수동으로 재현해본다(정식 체크는 Phase 12에서 문서화).

## 테스트 계획

- 스모크 테스트: 각 메뉴 키 입력 시 대응하는 하위 컨트롤러의 `handle`(또는 동등 메서드)이 정확히 1회 호출되는지 확인(mock/stub 컨트롤러 사용).
- 잘못된 메뉴 번호 입력 시 예외 없이 안내 메시지 후 같은 메뉴 재표시.
- 메뉴 4/5/6 진입 시 `production_service.advance()`가 호출되는지 확인(spy/mock으로 호출 여부만 검증, 결과값은 Phase 7에서 이미 검증했으므로 재검증하지 않음).

## 완료 조건

- [x] `tests/test_main_controller_smoke.py` 전체 통과.
- [x] `python main.py`로 전체 메뉴가 예외 없이 동작.
- [x] 메뉴 4/5/6 어디로 진입하든 생산 상태가 동일하게 최신 반영됨(수동 확인).

## 진행 기록

- `views/main_view.py`: SPEC.md §1 형식의 요약 화면(등록 시료 종수/총 재고/전체 주문 건수/생산라인 대기 건수).
- `services/monitoring_service.py`에 `DashboardSummary`/`dashboard_summary()` 추가 — 메인 메뉴 요약 계산도 Service에 위임(ARCHITECTURE.md 계층 원칙 준수, Controller가 직접 계산하지 않음).
- `services/order_service.py`에 `list_all_orders()` 추가(SPEC.md §1 "전체 주문 건수 — REJECTED 포함" 계산에 필요).
- `controllers/main_controller.py`: 메뉴 키 → 컨트롤러 `run` 딕셔너리 디스패치. `production_service.advance(now_fn())` 호출 위치는 (1) 메뉴 `[5]` 생산라인 조회는 `ProductionController.run()` 내부에서 이미 Phase 7에서 호출하도록 구현되어 있어 그대로 재사용하고, (2) 메뉴 `[4]` 모니터링/`[6]` 출고는 `MainController`가 해당 컨트롤러 실행 직전에 래퍼 함수(`_enter_monitoring`/`_enter_shipping`)로 감싸 `advance()`를 먼저 호출하도록 배치했다(ADR-0003 "메뉴 진입 시 갱신" 요구사항, 위치는 이 문서에 기록).
- `main.py`: `build_main_controller()`에서 Repository 2개 → Service 5개 → View/Controller 7개를 조립해 `MainController(...).run()`을 실행하도록 완성.
- 테스트: `tests/test_main_controller_smoke.py` 8개(메뉴 1~6 각각 해당 컨트롤러만 호출, 잘못된 번호 시 재표시, 메뉴 4 진입 시 `advance()` 발동 확인) 작성 및 통과. 전체 `pytest -q` → 68 passed.
- 수동 시나리오: `python main.py`로 시료 등록→목록→주문 접수→재고 부족 승인(PRODUCING 전환)→모니터링(주문량 확인)→생산라인 조회(진행률 0%)→종료까지 한 바퀴, 이어서 재실행해 출고 메뉴(빈 목록 메시지)까지 확인. `data/samples.json`/`data/orders.json`에 등록한 시료·주문이 정확히 저장됨을 확인(NFR-1 영속성 1차 확인, 정식 재현은 Phase 12).

## 발견한 제약사항 (중요 — Phase 12에서 재확인 필요)

수동 재현 중 다음 한계를 발견했다: **생산라인 큐(`ProductionService._queue`)는 메모리에만 존재하고 JSON으로 영속화되지 않는다.** `orders.json`에는 `PRODUCING` 상태가 그대로 남지만, 앱을 재시작하면 큐 자체(부족분/실생산량/총생산시간/시작 시각)는 사라져 해당 주문은 이후 `advance()`가 아무리 호출되어도 영원히 `PRODUCING`에 머무른다(재현: 승인으로 PRODUCING 전환 → 앱 재시작 → 생산라인 대기 건수가 0으로 표시됨).

- PRD.md NFR-1("애플리케이션 종료 후에도 데이터가 유지되어야 하며 재시작 시 이전 상태를 그대로 복원")과 ARCHITECTURE.md §5(저장 파일이 `samples.json`/`orders.json` 2개뿐, 큐 상태 저장 언급 없음) 사이의 간극이다.
- Phase 10은 "신규 비즈니스 로직 없음 — 순수 조립/배선 작업"으로 비작업 범위가 명시되어 있어, 이번 Phase에서 큐 재구성 로직(예: 시작 시 `PRODUCING` 주문을 스캔해 큐를 복원)을 임의로 추가하지 않았다.
- Phase 12(통합 검증)에서 PRD.md §9 인수 기준 재현 시 이 문제가 실제로 인수 기준을 위반하는지(현재 재고 증가 자체는 발생하지 않을 뿐, 데이터 손상은 아님) 확인하고, 필요하면 그 시점에 최소 범위의 복구 로직 추가 여부를 사용자에게 확인한다.
