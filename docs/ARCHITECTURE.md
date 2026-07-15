# ARCHITECTURE: 반도체 시료 생산주문관리 시스템

> 이 문서는 "어떻게 만들 것인가"를 다룬다. "무엇을 만드는가"는 [`PRD.md`](./PRD.md)(배경/범위/요구사항), "화면별 입출력 규칙이 무엇인가"는 [`SPEC.md`](./SPEC.md)를 참고한다. 세 문서의 계산식·상태값·메뉴 번호는 항상 일치해야 하며, 이 문서에서 별도로 재정의하지 않는다(SPEC.md §8 Single Source of Truth 준수).
>
> 미션1에서 검증된 4개 PoC 저장소(동일 워크스페이스 `../`)의 실제 구현 패턴을 그대로 재사용한다: `ConsoleMVC`, `DataPersistence`, `DataMonitor`, `DummyDataGenerator`. 아래 각 절에서 재사용 대상 클래스/함수명을 실제 이름으로 명시한다.

## 1. 레이어 구조

```
┌──────────────────────────────────────────────────────────┐
│ views/            콘솔 입출력 전담 (print/input만, 로직 없음)  │
├──────────────────────────────────────────────────────────┤
│ controllers/      View ↔ Service 연결, 메뉴 디스패치         │
├──────────────────────────────────────────────────────────┤
│ services/         비즈니스 로직 (승인 판정/생산 계산/집계 등)   │
├──────────────────────────────────────────────────────────┤
│ repositories/      CRUD + 조회 조건 (list_by_status 등)      │
├──────────────────────────────────────────────────────────┤
│ json_store.py     원자적 JSON 파일 입출력                    │
└──────────────────────────────────────────────────────────┘
```

의존 방향은 항상 위→아래 한 방향이다(`views`는 `controllers`만 알고, `controllers`는 `services`만 안다). `services`는 콘솔 I/O를 절대 import하지 않는다 — NFR-4(테스트 가능성)의 핵심 제약이다.

- **View**: 화면 출력·입력 수집만 담당. 검증 실패 메시지 문구(SPEC.md 각 절)는 View가 아니라 Service가 반환한 에러를 그대로 출력하는 방식으로, 문구 자체는 Service/exceptions 쪽에 두어 View 교체(예: GUI 전환) 시에도 검증 로직이 재사용되게 한다.
- **Controller**: 메뉴 선택 → 입력 수집 루프 → Service 호출 → View 출력 순서만 조립한다. 재고 비교, 계산식 등 분기 로직을 직접 갖지 않는다(ConsoleMVC 패턴 준수).
- **Service**: PRD.md §5 FR 항목의 실제 판정/계산이 있는 유일한 계층. SPEC.md §8의 5개 공식(부족분/실생산량/총생산시간/대기수요/재고상태)은 여기 한 곳에만 구현한다.
- **Repository**: `JsonFileStore` 위에 CRUD와 조건 조회만 얹는다. 비즈니스 규칙 없음.

## 2. 디렉터리 구조

```
SampleOrderSystem/
  main.py                        # 진입점: build_main_controller().run()
  src/sampleorder/
    models.py                    # Sample, Order, OrderStatus
    exceptions.py                # NotFoundError, DuplicateError, ValidationError
    json_store.py                # JsonFileStore (DataPersistence 재사용)
    repositories/
      sample_repository.py       # SampleRepository: create/get/list_all/search/update
      order_repository.py        # OrderRepository: create/get/list_all/list_by_status/update
      _record_utils.py           # find_record: id로 레코드 탐색 후 없으면 NotFoundError (두 레포지토리 공용)
    services/
      sample_service.py          # FR-1.1~1.3 등록/조회/검색 + 등록 검증
      order_service.py           # FR-2.1 접수, FR-3.2/3.3 승인·거절 판정
      production_service.py      # FR-5.1~5.5 FIFO 큐, 생산 계산/완료 처리
      shipping_service.py        # FR-6.1~6.2 출고
      monitoring_service.py      # FR-4.1~4.2 상태별 집계, 재고 상태 판정
      calculations.py            # 공식 7종 단일 구현체 (shortage/actual_yield/total_production_time/pending_demand/stock_status/reserved_qty/available_stock)
      sample_lookup.py           # sample_name_map: 주문 목록→시료명 매핑 (order_service/shipping_service 공용)
      validation.py              # validate_int: "true int" 검증 가드 (order_service/sample_service 공용)
    views/
      main_view.py, sample_view.py, order_view.py, approval_view.py,
      monitoring_view.py, production_view.py, shipping_view.py
      formatting.py              # 한글 폭 정렬 유틸 (DataMonitor render.py 이식)
    controllers/
      main_controller.py         # 메뉴 디스패치 (ConsoleMVC MainController 패턴)
      sample_controller.py, order_controller.py, approval_controller.py,
      monitoring_controller.py, production_controller.py, shipping_controller.py
      _prompting.py               # prompt_until_valid: 파싱→검증→재입력 루프 공용 헬퍼 (sample/order 컨트롤러 공용)
    clock.py                     # now_fn 기본값 및 타입 힌트 (DataMonitor DI 패턴)
  data/
    samples.json, orders.json, production_queue.json
  tools/
    dummy_data_cli.py            # DummyDataGenerator 로직 재사용 (배포 산출물 범위 밖)
  tests/
    test_calculations.py, test_order_service.py, test_production_service.py,
    test_monitoring_service.py, test_shipping_service.py,
    test_sample_repository.py, test_order_repository.py,
    test_json_store.py, test_models.py, test_sample_service.py,
    test_main_controller_smoke.py, test_prompting.py,
    test_sample_controller.py, test_order_controller.py, test_approval_controller.py,
    test_shipping_controller.py, test_monitoring_controller.py, test_production_controller.py,
    test_formatting.py, test_main_view.py, test_sample_view.py, test_order_view.py,
    test_approval_view.py, test_shipping_view.py, test_monitoring_view.py, test_production_view.py,
    conftest.py, __init__.py
  CLAUDE.md
  docs/
    PRD.md, SPEC.md, ARCHITECTURE.md
    plans/active/
  requirements.txt
  pyproject.toml
```

`calculations.py`를 별도 모듈로 분리한 이유: SPEC.md §8이 "이 공식들은 서비스 계층에 단일 구현으로 존재해야 하며 화면/메뉴 간 중복 계산을 두지 않는다"고 명시하므로, `order_service`(승인 시 미리보기 계산)와 `production_service`(큐 계산)가 같은 함수를 import하도록 물리적으로 한 파일에 고정한다.

## 3. PoC 재사용 매핑

| 대상 모듈 | 재사용 출처 | 실제 이름(원본) | 비고 |
|---|---|---|---|
| `controllers/main_controller.py` | `ConsoleMVC/app/controllers/main_controller.py` | `MainController` — `self._actions` 딕셔너리(`"1"`~`"6"` → 서브컨트롤러 바운드 메서드), `run()`이 `view.show_main_menu()` → `prompt_menu_choice()` → `_dispatch()` 순으로 루프 | 미구현 액션은 `NotImplementedError` → `view.show_not_implemented()`로 캐치하는 패턴도 동일 채택 |
| `json_store.py` | `DataPersistence/src/sampleorder/json_store.py` | `JsonFileStore.save()`가 `path.with_suffix(".tmp")`에 쓴 뒤 `os.replace()`로 치환, `load()`는 파일 없으면 `[]` 반환 | NFR-3 그대로 이식 |
| `repositories/*.py` | `DataPersistence`의 `OrderRepository`/`SampleRepository` | 공통 베이스 클래스 없이 각자 `JsonFileStore`를 감싸 `create/get/list_all/list_by_status/update` 구현(`delete`는 현재 스펙상 필요 없어 미구현), `order_id`는 정적 메서드 `_next_id`로 `ORD-YYYYMMDD-0001` 형식 채번 | 본 프로젝트도 베이스 클래스를 새로 만들지 않고 동일하게 각자 구현(과설계 방지) |
| `exceptions.py` | `DataPersistence/src/sampleorder/exceptions.py` | `NotFoundError(entity_name, entity_id)`, `DuplicateError(entity_name, entity_id)` | `ValidationError`는 본 프로젝트에서 신규 추가(FR-1.1/FR-2.1 검증 실패용) |
| `clock.py` 주입 방식 | `DataMonitor/datamonitor/app.py` | Clock 프로토콜 클래스 없이 `clock_now=datetime.now` 같은 함수 인자 주입 방식 | `production_service`의 진행률 계산 함수도 동일하게 `now_fn: Callable[[], datetime] = clock.utc_now`(timezone-aware) 파라미터로 주입 (NFR-4) |
| `monitoring_service.py` | `DataMonitor/datamonitor/monitor.py` | 클래스 `DataMonitor`의 `order_status_counts()` 패턴을 채택, 대기수요/재고상태 판정은 `calculations.pending_demand()`/`calculations.stock_status()` 자유 함수로 구현(`STOCK_DEPLETED`/`STOCK_SHORTAGE`/`STOCK_SUFFICIENT` = 고갈/부족/여유), 집계 조회는 `stock_report()`/`dashboard_summary()`로 구현 | 클래스명은 `MonitoringService`로 변경, 대기수요/재고상태 로직은 `calculations.py`로 이동(SPEC.md §8 공식 단일화 원칙 준수) |
| `views/formatting.py` | `DataMonitor/datamonitor/render.py` | `_display_width(text)`가 `unicodedata.east_asian_width(ch) in ("F", "W")`로 전각 판정, `_ljust`/`_rjust`로 고정폭 정렬 | NFR-5 그대로 이식 |
| `tools/dummy_data_cli.py` | `DummyDataGenerator/src/dummydata/generator.py` | 클래스 `DummyDataGenerator(sample_repo, order_repo, rng=random.Random())`, `SAMPLE_POOL`/`CUSTOMER_POOL` 고정 목록, `ORDER_STATUS_WEIGHTS` 가중치 목록 + `_weighted_status()` 누적 롤 방식, 공개 메서드 `generate_samples(count)`/`generate_orders(count, within_days=30)`/`generate(sample_count, order_count)` | 본 프로젝트의 `JsonFileStore`/Repository를 그대로 주입해 재사용(자체 사본 만들지 않음) |

## 4. 핵심 시퀀스

### 4.1 주문 승인 — 재고 부족 (FR-3.2, SPEC.md §4.2)

```
ApprovalController.approve(order_id)
  → OrderService.preview_approval(order_id)
      1. order = OrderRepository.get(order_id)          # 없으면 NotFoundError
      2. sample = SampleRepository.get(order.sample_id)
      3. other_orders = OrderRepository.list_all() 중 order_id 제외
         reserved = calculations.reserved_qty(other_orders, order.sample_id)   # CONFIRMED+PRODUCING만 합산
         available = calculations.available_stock(sample.stock, reserved)     # max(stock-reserved, 0)
      4. shortage = calculations.shortage(order.quantity, available)
      5. if shortage <= 0: return ApprovalPreview(kind=SUFFICIENT)
      6. actual_yield = calculations.actual_yield(shortage, sample.yield_rate)
         total_time = calculations.total_production_time(sample.avg_production_time, actual_yield)
         return ApprovalPreview(kind=SHORTAGE, shortage, actual_yield, total_time)
  ← ApprovalView가 preview를 표시하고 Y/N 확인
  → (Y) OrderService.confirm_approval(order_id, preview)
      1. sample 재조회(직전 조회 이후 변경 가능성 대비, 단일 프로세스라 실질적 위험은 낮음)
      2. preview.kind == SHORTAGE:
           OrderRepository.update(order_id, status=PRODUCING)
           ProductionService.enqueue(order_id, sample_id, shortage, actual_yield, total_time)
         preview.kind == SUFFICIENT:
           OrderRepository.update(order_id, status=CONFIRMED)
  → (N) OrderService.reject_order(order_id) → status = REJECTED (SPEC.md §4.2, §4.3의 거절과 동일 결과)
```

`OrderService`는 `ProductionService`를 호출만 하고, 큐 자료구조(FIFO 리스트) 자체는 `ProductionService`가 소유한다 — 두 서비스가 같은 상태를 이중 관리하지 않도록 소유권을 한쪽에 고정한다.

### 4.2 생산 완료 처리 (FR-5.3)

메뉴 4/5/6 진입 시 컨트롤러가 매번 `ProductionService.advance(now_fn())`를 먼저 호출한다(SPEC.md §6.2 "실시간 스케줄러 없이 메뉴 진입 시 갱신").

```
ProductionService.advance(now)
  while queue and queue[0].elapsed(now) >= queue[0].total_time:
      item = queue.popleft()
      SampleRepository.update(item.sample_id, stock=+item.actual_yield)
      OrderRepository.update(item.order_id, status=CONFIRMED)
      if queue:
          queue[0].started_at = item.started_at + timedelta(minutes=item.total_time)   # 다음 항목은 "이전 항목의 이론적 완료 시각"부터 시작
```

`while` 루프인 이유: 사용자가 오랫동안 메뉴에 들어오지 않아 큐 앞의 여러 항목이 한꺼번에 완료 조건을 만족할 수 있기 때문(시간 소스 주입 기반 시뮬레이션이므로 실제로도 발생 가능).

다음 항목의 `started_at`을 완료 처리 시점의 `now`가 아니라 "이전 항목의 이론적 완료 시각"(`started_at + total_time`)으로 재설정하는 이유: `now`로 재설정하면, 오랫동안 메뉴에 들어오지 않아 한 번의 `advance()` 호출에서 `now`가 크게 점프한 경우 큐의 첫 항목만 완료되고 이후 항목은 시계가 `now` 시점부터 다시 0으로 시작해 버려, 위 "여러 항목이 한꺼번에 완료"되어야 하는 요구사항을 만족하지 못한다(Phase 7 구현 중 발견, `docs/plans/completed/008-phase7-production-line.md` 진행 기록 참고).

### 4.3 출고 처리 (FR-6.2)

```
ShippingController.ship(order_id)
  → ShippingService.release(order_id)
      1. order = OrderRepository.get(order_id)   # status != CONFIRMED면 ValidationError
      2. sample = SampleRepository.get(order.sample_id)
         if sample.stock < order.quantity: raise InsufficientStockError   # stock 변경 없이 중단
      3. SampleRepository.update(order.sample_id, stock=-order.quantity)
      4. OrderRepository.update(order_id, status=RELEASE)
      5. return ReleaseResult(order, processed_at=now_fn())
```

Y/N 확인 없이 즉시 실행(SPEC.md §7.2)하므로 컨트롤러에 확인 분기가 없다 — 다른 메뉴(승인, 주문 접수)와 다른 흐름임을 컨트롤러 주석이 아니라 이 문서로 남긴다.

2단계 검증 방어선: `preview_approval`이 예약 재고를 반영해 승인 시점에 이미 부족 판정을 걸러내지만(ADR-0004), `release()`도 차감 직전 재고를 다시 검증한다 — 두 검증 지점이 다른 시점(승인 vs 출고)의 다른 위험(중복 예약 vs 그 사이 발생할 수 있는 다른 변경)을 막는 별개의 방어선이기 때문에 하나로 줄이지 않는다.

## 5. 영속성 설계

- 저장 파일: `data/samples.json`, `data/orders.json`, `data/production_queue.json`. 각각 레코드 리스트(JSON 배열)를 통째로 읽고 통째로 쓴다(NFR-2). 트랜잭션/부분 갱신 개념 없음 — 단일 프로세스 콘솔 앱 규모에 적합하다는 PRD.md §3 Out of Scope 전제와 일치.
- `production_queue.json`은 `ProductionService`가 직접 소유한다(별도 Repository 없음) — `enqueue()`/`advance()`로 큐 내용이 바뀔 때마다 전체 큐를 직렬화해 저장하고, 생성 시점에 복원한다. 이로써 `PRODUCING` 상태 주문도 앱 재시작 후 진행 정보(부족분/실생산량/총생산시간/시작 시각)가 유지된다(PRD.md NFR-1).
- 쓰기는 `JsonFileStore.save()` 1곳에서만 발생하며, 모든 Repository의 `update`/`create`(`delete`는 현재 스펙상 미구현)는 내부적으로 전체 리스트를 메모리에서 수정한 뒤 `save()`를 호출한다. 동시 쓰기 경합은 고려하지 않는다(NFR 범위 밖, 단일 프로세스 가정).
- ID 채번: `sample_id`는 전체 레코드 수 기준 순번(`S-001`...), `order_id`는 "해당 날짜 내" 순번이므로 채번 시 같은 날짜의 기존 `order_id` 최대값을 조회해야 한다 — `OrderRepository._next_id(date)`가 `list_all()`을 필터링해 계산한다(별도 카운터 파일을 두지 않음, 단일 파일 원칙 유지).

## 6. 예외 처리 전략

| 예외 | 발생 위치 | Controller/View 처리 |
|---|---|---|
| `NotFoundError` | Repository `get()` | 주문 접수 시 `sample_id` 미존재 → SPEC.md §3.1 오류 메시지 출력 후 주문 생성 중단(재입력 요청 아님) |
| `ValidationError` | Service 계층 (수량/생산시간/수율 범위) | Controller가 catch해 SPEC.md 해당 절의 메시지를 출력하고 **같은 필드만** 재입력 루프 |
| `DuplicateError` | 현재 스펙상 발생 지점 없음(ID는 항상 자동 채번) | 향후 수동 ID 입력 기능이 생기기 전까지는 미사용 — 코드에 존재만 하고 raise하는 곳이 없다면 그 사실을 테스트에 남기지 않는다(불필요한 커버리지 강요 금지) |
| `InsufficientStockError` | `ShippingService.release()` (차감 전 `stock < quantity` 검증) | Controller가 catch해 SPEC.md §7.2 오류 메시지 출력 후 메인 메뉴 복귀, `stock`은 변경하지 않음 |

콘솔에 노출되는 문구는 SPEC.md에 명시된 문구를 정확히 그대로 사용한다 — Service/exceptions가 문구를 만들고 View는 그대로 print한다(문구 이중 관리 방지).

## 7. 테스트 전략 (NFR-8)

- `tests/test_calculations.py`: 5개 공식의 경계값(수율 1.0, 부족분 0, 올림 처리 등)만 순수 함수 테스트로 커버.
- `tests/test_*_service.py`: Repository를 실제 `JsonFileStore`(`tmp_path` 기반)로 생성해 통합 테스트하거나, 인터페이스가 작으면 in-memory 딕셔너리 fake로 대체 — 어느 쪽이든 콘솔 I/O(`input`/`print`) 없이 실행 가능해야 한다(NFR-4).
- `tests/conftest.py`: `tmp_path`로 `data/` 격리(DataPersistence `conftest.py` 패턴 재사용), `now_fn`은 고정 `datetime`을 반환하는 fixture로 주입해 생산 진행률 계산을 결정론적으로 검증.
- Controller/View 계층은 얇은 조립 코드이므로 단위 테스트 필수 대상이 아니다 — 필요 시 스모크 수준의 통합 테스트 1~2개만 둔다(과도한 mocking 지양).

## 8. 설계 결정 요약

| 결정 | 대안 | 선택 이유 | 상세 |
|---|---|---|---|
| JSON 파일 저장 | SQLite | PRD.md §3 Out of Scope 및 §5.2 근거 그대로 — 미션1 4개 PoC가 이미 JSON 스키마로 검증됨, 단일 프로세스 규모에 DB 도입은 과설계 | [ADR-0001](./adr/ADR-0001-JSON파일기반영속성.md) |
| MVC + Service + Repository 4계층 | 단일 스크립트 / Fat Controller | 계산식 중복 방지(SPEC.md §8), 콘솔 I/O와 로직 분리로 테스트 가능성 확보(NFR-4) | [ADR-0002](./adr/ADR-0002-계층형MVC구조채택.md) |
| 생산 진행 상태를 메뉴 진입 시 지연 계산 | 백그라운드 스레드/타이머 | PRD.md §5.5 구현 노트 명시, 단일 프로세스 콘솔 앱에서 스레드 동기화 복잡도 회피, 시간 소스 주입으로 테스트 결정론성 확보 | [ADR-0003](./adr/ADR-0003-생산진행상태갱신방식.md) |
| 단일 생산라인 FIFO 큐 | 다중 라인/우선순위 큐 | PDF·PRD 명세가 "단일 생산라인만 지원"으로 고정, 다중 라인은 Out of Scope | — |
| Repository 공통 베이스 클래스 없음 | `AbstractRepository` 도입 | PoC 원본에도 없음, 2개 Repository만 존재하는 규모에서 추상화는 이득보다 비용이 큼 | — |
| Clock을 함수 인자로 주입 (`now_fn`) | `Clock` 프로토콜 클래스 | DataMonitor 원본 패턴 그대로 재사용, 클래스 도입 없이 동일한 테스트 용이성 확보 | — |
| 승인 시점 재고 예약을 파생값(계산)으로 구현 | `Sample`에 `reserved` 필드 추가 / 승인 시점 즉시 차감 | 스키마 변경·마이그레이션 불필요, "재고는 승인 시점에 차감하지 않는다"는 기존 불변식(SPEC.md §4.2) 유지, `pending_demand`와 동일 패턴 재사용 | [ADR-0004](./adr/ADR-0004-승인시점재고예약.md) |

시스템 전체에 영향을 주거나 되돌리기 어려운 결정은 `docs/adr/`에 별도 ADR로 기록한다(위 표의 "상세" 열). 나머지는 국소적이고 쉽게 되돌릴 수 있어 이 표에만 남긴다.

## 9. 문서 간 책임 분리

- **PRD.md**: 배경/목표/범위/용어/FR·NFR/인수 기준. "무엇을, 왜" 만든다.
- **SPEC.md**: 메뉴별 화면 입출력, 검증 메시지 문구, 계산식(Single Source of Truth 표). "화면에서 무엇이 보이는가".
- **ARCHITECTURE.md(본 문서)**: 모듈 분할, 계층 간 호출 순서, PoC 재사용 매핑, 영속성/예외/테스트 전략. "코드가 어떻게 짜여지는가".

세 문서의 계산식·상태값이 어긋나면 SPEC.md §8을 기준으로 삼는다(구현 세부사항은 이 문서가, 계산 공식의 정본은 SPEC.md가 갖는다).
