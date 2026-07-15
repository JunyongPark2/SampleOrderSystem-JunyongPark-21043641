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

- [ ] `python tools/dummy_data_cli.py --samples 12 --orders 36` 실행이 에러 없이 완료.
- [ ] 생성된 데이터로 `python main.py`의 모든 메뉴(1~6)를 한 번씩 순회했을 때 예외가 발생하지 않음.
