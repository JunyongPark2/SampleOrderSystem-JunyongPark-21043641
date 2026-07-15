# 시료 등록 시 재고(stock) 수동 입력 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 시료 등록 시 `stock`을 항상 `0`으로 초기화하던 것을 사용자가 직접 입력하도록 바꾼다. 입력값은 `0` 이상의 정수여야 하며, 잘못된 입력은 재입력을 요구한다.

**Architecture:** 기존 `avg_production_time`/`yield_rate` 검증 패턴(Service에 `validate_*` 메서드, Controller에 `_prompt_*` 재입력 루프)을 그대로 따르고, 주문 수량(`quantity`) 검증에 쓰인 `isinstance(x, int) and not isinstance(x, bool)` 가드를 재사용한다. `SampleRepository.create()`와 `SampleService.register()`는 `stock` 파라미터를 **기본값 `0`을 가진 키워드 인자**로 추가한다 — 테스트/더미데이터 도구(`tools/dummy_data_cli.py`)의 기존 3-인자 호출부 30여 곳이 `create()` 후 `update(sample_id, stock=...)`로 재고를 별도 설정하는 패턴에 의존하고 있으므로, 필수 인자로 바꾸면 전부 깨진다.

**Tech Stack:** Python (dataclass, pytest), 기존 ConsoleMVC 계층 구조(Controller/Service/Repository/View) 그대로 사용.

## Global Constraints

- 재고 입력값은 `0` 이상의 정수만 허용한다 (사용자 지정).
- 검증 실패 메시지: `재고는 0 이상의 정수여야 합니다. 다시 입력해주세요.` (사용자 확정 문구).
- 입력 순서: `name` → `avg_production_time` → `yield_rate` → `stock` (사용자 확정, 기존 순서 뒤에 추가).
- `SampleRepository.create()` / `SampleService.register()`의 `stock` 파라미터는 기존 호출부 호환을 위해 기본값 `0`을 가진 키워드 인자로 추가한다 (하드코딩된 `stock=0` 대입을 파라미터로 바꾸는 것이지, 필수 인자로 만드는 것이 아니다).
- `docs/PRD.md`, `docs/SPEC.md`를 이번 변경에 맞게 갱신한다 (`docs/ARCHITECTURE.md`, ADR은 이번 변경과 무관하므로 수정하지 않는다).

---

### Task 1: Service 계층 — `validate_stock` 추가 및 `register()`에 `stock` 파라미터 연결

**Files:**
- Modify: `src/sampleorder/services/sample_service.py`
- Test: `tests/test_sample_service.py`

**Interfaces:**
- Consumes: 없음 (기존 `ValidationError`, `Sample`, `SampleRepository`만 사용).
- Produces: `SampleService.STOCK_ERROR: str` (모듈 상수), `SampleService.validate_stock(stock) -> int`, `SampleService.register(name: str, avg_production_time: float, yield_rate: float, stock: int = 0) -> Sample`.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_sample_service.py`의 import 문을 갱신하고 아래 테스트들을 추가한다.

```python
import pytest

from sampleorder.exceptions import ValidationError
from sampleorder.services.sample_service import (
    AVG_PRODUCTION_TIME_ERROR,
    STOCK_ERROR,
    YIELD_RATE_ERROR,
    SampleService,
)


@pytest.fixture
def sample_service(sample_repository):
    return SampleService(sample_repository)


def test_register_rejects_non_positive_avg_production_time(sample_service):
    with pytest.raises(ValidationError) as excinfo:
        sample_service.register("A", 0, 0.9, 10)
    assert str(excinfo.value) == AVG_PRODUCTION_TIME_ERROR
    assert sample_service.list_all() == []


def test_register_rejects_yield_rate_out_of_range(sample_service):
    for invalid_rate in (0, -0.1, 1.1):
        with pytest.raises(ValidationError) as excinfo:
            sample_service.register("A", 0.5, invalid_rate, 10)
        assert str(excinfo.value) == YIELD_RATE_ERROR
    assert sample_service.list_all() == []


def test_register_rejects_invalid_stock(sample_service):
    for invalid_stock in (-1, 1.5, "10", True):
        with pytest.raises(ValidationError) as excinfo:
            sample_service.register("A", 0.5, 0.9, invalid_stock)
        assert str(excinfo.value) == STOCK_ERROR
    assert sample_service.list_all() == []


def test_register_succeeds_with_user_supplied_stock_and_sequential_ids(sample_service):
    first = sample_service.register("A", 0.5, 0.9, 25)
    second = sample_service.register("B", 0.3, 0.8, 0)
    assert first.stock == 25
    assert second.stock == 0
    assert first.sample_id == "S-001"
    assert second.sample_id == "S-002"


def test_search_is_case_insensitive_substring(sample_service):
    sample_service.register("GaN 에피택셜", 0.3, 0.8, 5)
    results = sample_service.search("gan")
    assert len(results) == 1


def test_search_returns_empty_list_when_no_match(sample_service):
    sample_service.register("A", 0.5, 0.9, 5)
    assert sample_service.search("존재하지않음") == []
```

기존 `test_register_succeeds_with_stock_zero_and_sequential_ids` 테스트는 위 `test_register_succeeds_with_user_supplied_stock_and_sequential_ids`로 대체하므로 삭제한다.

- [ ] **Step 2: 테스트 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_sample_service.py -v`
Expected: `STOCK_ERROR` import 자체가 실패 (`ImportError`), 또는 `register()`가 4번째 위치 인자를 받지 않아 `TypeError`.

- [ ] **Step 3: 최소 구현 작성**

`src/sampleorder/services/sample_service.py` 전체를 아래로 교체한다.

```python
from sampleorder.exceptions import ValidationError
from sampleorder.models import Sample
from sampleorder.repositories.sample_repository import SampleRepository

AVG_PRODUCTION_TIME_ERROR = "평균 생산시간은 0보다 커야 합니다. 다시 입력해주세요."
YIELD_RATE_ERROR = "수율은 0 초과 1 이하 값이어야 합니다. 다시 입력해주세요."
STOCK_ERROR = "재고는 0 이상의 정수여야 합니다. 다시 입력해주세요."


class SampleService:
    def __init__(self, repository: SampleRepository):
        self._repo = repository

    def validate_avg_production_time(self, avg_production_time: float) -> float:
        if avg_production_time <= 0:
            raise ValidationError(AVG_PRODUCTION_TIME_ERROR)
        return avg_production_time

    def validate_yield_rate(self, yield_rate: float) -> float:
        if not (0 < yield_rate <= 1):
            raise ValidationError(YIELD_RATE_ERROR)
        return yield_rate

    def validate_stock(self, stock) -> int:
        if not isinstance(stock, int) or isinstance(stock, bool) or stock < 0:
            raise ValidationError(STOCK_ERROR)
        return stock

    def register(
        self, name: str, avg_production_time: float, yield_rate: float, stock: int = 0
    ) -> Sample:
        self.validate_avg_production_time(avg_production_time)
        self.validate_yield_rate(yield_rate)
        self.validate_stock(stock)
        return self._repo.create(name, avg_production_time, yield_rate, stock=stock)

    def list_all(self) -> list:
        return self._repo.list_all()

    def search(self, keyword: str) -> list:
        return self._repo.search(keyword)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_sample_service.py -v`
Expected: 전부 PASS (Task 2를 완료해야 `register()`가 실제로 `stock`을 반영한다 — Task 2 완료 후 다시 실행해서 최종 확인).

- [ ] **Step 5: 커밋**

Task 2까지 완료한 뒤 함께 커밋한다 (아래 Task 2 Step 5 참고).

---

### Task 2: Repository 계층 — `create()`에 `stock` 파라미터 추가

**Files:**
- Modify: `src/sampleorder/repositories/sample_repository.py:33-44`
- Test: `tests/test_sample_repository.py`

**Interfaces:**
- Consumes: 없음.
- Produces: `SampleRepository.create(name: str, avg_production_time: float, yield_rate: float, stock: int = 0) -> Sample`.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_sample_repository.py`의 `test_create_initializes_stock_to_zero`를 아래로 교체한다.

```python
def test_create_defaults_stock_to_zero_when_omitted(sample_repository):
    sample = sample_repository.create("실리콘 웨이퍼", 0.5, 0.9)
    assert sample.stock == 0


def test_create_uses_given_stock_value(sample_repository):
    sample = sample_repository.create("실리콘 웨이퍼", 0.5, 0.9, stock=42)
    assert sample.stock == 42
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_sample_repository.py -v`
Expected: `test_create_uses_given_stock_value`이 `TypeError: create() got an unexpected keyword argument 'stock'`로 FAIL, 나머지는 PASS.

- [ ] **Step 3: 최소 구현 작성**

`src/sampleorder/repositories/sample_repository.py:33-44`의 `create()`를 아래로 교체한다 (다른 부분은 변경하지 않는다).

```python
    def create(
        self, name: str, avg_production_time: float, yield_rate: float, stock: int = 0
    ) -> Sample:
        records = self._store.load()
        sample = Sample(
            sample_id=self._next_id(records),
            name=name,
            avg_production_time=avg_production_time,
            yield_rate=yield_rate,
            stock=stock,
        )
        records.append(_to_dict(sample))
        self._store.save(records)
        return sample
```

- [ ] **Step 4: 전체 테스트 통과 확인**

Run: `.venv/bin/python -m pytest -q`
Expected: 전체 스위트 통과 (기존 30여 곳의 `sample_repository.create(name, avg, yield_rate)` 3-인자 호출부가 `stock` 기본값 `0`으로 그대로 동작함을 확인 — `tests/test_monitoring_service.py`, `tests/test_order_service.py`, `tests/test_production_service.py`, `tests/test_shipping_service.py`, `tests/test_main_controller_smoke.py` 포함).

- [ ] **Step 5: 커밋**

```bash
git add src/sampleorder/services/sample_service.py src/sampleorder/repositories/sample_repository.py tests/test_sample_service.py tests/test_sample_repository.py
git commit -m "feat: allow user-supplied stock on sample registration (service/repository)"
```

---

### Task 3: Controller 계층 — `stock` 입력 프롬프트 연결

**Files:**
- Modify: `src/sampleorder/controllers/sample_controller.py`

**Interfaces:**
- Consumes: `SampleService.validate_stock(stock) -> int`, `SampleService.register(name, avg_production_time, yield_rate, stock) -> Sample` (Task 1에서 정의), `SampleView.prompt_avg_production_time() -> str` 등 기존 View 메서드.
- Produces: `SampleController._prompt_stock() -> int` (내부 메서드, 다른 태스크가 의존하지 않음).

이 프로젝트에는 `SampleController`를 직접 실행하는 자동화 테스트가 없다(`tests/test_main_controller_smoke.py`는 `MainController`의 디스패치만 mock recorder로 검증하며 `SampleController.run()`을 실제로 실행하지 않는다). 따라서 이 태스크는 Step 4의 수동 CLI 검증으로 완료를 확인한다.

- [ ] **Step 1: View에 재고 입력 프롬프트 추가**

`src/sampleorder/views/sample_view.py`의 `prompt_yield_rate` 메서드(27번째 줄) 바로 다음에 추가한다.

```python
    def prompt_stock(self) -> str:
        return input("재고(ea) > ").strip()
```

- [ ] **Step 2: Controller에 `_prompt_stock` 추가 및 `_register` 연결**

`src/sampleorder/controllers/sample_controller.py`의 `_register`와 `_prompt_yield_rate`를 아래로 교체한다 (그 외 메서드는 변경하지 않는다).

```python
    def _register(self) -> None:
        name = self._view.prompt_name()
        avg_production_time = self._prompt_avg_production_time()
        yield_rate = self._prompt_yield_rate()
        stock = self._prompt_stock()
        sample = self._service.register(name, avg_production_time, yield_rate, stock)
        self._view.show_registration_result(sample)
```

```python
    def _prompt_yield_rate(self) -> float:
        while True:
            raw = self._view.prompt_yield_rate()
            try:
                value = float(raw)
                self._service.validate_yield_rate(value)
                return value
            except (ValueError, ValidationError) as error:
                self._view.show_validation_error(self._error_message(error))

    def _prompt_stock(self) -> int:
        while True:
            raw = self._view.prompt_stock()
            try:
                value = int(raw)
                self._service.validate_stock(value)
                return value
            except (ValueError, ValidationError) as error:
                self._view.show_validation_error(self._error_message(error))
```

- [ ] **Step 3: 전체 자동화 테스트 통과 확인**

Run: `.venv/bin/python -m pytest -q`
Expected: 전체 스위트 통과 (기존 테스트 중 `SampleController`를 실행하는 것이 없으므로 회귀 없이 그대로 통과해야 한다).

- [ ] **Step 4: 수동 CLI 검증**

```bash
python main.py
```
메뉴에서 `[1] 시료 관리` → `[1] 시료 등록` 진입 후 아래를 확인한다.
- 시료명/평균 생산시간/수율 입력 후 `재고(ea) >` 프롬프트가 표시되는지.
- `-1`, `1.5`, `abc` 입력 시 `재고는 0 이상의 정수여야 합니다. 다시 입력해주세요.`가 출력되고 같은 프롬프트가 재표시되는지.
- `0`과 양의 정수(`50`) 입력이 모두 정상 등록되고, 등록 완료 화면의 `재고` 값이 입력한 값과 일치하는지.
- `[2] 시료 목록`에서 방금 등록한 시료의 `현재 재고` 컬럼이 입력값과 일치하는지.

- [ ] **Step 5: 커밋**

```bash
git add src/sampleorder/controllers/sample_controller.py src/sampleorder/views/sample_view.py
git commit -m "feat: prompt for stock during interactive sample registration"
```

---

### Task 4: 문서 갱신 (PRD.md, SPEC.md)

**Files:**
- Modify: `docs/PRD.md:59`, `docs/PRD.md:109-111`
- Modify: `docs/SPEC.md:56`, `docs/SPEC.md:60-73`

**Interfaces:** 없음 (문서 전용 태스크).

- [ ] **Step 1: `docs/PRD.md` 갱신**

`docs/PRD.md:59`의 Sample 필드 표 행을 교체한다.

```
| stock | int | 현재 재고 수량 (등록 시 사용자 입력, `0` 이상 정수. 이후 생산 완료로 증가, 출고로 감소) |
```

`docs/PRD.md:109-111`의 FR-1.1 항목을 교체한다.

```
- **FR-1.1 시료 등록**: `sample_id`(자동 채번), `name`, `avg_production_time`, `yield_rate`, `stock`을 입력받아 신규 시료를 추가한다.
  - `yield_rate`는 0 초과 1 이하 범위여야 하며, 범위를 벗어나면 등록을 거부하고 재입력을 요청한다.
  - `avg_production_time`은 0보다 커야 한다.
  - `stock`은 0 이상의 정수여야 하며, 그렇지 않으면 등록을 거부하고 재입력을 요청한다.
```

- [ ] **Step 2: `docs/SPEC.md` 갱신**

`docs/SPEC.md:56`의 입력 순서 설명을 교체한다.

```
입력 순서: `name` → `avg_production_time` → `yield_rate` → `stock`. `sample_id`는 자동 채번(`S-001`, `S-002`, ... 등록 순).
```

`docs/SPEC.md:60-73`의 검증 규칙 표와 등록 완료 출력 예시를 교체한다.

```
검증 규칙 및 실패 시 메시지:

| 필드 | 규칙 | 실패 메시지 |
|---|---|---|
| `avg_production_time` | 숫자, `0` 초과 | `평균 생산시간은 0보다 커야 합니다. 다시 입력해주세요.` |
| `yield_rate` | 숫자, `0` 초과 `1` 이하 | `수율은 0 초과 1 이하 값이어야 합니다. 다시 입력해주세요.` |
| `stock` | 정수, `0` 이상 | `재고는 0 이상의 정수여야 합니다. 다시 입력해주세요.` |

검증 실패 시 등록을 진행하지 않고 해당 필드만 재입력을 요청한다(FR-1.1). `stock`은 사용자가 직접 입력한 값으로 등록된다.

등록 완료 시 출력:
```
등록 완료.
 시료 ID   S-013
 시료명    GaN 에피택셜-6인치
 재고      50 ea
```
```

- [ ] **Step 3: 갱신 확인**

Run: `grep -n "stock" docs/PRD.md docs/SPEC.md`
Expected: 위에서 수정한 문구가 그대로 반영되어 있고, "기본값 0"이나 "항상 0으로 초기화"라는 표현이 FR-1.1/§2.2 어디에도 남아있지 않은지 눈으로 확인.

- [ ] **Step 4: 커밋**

```bash
git add docs/PRD.md docs/SPEC.md
git commit -m "docs: reflect user-supplied stock at sample registration"
```

---

## 완료 조건

- [ ] `.venv/bin/python -m pytest -q` 전체 통과.
- [ ] `python main.py`에서 시료 등록 시 재고를 직접 입력할 수 있고, 음수/소수/문자 입력 시 재입력을 요구함을 수동 확인.
- [ ] `docs/PRD.md`, `docs/SPEC.md`에 "재고 기본값 0" 관련 서술이 남아있지 않고 사용자 입력 방식으로 갱신됨.
- [ ] Task별로 커밋 완료 (총 3개 커밋: service/repository, controller/view, docs).
