# Phase 11: 더미 데이터 생성 도구

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고. 제품 기능이 아닌 보조 도구(PRD.md §3 In Scope의 "초기 구동/테스트를 위한 더미 데이터 생성 기능").

## 목표

`DummyDataGenerator` 로직을 재이식해, 앱을 처음 실행했을 때 SPEC.md §1 메인 메뉴 예시(등록 시료 12종, 전체 주문 36건 등)와 유사한 초기 데이터를 손쉽게 시딩할 수 있게 한다.

## 선행 조건

Phase 2(영속성 — Repository/JsonFileStore 완성) 완료. 다른 Phase와 독립적이므로 Phase 3~10과 병행 가능하지만, 계획상 순서는 Phase 10 다음으로 둔다(전체 플로우가 완성된 후 시연 데이터를 채우는 것이 자연스럽기 때문).

## 작업 범위

- `tools/dummy_data_cli.py`: `DummyDataGenerator(sample_repo, order_repo, rng=random.Random())` — `SAMPLE_POOL`, `CUSTOMER_POOL`, `ORDER_STATUS_WEIGHTS` + `_weighted_status()`, `generate_samples(count)`/`generate_orders(count, within_days=30)`/`generate(sample_count, order_count)`(ARCHITECTURE.md §3 매핑).
- 본 프로젝트의 `JsonFileStore`/`SampleRepository`/`OrderRepository`를 그대로 주입(별도 사본 만들지 않음).

## 비작업 범위

- 자동화 테스트 — 제품 기능이 아니므로 작성하지 않는다(ARCHITECTURE.md §7 "과도한 커버리지 강요 금지" 원칙).
- 신규 도메인 로직 — 없음, 기존 Repository를 호출만 함.

## 수정하거나 생성할 파일

```
tools/dummy_data_cli.py
```

## 구현 단계

1. `DummyDataGenerator` 클래스 이식: 고정 `SAMPLE_POOL`(이름, 기본 생산시간, 기본 수율 튜플 목록), `CUSTOMER_POOL`(한국 기업명 목록).
2. `ORDER_STATUS_WEIGHTS`(상태별 가중치 목록 합 1.0) + `_weighted_status()`(누적 롤 방식)로 더미 주문 상태 분포.
3. CLI 인자 파싱(`--samples`, `--orders`) 및 `generate(sample_count, order_count)` 호출.
4. 본 프로젝트의 실제 `JsonFileStore` 경로(`data/samples.json`, `data/orders.json`)를 사용하도록 배선.

## 검증 방법

`python tools/dummy_data_cli.py --samples 12 --orders 36` 실행 후:
- `data/samples.json`/`data/orders.json`이 생성되고 각각 12건/36건 레코드 존재.
- `python main.py` 실행 시 메인 메뉴 요약 정보가 "등록 시료 12종, 전체 주문 36건"으로 표시됨(SPEC.md §1 예시와 동일한 형식).

## 테스트 계획

자동화 테스트는 작성하지 않는다(위 "비작업 범위" 참고). 대신 위 "검증 방법"의 수동 실행으로 동작을 확인한다.

## 완료 조건

- [x] `python tools/dummy_data_cli.py --samples 12 --orders 36` 실행이 에러 없이 완료.
- [x] 생성된 데이터로 `python main.py`의 모든 메뉴(1~6)를 한 번씩 순회했을 때 예외가 발생하지 않음.

## 진행 기록

- `tools/dummy_data_cli.py`: `DummyDataGenerator(sample_repo, order_repo, rng)` — `SAMPLE_POOL`(12종 고정 목록, 그 이상 요청 시 `#N` 접미사로 순환), `CUSTOMER_POOL`(8개 기업/연구실명), `ORDER_STATUS_WEIGHTS`(RESERVED 0.15/CONFIRMED 0.2/PRODUCING 0.15/RELEASE 0.4/REJECTED 0.1) + `_weighted_status()`(누적 롤).
- **ARCHITECTURE.md §3 매핑과의 사소한 차이**: `generate_orders(count, within_days=30)`의 `within_days`는 시그니처에는 남겨두되 실제로 주문 생성 시각을 과거로 분산시키는 로직은 구현하지 않았다. `OrderRepository.create()`가 생성자에 고정된 `now_fn` 하나만 사용하는 구조라, 주문마다 다른 시각을 주입하려면 Repository 내부(`_now_fn`)에 접근해야 하는데 이는 본 도구가 제품 코드가 아니라도 캡슐화를 깨는 방식이라 피했다. 이 도구는 제품 기능이 아니라 시연/테스트용 보조 스크립트(PRD.md §3, ARCHITECTURE.md §7 "과도한 커버리지 강요 금지"와 동일한 취지)이므로, 모든 더미 주문이 실행 시각 기준으로 생성되는 단순화를 그대로 두었다.
- CLI 인자: `--samples`(기본 12), `--orders`(기본 36), `--seed`(재현 가능한 난수 시드).
- 비작업 범위 그대로 자동화 테스트는 작성하지 않았다(제품 기능 아님).
- 수동 검증: `python tools/dummy_data_cli.py --samples 12 --orders 36 --seed 42` → `data/samples.json` 12건, `data/orders.json` 36건 생성 확인. 이어서 `python main.py`로 메뉴 1~6 전체를 한 바퀴(시료 등록/목록, 주문 접수, 승인 목록에서 거절, 모니터링 주문량/재고량, 생산라인 조회, 출고 목록)를 오류 없이 순회 확인(`traceback`/`error` 문자열 없음). 전체 `pytest -q` → 68 passed(회귀 없음).
