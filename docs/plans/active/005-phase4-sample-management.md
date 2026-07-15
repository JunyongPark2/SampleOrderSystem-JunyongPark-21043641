# Phase 4: 시료 관리 (FR-1.1~1.3)

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고.

## 목표

시료 등록/조회/검색 기능을 Service–View–Controller 전 계층으로 완성해, 메뉴 `[1] 시료 관리`가 SPEC.md §2 예시 화면대로 동작하게 한다. 이 Phase에서 만드는 `formatting.py`(한글 폭 정렬)는 이후 모든 View가 공유한다.

## 선행 조건

Phase 2(영속성), Phase 3(계산 모듈, 직접 의존은 없지만 순서상 선행) 완료.

## 작업 범위

- `services/sample_service.py`: 등록 검증(`avg_production_time > 0`, `0 < yield_rate <= 1`) + 조회 + 이름 검색.
- `views/formatting.py`: 한글(전각 문자) 폭 정렬 유틸(DataMonitor `render.py`의 `_display_width`/`_ljust`/`_rjust` 이식, ARCHITECTURE.md §3).
- `views/sample_view.py`: 시료 등록/목록/검색 화면 입출력.
- `controllers/sample_controller.py`: 하위 메뉴 디스패치(`[1] 등록 [2] 목록 [3] 검색 [0] 뒤로`).

## 비작업 범위

- 주문/승인/생산/모니터링/출고 — 이후 Phase.
- 메인 메뉴 통합 — Phase 10.

## 수정하거나 생성할 파일

```
src/sampleorder/services/sample_service.py
src/sampleorder/views/formatting.py
src/sampleorder/views/sample_view.py
src/sampleorder/controllers/sample_controller.py
tests/test_sample_service.py
```

## 구현 단계

1. `formatting.py`: `_display_width(text)`(`unicodedata.east_asian_width` 기반), `ljust`/`rjust` 헬퍼 구현.
2. `sample_service.py`: `register(name, avg_production_time, yield_rate)` — 검증 실패 시 `ValidationError`(SPEC.md §2.2 문구 그대로), 성공 시 Repository에 위임.
3. `sample_service.py`: `list_all()`, `search(keyword)`(대소문자 무관 부분 문자열).
4. `sample_view.py`: 입력 순서(`name`→`avg_production_time`→`yield_rate`) 프롬프트, 검증 실패 시 해당 필드만 재입력 루프, 표 형식 출력(SPEC.md §2.3 컬럼: ID/시료명/평균 생산시간/수율/현재 재고).
5. `sample_controller.py`: 하위 메뉴 루프, 잘못된 번호 입력 시 SPEC.md §0 공통 문구 후 재표시.

## 검증 방법

- 자동: `pytest tests/test_sample_service.py`.
- 수동: `python main.py` → `[1] 시료 관리` 진입 → 등록/조회/검색 3개 기능이 SPEC.md §2 예시 화면과 동일한 문구·형식으로 동작.

## 테스트 계획

- `avg_production_time <= 0` → SPEC.md §2.2 오류 메시지, 등록 미진행.
- `yield_rate` 범위 밖(0, 음수, 1 초과) → 오류 메시지, 등록 미진행.
- 등록 성공 시 `stock == 0`, `sample_id` 순차 채번.
- `search`: 대소문자 무관, 부분 일치 없을 시 "일치하는 시료가 없습니다." 반환.

## 완료 조건

- [ ] `tests/test_sample_service.py` 전체 통과.
- [ ] 수동 시나리오(등록/조회/검색)가 SPEC.md §2 화면과 일치.
- [ ] `formatting.py`가 이후 Phase의 다른 View에서 재사용 가능한 형태(순수 함수, 콘솔 의존 없음).
