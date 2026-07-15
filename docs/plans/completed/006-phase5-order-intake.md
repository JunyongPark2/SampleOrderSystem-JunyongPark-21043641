# Phase 5: 주문 접수 (FR-2.1)

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고.

## 목표

고객 주문 접수 기능을 완성해 메뉴 `[2] 시료 주문`이 SPEC.md §3 예시 화면대로 동작하게 한다. 승인/거절(Phase 6)의 기반이 되는 `RESERVED` 상태 생성까지만 다룬다.

## 선행 조건

Phase 2(영속성), Phase 4(시료 관리 — `sample_id` 존재 여부 확인을 위해 `SampleRepository` 완성 필요) 완료.

## 작업 범위

- `services/order_service.py`: `create_order(sample_id, customer_name, quantity)` — `sample_id` 미존재 시 생성 중단, `quantity` 검증(1 이상 정수) 실패 시 재입력.
- `views/order_view.py`: 입력 순서(`sample_id`→`customer_name`→`quantity`) + 확인(Y/N) + 결과 화면(SPEC.md §3.1).
- `controllers/order_controller.py`: 메뉴 진입/흐름 제어.

## 비작업 범위

- 승인/거절 로직 — Phase 6.
- `order_service.py`의 승인/거절 메서드는 이 Phase에서 만들지 않는다(다음 Phase에서 같은 파일에 추가).

## 수정하거나 생성할 파일

```
src/sampleorder/services/order_service.py       (신규, create_order만)
src/sampleorder/views/order_view.py
src/sampleorder/controllers/order_controller.py
tests/test_order_service.py                      (신규, 접수 케이스만)
```

## 구현 단계

1. `order_service.py`: `create_order()` — `SampleRepository.get(sample_id)`에서 `NotFoundError` 발생 시 SPEC.md §3.1 오류 메시지로 변환해 주문 생성을 중단(재입력 요구 없음).
2. `quantity` 검증: 정수이고 1 이상인지 확인, 실패 시 `ValidationError` → View에서 같은 필드만 재입력.
3. `order_id` 채번은 `OrderRepository.create()`에 위임(Phase 2에서 구현됨), `status=RESERVED`, `created_at`은 ISO8601 UTC.
4. `order_view.py`: 입력 확인 화면(SPEC.md §3.1 "입력 내용 확인" + `[Y]/[N]`) 구현, `N` 선택 시 주문 생성 취소.
5. `order_controller.py`: 위 흐름 조립.

## 검증 방법

- 자동: `pytest tests/test_order_service.py -k intake`(또는 해당 테스트 클래스/함수명 기준).
- 수동: `python main.py` → `[2] 시료 주문` → SPEC.md §3.1 예시 화면과 동일하게 접수 완료 문구·주문번호 형식(`ORD-YYYYMMDD-NNNN`) 확인.

## 테스트 계획

- 존재하지 않는 `sample_id` → 오류 메시지, 주문 미생성(Repository에 레코드 없음 확인).
- `quantity` 0 또는 음수 또는 소수 → 재입력 요구(반복 검증), 결국 유효값 입력 시 생성 성공.
- 생성된 주문의 `status == RESERVED`, `order_id` 형식, `created_at` ISO8601 형식 확인.

## 완료 조건

- [x] `tests/test_order_service.py`(접수 관련) 전체 통과.
- [x] 수동 시나리오가 SPEC.md §3.1과 일치.

## 진행 기록

- `services/order_service.py`: `validate_sample_id`(미존재 시 `NotFoundError` → `ValidationError(SAMPLE_NOT_FOUND_ERROR)`로 변환, 재입력 없이 중단), `validate_quantity`(정수·1 이상만 통과), `create_order`가 둘을 검증한 뒤 `OrderRepository.create()`에 위임.
- `views/order_view.py`, `controllers/order_controller.py`: `sample_id`→`customer_name`→`quantity` 순서 입력, `sample_id` 오류 시 즉시 중단(재입력 없음), `quantity` 오류 시 재입력 루프, Y/N 확인 화면, 접수 완료 화면(SPEC.md §3.1 문구 그대로).
- 메뉴 `[2]`는 시료 관리(메뉴 `[1]`)와 달리 하위 메뉴 루프가 없고 단발성 흐름이라 `OrderController.run()`을 1회 실행 후 자동으로 메인 메뉴로 복귀하는 구조로 구현(SPEC.md §3 예시 화면에 하위 메뉴 표시가 없음을 근거로 판단).
- 테스트: `pytest tests/test_order_service.py -q` → 5 passed.
- 수동 시나리오: `OrderController`를 임시 스크립트로 조립해 (1) 숫자 아님/0 → 재입력 요구 → 200 입력 → Y 확인 → `ORD-20260715-0001`/RESERVED 접수 완료, (2) 존재하지 않는 `sample_id` → 즉시 중단 메시지, 두 경우 모두 SPEC.md §3.1 문구·형식과 일치 확인.
