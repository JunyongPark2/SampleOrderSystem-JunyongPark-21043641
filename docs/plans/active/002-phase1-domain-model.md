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

- [ ] `tests/test_models.py` 전체 통과.
- [ ] 이후 Phase에서 이 모델/예외를 그대로 import해 사용할 수 있음(수정 없이).
