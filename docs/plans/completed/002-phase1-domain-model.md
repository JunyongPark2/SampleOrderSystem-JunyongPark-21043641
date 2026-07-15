# Phase 1: 도메인 모델 & 예외

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고.

## 목표

`Sample`, `Order`, `OrderStatus`와 공용 예외(`NotFoundError`, `DuplicateError`, `ValidationError`)를 정의해, 이후 모든 계층(Repository/Service)이 공유하는 타입 기반을 마련한다.

## 선행 조건

Phase 0(스캐폴딩) 완료.

## 작업 범위

- `models.py`에 `OrderStatus`(Enum: RESERVED/REJECTED/PRODUCING/CONFIRMED/RELEASE), `Sample`, `Order` dataclass 구현(PRD.md §4, §8).
- `exceptions.py`에 `NotFoundError(entity_name, entity_id)`, `DuplicateError(entity_name, entity_id)`, `ValidationError` 구현(ARCHITECTURE.md §6, DataPersistence 재사용 + 신규 `ValidationError`).

## 비작업 범위

- Repository/JsonFileStore 구현 — Phase 2에서 진행.
- 검증 로직(수량/수율 범위 등)의 실제 판정 — Phase 3~5의 Service 계층에서 구현. 여기서는 예외 타입만 정의한다.

## 수정하거나 생성할 파일

```
src/sampleorder/models.py
src/sampleorder/exceptions.py
tests/test_models.py
```

## 구현 단계

1. `OrderStatus` Enum 정의(문자열 값 그대로 PRD.md §4.3과 일치).
2. `Sample` dataclass: `sample_id: str, name: str, avg_production_time: float, yield_rate: float, stock: int = 0`.
3. `Order` dataclass: `order_id: str, sample_id: str, customer_name: str, quantity: int, status: OrderStatus = OrderStatus.RESERVED, created_at: str`.
4. `exceptions.py`에 3개 예외 클래스와 메시지 포맷 구현.

## 검증 방법

`pytest tests/test_models.py`가 통과하고, `python -c "from src.sampleorder.models import Sample, Order, OrderStatus"`가 에러 없이 import됨을 확인.

## 테스트 계획

- `Sample`/`Order` 기본값(`stock=0`, `status=RESERVED`) 확인.
- `OrderStatus`가 정확히 5개 값을 가지는지 확인.
- 각 예외의 `str()` 메시지에 `entity_name`/`entity_id`가 포함되는지 확인.

## 완료 조건

- [x] `tests/test_models.py` 전체 통과.
- [x] 이후 Phase에서 이 모델/예외를 그대로 import해 사용할 수 있음(수정 없이).

## 진행 기록

- `models.py`: `OrderStatus` Enum(5개 값), `Sample`/`Order` dataclass 구현.
- **PRD.md §8 예시 코드와의 차이**: PRD 스니펫은 `Order`에서 `status: OrderStatus = OrderStatus.RESERVED` 뒤에 기본값 없는 `created_at: str`을 두었는데, 이는 Python dataclass 규칙(기본값 없는 필드는 기본값 있는 필드보다 앞에 와야 함)을 위반해 그대로 옮기면 `TypeError`가 난다. `created_at`을 `status`보다 앞으로 옮겨 `status`만 기본값을 갖도록 재배치했다(필드 이름/타입/기본값 자체는 PRD와 동일, 순서만 조정). 사소한 오타 수준이라 PRD.md 수정 없이 이 기록으로 남긴다.
- `exceptions.py`: `NotFoundError(entity_name, entity_id)`, `DuplicateError(entity_name, entity_id)`, `ValidationError(message)` — 메시지에 두 값이 모두 포함되도록 구현.
- `tests/test_models.py` 6개 테스트(기본값, Enum 5개 값, 각 예외 메시지) 작성 및 통과 확인: `pytest tests/test_models.py -q` → 6 passed.
