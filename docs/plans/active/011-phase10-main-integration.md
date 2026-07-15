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

- [ ] `tests/test_main_controller_smoke.py` 전체 통과.
- [ ] `python main.py`로 전체 메뉴가 예외 없이 동작.
- [ ] 메뉴 4/5/6 어디로 진입하든 생산 상태가 동일하게 최신 반영됨(수동 확인).
