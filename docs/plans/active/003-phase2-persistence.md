# Phase 2: 영속성 계층 (JsonFileStore + Repository)

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고. ADR-0001(JSON 파일 기반 영속성) 근거.

## 목표

원자적 JSON 파일 읽기/쓰기(`JsonFileStore`)와 그 위에 얹는 `SampleRepository`/`OrderRepository`(CRUD + ID 채번)를 구현해, 이후 Service 계층이 데이터를 영속화할 수 있게 한다.

## 선행 조건

Phase 1(도메인 모델 & 예외) 완료.

## 작업 범위

- `json_store.py`: `JsonFileStore` — `load()`(파일 없으면 `[]`), `save()`(임시 파일에 쓴 뒤 `os.replace()`로 원자적 치환).
- `repositories/sample_repository.py`: `create/get/list_all/search/update/delete`, `sample_id` 자동 채번(`S-001`...).
- `repositories/order_repository.py`: `create/get/list_all/list_by_status/update/delete`, `order_id` 자동 채번(`ORD-YYYYMMDD-NNNN`, 해당 날짜 내 순번).
- `tests/conftest.py`: `tmp_path` 기반 fixture로 실제 `data/`를 훼손하지 않는 테스트 환경 구성(NFR-8).

## 비작업 범위

- 계산 로직, 검증 로직 — Repository는 순수 CRUD만 담당.
- Service 계층 — Phase 3 이후.

## 수정하거나 생성할 파일

```
src/sampleorder/json_store.py
src/sampleorder/repositories/sample_repository.py
src/sampleorder/repositories/order_repository.py
tests/conftest.py
tests/test_json_store.py
tests/test_sample_repository.py
tests/test_order_repository.py
```

## 구현 단계

1. `JsonFileStore(path)` 구현: `save(records)`는 `path.with_suffix(".tmp")`에 쓰고 `os.replace()`, `load()`는 파일 미존재 시 `[]` 반환.
2. `SampleRepository(store)` 구현: `create(name, avg_production_time, yield_rate)` 시 `stock=0`으로 초기화, `sample_id`는 `list_all()` 길이 기준 채번.
3. `OrderRepository(store)` 구현: `create(sample_id, customer_name, quantity)` 시 `_next_id(date)`로 해당 날짜 내 최대 순번+1 채번, `list_by_status(status)` 필터 구현.
4. `conftest.py`에 `tmp_path`로 격리된 `JsonFileStore` 인스턴스를 만드는 fixture 작성.

## 검증 방법

`pytest tests/test_json_store.py tests/test_sample_repository.py tests/test_order_repository.py` 전체 통과. 테스트 실행 후 실제 저장소의 `data/` 디렉터리가 변경되지 않았음을 `git status`로 확인.

## 테스트 계획

- `JsonFileStore`: 저장 후 재로드 시 데이터 일치, 쓰기 후 `.tmp` 파일이 남지 않음, 파일 없을 때 `load()`가 `[]` 반환.
- `SampleRepository`: 등록 시 `stock=0` 초기화, 순차 채번(`S-001`, `S-002`...), `search`(부분 문자열/대소문자 무관).
- `OrderRepository`: 같은 날짜 내 2건 이상 연속 생성 시 순번 증가(`-0001`, `-0002`), 날짜가 다르면 순번이 1부터 다시 시작, `list_by_status`가 정확히 필터링.

## 완료 조건

- [ ] 세 테스트 파일 전체 통과.
- [ ] 동시성/락 처리는 의도적으로 구현하지 않았음을 코드 주석이 아닌 이 문서로 남김(ADR-0001 참고).
