# 생산라인 큐(FIFO) 영속화 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ProductionService`의 FIFO 큐(`self._queue`)가 현재 메모리에만 존재해 앱을 재시작하면 `PRODUCING` 상태 주문의 진행 정보(부족분/실생산량/총생산시간/시작 시각)가 사라지는 문제를 고친다. 이는 `docs/plans/completed/000-overview.md` §11에 이미 알려진 위험으로 기록돼 있고, PRD.md Goal 4 / NFR-1("재시작 후에도 데이터가 유지되는 영속성 보장")과 어긋난다. `data/production_queue.json` 파일을 추가해 큐를 다른 Repository와 동일한 원자적 쓰기 방식으로 영속화한다.

**Architecture:** 새 Repository 계층을 만들지 않고, `ProductionService` 생성자에 `JsonFileStore` 인스턴스를 세 번째 인자로 받는다(`repositories/*.py`가 각자 `JsonFileStore`를 감싸는 기존 패턴과 동일하게, `ProductionService` 자신이 큐 레코드의 dict ↔ `QueueItem` 변환과 저장을 책임진다 — 큐는 Repository의 CRUD 대상이 아니라 서비스 내부 상태이므로 별도 Repository 클래스를 만드는 것은 과설계). 큐가 바뀌는 시점(`enqueue`, `advance`의 `popleft`/`started_at` 갱신)마다 전체 큐를 dict 리스트로 직렬화해 `store.save()`를 호출한다. 생성자에서는 `store.load()`로 저장된 레코드를 읽어 `deque`를 복원한다. `store` 인자는 기본값 `None`으로 두어(하위 호환), `None`이면 기존과 동일하게 메모리 전용으로 동작한다 — 기존 테스트/호출부(`test_order_service.py`, `test_main_controller_smoke.py`)가 `ProductionService(order_repository, sample_repository)` 2-인자 호출에 의존하므로 깨지지 않는다. 실제 앱(`main.py`)은 항상 `store`를 전달해 영속화를 활성화한다.

**Tech Stack:** Python (dataclass, pytest), 기존 `JsonFileStore` 원자적 쓰기 재사용.

## Global Constraints

- 새 파일: `data/production_queue.json` (다른 데이터 파일과 동일하게 `.gitignore`의 `data/*.json` 패턴에 이미 포함되어 별도 설정 불필요).
- `QueueItem.started_at`은 `datetime | None`이므로 직렬화 시 `None`은 `null`로, 값이 있으면 ISO8601 문자열로 저장하고 복원 시 역변환한다.
- 큐 저장은 `enqueue()`와 `advance()`가 실제로 큐 내용을 바꿀 때만 수행한다(`current_item`/`pending_queue`/`queue_length`처럼 읽기 전용 메서드는 저장하지 않음).
- `store=None`일 때(기존 테스트 호환 경로)는 저장/복원 로직을 완전히 건너뛴다 — `None` 체크만 추가하고 기존 메모리 전용 동작은 한 줄도 바꾸지 않는다.
- `docs/ARCHITECTURE.md` §2(디렉터리 구조)·§5(영속성 설계), `docs/adr/ADR-0001-JSON파일기반영속성.md`을 이번 변경에 맞게 갱신한다. `docs/plans/completed/000-overview.md` §11은 과거 계획의 완료 기록이므로 수정하지 않는다(히스토리 보존 — 대신 이 계획 파일이 그 위험에 대한 후속 조치임을 위 Goal에 명시했다).

---

### Task 1: `ProductionService`에 저장/복원 로직 추가

**Files:**
- Modify: `src/sampleorder/services/production_service.py`
- Test: `tests/test_production_service.py`
- Modify: `tests/conftest.py` (재사용 가능한 `queue_store` fixture 추가)

**Interfaces:**
- Produces: `ProductionService.__init__(order_repository, sample_repository, store=None)` — `store: JsonFileStore | None`.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/conftest.py`에 fixture 추가:

```python
@pytest.fixture
def queue_store(tmp_path):
    return JsonFileStore(tmp_path / "production_queue.json")
```

`tests/test_production_service.py`에 추가(파일 상단 import에 `queue_store` fixture는 conftest에서 자동 주입되므로 별도 import 불필요, `JsonFileStore`만 새로 import):

```python
from sampleorder.json_store import JsonFileStore


def test_queue_survives_restart_via_store(
    queue_store, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.8, 0.92)
    order = order_repository.create("S-001", "고객A", 200)

    first_instance = ProductionService(order_repository, sample_repository, store=queue_store)
    first_instance.enqueue(
        order.order_id, "S-001", "A", 200, 170, 185, 148.0, now_fn=lambda: fixed_now
    )

    second_instance = ProductionService(order_repository, sample_repository, store=queue_store)
    assert second_instance.queue_length() == 1

    completion_time = fixed_now + timedelta(minutes=148)
    second_instance.advance(now_fn=lambda: completion_time)
    assert second_instance.queue_length() == 0
    assert order_repository.get(order.order_id).status == OrderStatus.CONFIRMED

    third_instance = ProductionService(order_repository, sample_repository, store=queue_store)
    assert third_instance.queue_length() == 0


def test_queue_restores_started_at_and_pending_order(
    queue_store, sample_repository, order_repository, fixed_now
):
    sample_repository.create("A", 0.8, 0.92)
    order1 = order_repository.create("S-001", "고객A", 100)
    order2 = order_repository.create("S-001", "고객B", 50)

    first_instance = ProductionService(order_repository, sample_repository, store=queue_store)
    first_instance.enqueue(order1.order_id, "S-001", "A", 100, 100, 109, 10.0, now_fn=lambda: fixed_now)
    first_instance.enqueue(order2.order_id, "S-001", "A", 50, 50, 55, 5.0, now_fn=lambda: fixed_now)

    restored = ProductionService(order_repository, sample_repository, store=queue_store)
    current = restored.current_item(now_fn=lambda: fixed_now)
    assert current.item.order_id == order1.order_id
    assert current.item.started_at == fixed_now
    pending = restored.pending_queue(now_fn=lambda: fixed_now)
    assert [p.item.order_id for p in pending] == [order2.order_id]


def test_store_none_keeps_in_memory_only_behavior(sample_repository, order_repository, fixed_now):
    service = ProductionService(order_repository, sample_repository)
    order = order_repository.create("S-001", "고객A", 200)
    service.enqueue(order.order_id, "S-001", "A", 200, 170, 185, 148.0, now_fn=lambda: fixed_now)
    assert service.queue_length() == 1
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_production_service.py -v`
Expected: 새 테스트들이 `TypeError: __init__() got an unexpected keyword argument 'store'`로 FAIL, 기존 테스트는 그대로 PASS.

- [ ] **Step 3: 최소 구현 작성**

`src/sampleorder/services/production_service.py`에서 아래를 수정한다.

파일 상단에 직렬화 헬퍼 추가(클래스 정의 이전, `dataclass` 정의들 다음):

```python
def _item_to_dict(item: QueueItem) -> dict:
    return {
        "order_id": item.order_id,
        "sample_id": item.sample_id,
        "sample_name": item.sample_name,
        "quantity": item.quantity,
        "shortage_qty": item.shortage_qty,
        "actual_yield_qty": item.actual_yield_qty,
        "total_time": item.total_time,
        "started_at": item.started_at.isoformat() if item.started_at else None,
    }


def _dict_to_item(record: dict) -> QueueItem:
    return QueueItem(
        order_id=record["order_id"],
        sample_id=record["sample_id"],
        sample_name=record["sample_name"],
        quantity=record["quantity"],
        shortage_qty=record["shortage_qty"],
        actual_yield_qty=record["actual_yield_qty"],
        total_time=record["total_time"],
        started_at=datetime.fromisoformat(record["started_at"]) if record["started_at"] else None,
    )
```

`ProductionService.__init__`을 교체:

```python
    def __init__(self, order_repository, sample_repository, store=None):
        self._order_repo = order_repository
        self._sample_repo = sample_repository
        self._store = store
        if store is not None:
            self._queue = deque(_dict_to_item(record) for record in store.load())
        else:
            self._queue = deque()

    def _persist(self) -> None:
        if self._store is not None:
            self._store.save([_item_to_dict(item) for item in self._queue])
```

`enqueue()` 끝에 저장 호출 추가(메서드 마지막 줄 `return item` 직전):

```python
        self._queue.append(item)
        self._persist()
        return item
```

`advance()`의 `while` 루프 몸통 마지막에 저장 호출 추가(루프가 한 번이라도 돌면 저장; 루프 밖에서 한 번만 호출해도 되지만 "여러 항목이 한꺼번에 완료"되는 경우를 고려해 루프 종료 후 1회 호출로 충분):

```python
    def advance(self, now_fn=utc_now) -> None:
        now = now_fn()
        changed = False
        while self._queue and self._elapsed_minutes(self._queue[0], now) >= self._queue[0].total_time:
            item = self._queue.popleft()
            sample = self._sample_repo.get(item.sample_id)
            self._sample_repo.update(item.sample_id, stock=sample.stock + item.actual_yield_qty)
            self._order_repo.update(item.order_id, status=OrderStatus.CONFIRMED)
            if self._queue:
                self._queue[0].started_at = item.started_at + timedelta(minutes=item.total_time)
            changed = True
        if changed:
            self._persist()
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest -q` → 전체 스위트 통과(기존 `production_service` fixture는 `store` 인자를 넘기지 않으므로 `store=None` 경로로 그대로 동작).

- [ ] **Step 5: 커밋**

```bash
git add src/sampleorder/services/production_service.py tests/test_production_service.py tests/conftest.py
git commit -m "feat: persist production queue to survive app restart"
```

---

### Task 2: `main.py`에 실제 저장소 연결

**Files:**
- Modify: `main.py`

**Interfaces:** 없음(배선 변경만).

- [ ] **Step 1: `build_main_controller()` 수정**

`main.py`에서 `order_store`/`sample_store` 생성 부분 다음에 추가:

```python
    queue_store = JsonFileStore(DATA_DIR / "production_queue.json")
```

`ProductionService(order_repo, sample_repo)` → `ProductionService(order_repo, sample_repo, store=queue_store)`로 수정.

- [ ] **Step 2: 수동 재시작 검증**

```bash
python main.py
```
1. `[2] 주문 접수`로 재고보다 많은 수량 주문 생성 → `[3] 주문 승인/거절`에서 승인(재고 부족 분기, `PRODUCING` 전환)
2. 앱 종료(`Ctrl+D`/종료 메뉴) 후 `data/production_queue.json`이 생성되고 내용이 있는지 확인: `cat data/production_queue.json`
3. `python main.py` 재실행 → `[5] 생산라인 조회` 진입 시 방금 등록한 항목이 그대로 표시되는지 확인(재시작 전과 동일한 부족분/실생산량/진행률 기준점)
4. 총생산시간이 지난 뒤(또는 짧은 `total_time`의 테스트 데이터로) 재진입 시 정상적으로 `CONFIRMED`로 완료 처리되는지 확인

- [ ] **Step 3: 전체 테스트 통과 확인**

Run: `.venv/bin/python -m pytest -q` → 전체 스위트 통과.

- [ ] **Step 4: 커밋**

```bash
git add main.py
git commit -m "feat: wire production queue persistence into main.py"
```

---

### Task 3: 문서 갱신 (ARCHITECTURE.md, ADR-0001)

**Files:**
- Modify: `docs/ARCHITECTURE.md` §2, §5
- Modify: `docs/adr/ADR-0001-JSON파일기반영속성.md`

**Interfaces:** 없음(문서 전용).

- [ ] **Step 1: `docs/ARCHITECTURE.md` §2 디렉터리 구조 갱신**

`data/` 항목을 아래로 교체:

```
  data/
    samples.json, orders.json, production_queue.json
```

- [ ] **Step 2: `docs/ARCHITECTURE.md` §5 영속성 설계 갱신**

"저장 파일: `data/samples.json`, `data/orders.json`." 문장을 아래로 교체:

```
- 저장 파일: `data/samples.json`, `data/orders.json`, `data/production_queue.json`. 각각 레코드 리스트(JSON 배열)를 통째로 읽고 통째로 쓴다(NFR-2). 트랜잭션/부분 갱신 개념 없음 — 단일 프로세스 콘솔 앱 규모에 적합하다는 PRD.md §3 Out of Scope 전제와 일치.
- `production_queue.json`은 `ProductionService`가 직접 소유한다(별도 Repository 없음) — `enqueue()`/`advance()`로 큐 내용이 바뀔 때마다 전체 큐를 직렬화해 저장하고, 생성 시점에 복원한다. 이로써 `PRODUCING` 상태 주문도 앱 재시작 후 진행 정보(부족분/실생산량/총생산시간/시작 시각)가 유지된다(PRD.md NFR-1).
```

- [ ] **Step 3: `docs/adr/ADR-0001-JSON파일기반영속성.md` 갱신**

"결정" 절의 "`data/samples.json`, `data/orders.json` 두 개의 JSON 파일" 문장을 "`data/samples.json`, `data/orders.json`, `data/production_queue.json` 세 개의 JSON 파일"로 수정.

- [ ] **Step 4: 갱신 확인**

Run: `grep -n "production_queue" docs/ARCHITECTURE.md docs/adr/ADR-0001-JSON파일기반영속성.md`
Expected: 위에서 추가한 문구가 모두 반영됨.

- [ ] **Step 5: 커밋**

```bash
git add docs/ARCHITECTURE.md "docs/adr/ADR-0001-JSON파일기반영속성.md"
git commit -m "docs: reflect production queue persistence in ARCHITECTURE/ADR-0001"
```

---

## 완료 조건

- [ ] `.venv/bin/python -m pytest -q` 전체 통과.
- [ ] `PRODUCING` 상태 주문이 있는 상태에서 `python main.py`를 재시작해도 `[5] 생산라인 조회`에 해당 항목이 유지되고, 완료 시점에 정상적으로 `CONFIRMED`로 전환됨을 수동 확인.
- [ ] `data/production_queue.json`이 다른 데이터 파일과 동일한 원자적 쓰기 방식(`os.replace`)으로 저장됨(코드 재사용 확인 — 별도 구현 없음).
- [ ] `docs/ARCHITECTURE.md`, `docs/adr/ADR-0001-JSON파일기반영속성.md`에 세 번째 데이터 파일이 반영됨.
- [ ] Task별로 커밋 완료(총 3개 커밋).
