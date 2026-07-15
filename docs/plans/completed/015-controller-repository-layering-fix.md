# Controller의 Repository 직접 접근 제거 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** `ApprovalController`와 `ShippingController`가 `sample_repository`를 직접 주입받아 `self._sample_repo.get(...)`을 호출하는 것을 제거하고, 시료명 조회를 각 컨트롤러가 이미 갖고 있는 Service(`OrderService`, `ShippingService`)를 통해서만 하도록 바꾼다. 이는 ARCHITECTURE.md §1("의존 방향은 항상 위→아래 한 방향... `controllers`는 `services`만 안다")과 ADR-0002("controllers/... → services/... → repositories/...의 단방향 의존")를 코드가 어기고 있던 것을 바로잡는 작업이다 — 두 문서 모두 이미 올바른 원칙을 서술하고 있으므로 문서 수정은 필요 없고 코드만 원칙에 맞춘다.

**Architecture:** `OrderService`와 `ShippingService`는 생성자에서 이미 `sample_repository`를 받아 보관하고 있다(승인 판정/출고 처리에 재고 조회가 필요하기 때문). 여기에 "주문 목록 → `{sample_id: sample_name}` 매핑"을 반환하는 조회 전용 메서드를 하나씩 추가하고, 각 컨트롤러는 자신의 `sample_repository` 참조를 제거한 뒤 이 메서드를 호출하도록 바꾼다. 새 Repository 메서드나 인터페이스 변경은 없다(기존 `sample_repository.get()`을 Service 내부로 옮기는 것뿐).

**Tech Stack:** Python (pytest), 기존 계층 구조 그대로.

## Global Constraints

- Repository/모델/계산 로직은 변경하지 않는다 — 오직 "어느 계층이 `sample_repository.get()`을 호출하는가"만 바꾼다.
- `OrderService.sample_name_map` / `ShippingService.sample_name_map`은 존재하지 않는 `sample_id`가 섞여 있어도 예외를 던지지 않는다(호출 시점에 이미 Repository에서 조회된 유효한 주문 목록에서만 뽑아낸 `sample_id`이므로 실무적으로 항상 존재하지만, 방어적으로 `NotFoundError`를 전파하지 않고 그대로 두어도 무방 — 기존 컨트롤러 코드도 동일하게 예외 처리를 하지 않았으므로 동작 변화 없음).
- `main.py`의 `ApprovalController`/`ShippingController` 생성자 호출부에서 `sample_repo` 인자를 제거한다.

---

### Task 1: `OrderService.sample_name_map` 추가 및 `ApprovalController` 수정

**Files:**
- Modify: `src/sampleorder/services/order_service.py`
- Test: `tests/test_order_service.py`
- Modify: `src/sampleorder/controllers/approval_controller.py`
- Modify: `main.py`

**Interfaces:**
- Produces: `OrderService.sample_name_map(orders: list[Order]) -> dict[str, str]`

- [x] **Step 1: 실패하는 테스트 작성**

`tests/test_order_service.py`에 추가:

```python
def test_sample_name_map_returns_name_per_sample_id(order_service, sample_repository, order_repository):
    sample_repository.create("실리콘 웨이퍼-8인치", 0.5, 0.9)
    order = order_repository.create("S-001", "고객A", 10)
    result = order_service.sample_name_map([order])
    assert result == {"S-001": "실리콘 웨이퍼-8인치"}
```

- [x] **Step 2: 테스트 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_order_service.py -v`
Expected: `AttributeError: 'OrderService' object has no attribute 'sample_name_map'`

- [x] **Step 3: 최소 구현 작성**

`src/sampleorder/services/order_service.py`의 `OrderService` 클래스에 메서드 추가(다른 메서드 순서/내용은 변경하지 않음):

```python
    def sample_name_map(self, orders: list) -> dict:
        return {order.sample_id: self._sample_repo.get(order.sample_id).name for order in orders}
```

- [x] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_order_service.py -v` → 전부 PASS.

- [x] **Step 5: `ApprovalController`에서 `sample_repository` 제거**

`src/sampleorder/controllers/approval_controller.py` 전체를 아래로 교체:

```python
from sampleorder.services.order_service import APPROVAL_SUFFICIENT, OrderService
from sampleorder.views.approval_view import ApprovalView


class ApprovalController:
    def __init__(self, service: OrderService, view: ApprovalView):
        self._service = service
        self._view = view

    def run(self) -> None:
        orders = self._service.list_reserved_orders()
        if not orders:
            self._view.show_no_pending_orders()
            return

        sample_names = self._service.sample_name_map(orders)
        self._view.show_reserved_table(orders, sample_names)

        choice = self._view.prompt_order_choice()
        if not choice.isdigit() or not (1 <= int(choice) <= len(orders)):
            self._view.show_invalid_choice()
            return

        order = orders[int(choice) - 1]
        decision = self._view.prompt_approve_or_reject()
        if decision == "N":
            rejected = self._service.reject_order(order.order_id)
            self._view.show_rejection_result(rejected)
            return

        self._approve(order.order_id)

    def _approve(self, order_id: str) -> None:
        preview = self._service.preview_approval(order_id)
        if preview.kind == APPROVAL_SUFFICIENT:
            updated = self._service.confirm_approval(order_id, preview)
            self._view.show_approval_result(updated, "RESERVED")
            return

        self._view.show_shortage_preview(preview)
        confirm = self._view.prompt_shortage_confirm()
        if confirm == "N":
            rejected = self._service.reject_order(order_id)
            self._view.show_rejection_result(rejected)
            return
        updated = self._service.confirm_approval(order_id, preview)
        self._view.show_approval_result(updated, "RESERVED")
```

- [x] **Step 6: `main.py` 생성자 호출 수정**

`main.py`에서 `ApprovalController(order_service, ApprovalView(), sample_repo)` →
`ApprovalController(order_service, ApprovalView())`로 수정.

- [x] **Step 7: 전체 테스트 통과 확인**

Run: `.venv/bin/python -m pytest -q` → 전체 스위트 통과.

- [x] **Step 8: 수동 CLI 검증**

```bash
python main.py
```
`[3] 주문 승인/거절` 메뉴에서 예약 목록의 시료명이 이전과 동일하게 표시되는지, 승인/거절이 정상 동작하는지 확인.

- [x] **Step 9: 커밋**

```bash
git add src/sampleorder/services/order_service.py src/sampleorder/controllers/approval_controller.py tests/test_order_service.py main.py
git commit -m "refactor: remove ApprovalController's direct repository access"
```

---

### Task 2: `ShippingService.sample_name_map` 추가 및 `ShippingController` 수정

**Files:**
- Modify: `src/sampleorder/services/shipping_service.py`
- Test: `tests/test_shipping_service.py`
- Modify: `src/sampleorder/controllers/shipping_controller.py`
- Modify: `main.py`

**Interfaces:**
- Produces: `ShippingService.sample_name_map(orders: list[Order]) -> dict[str, str]`

- [x] **Step 1: 실패하는 테스트 작성**

`tests/test_shipping_service.py`에 추가:

```python
def test_sample_name_map_returns_name_per_sample_id(shipping_service, sample_repository, order_repository):
    sample_repository.create("SiC 파워기판-6인치", 0.8, 0.92, stock=100)
    order = order_repository.create("S-001", "고객A", 10)
    result = shipping_service.sample_name_map([order])
    assert result == {"S-001": "SiC 파워기판-6인치"}
```

- [x] **Step 2: 테스트 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_shipping_service.py -v`
Expected: `AttributeError: 'ShippingService' object has no attribute 'sample_name_map'`

- [x] **Step 3: 최소 구현 작성**

`src/sampleorder/services/shipping_service.py`의 `ShippingService` 클래스에 메서드 추가:

```python
    def sample_name_map(self, orders: list) -> dict:
        return {order.sample_id: self._sample_repo.get(order.sample_id).name for order in orders}
```

- [x] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_shipping_service.py -v` → 전부 PASS.

- [x] **Step 5: `ShippingController`에서 `sample_repository` 제거**

`src/sampleorder/controllers/shipping_controller.py` 전체를 아래로 교체:

```python
from sampleorder.services.shipping_service import ShippingService
from sampleorder.views.shipping_view import ShippingView


class ShippingController:
    def __init__(self, service: ShippingService, view: ShippingView):
        self._service = service
        self._view = view

    def run(self) -> None:
        orders = self._service.list_confirmed_orders()
        if not orders:
            self._view.show_no_shippable_orders()
            return

        sample_names = self._service.sample_name_map(orders)
        self._view.show_confirmed_table(orders, sample_names)

        choice = self._view.prompt_order_choice()
        if not choice.isdigit() or not (1 <= int(choice) <= len(orders)):
            self._view.show_invalid_choice()
            return

        order = orders[int(choice) - 1]
        result = self._service.release(order.order_id)
        self._view.show_release_result(result)
```

- [x] **Step 6: `main.py` 생성자 호출 수정**

`main.py`에서 `ShippingController(shipping_service, ShippingView(), sample_repo)` →
`ShippingController(shipping_service, ShippingView())`로 수정.

- [x] **Step 7: 전체 테스트 통과 확인**

Run: `.venv/bin/python -m pytest -q` → 전체 스위트 통과.

- [x] **Step 8: 수동 CLI 검증**

```bash
python main.py
```
`[6] 출고 처리` 메뉴에서 출고 대기 목록의 시료명이 이전과 동일하게 표시되는지, 출고 처리가 정상 동작하는지 확인.

- [x] **Step 9: 커밋**

```bash
git add src/sampleorder/services/shipping_service.py src/sampleorder/controllers/shipping_controller.py tests/test_shipping_service.py main.py
git commit -m "refactor: remove ShippingController's direct repository access"
```

---

## 완료 조건

- [x] `.venv/bin/python -m pytest -q` 전체 통과.
- [x] `ApprovalController`, `ShippingController` 생성자에 `sample_repository` 파라미터가 남아있지 않음(`grep -rn "sample_repo" src/sampleorder/controllers/` 결과 없음).
- [x] `python main.py`에서 메뉴 3(승인/거절), 6(출고)의 시료명 표시·동작이 이전과 동일함을 수동 확인.
- [x] Task별로 커밋 완료(총 2개 커밋).
