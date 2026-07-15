# 구현 계획 개요: 반도체 시료 생산주문관리 시스템

> 근거 문서: [`PRD.md`](../../PRD.md), [`SPEC.md`](../../SPEC.md), [`ARCHITECTURE.md`](../../ARCHITECTURE.md), [`ADR-0001`](../../adr/ADR-0001-JSON파일기반영속성.md)~[`ADR-0003`](../../adr/ADR-0003-생산진행상태갱신방식.md).
> 상태: 계획 단계 — 아직 구현을 시작하지 않았다.
>
> 이 문서는 계획 전체의 공통 맥락(목표/범위/위험/롤백/완료 조건)을 담고, 실제 구현 순서는 Phase별로 분리된 아래 파일에 하나씩 정의한다. 각 Phase 파일은 그 자체로 실행·검증 가능한 단위이며, 순서대로 진행한다(뒤 Phase는 앞 Phase의 산출물에 의존).

## 1. 작업 목표

PDF 과제 명세(Chapter 2 기능 명세)를 100% 충족하는 콘솔 기반 Python 애플리케이션을, ARCHITECTURE.md에서 정의한 View–Controller–Service–Repository 계층 구조로 처음부터 구현한다. 미션1 4개 PoC(ConsoleMVC, DataPersistence, DataMonitor, DummyDataGenerator)의 검증된 패턴을 그대로 재사용하고, PRD.md §9 인수 기준을 모두 만족시킨다.

## 2. 현재 상태

- 저장소에는 문서(`CLAUDE.md`, `docs/PRD.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/adr/*`)만 존재한다.
- `src/`, `tests/`, `main.py`, `data/`, `tools/` 등 실제 코드/디렉터리는 전혀 없다.
- 의존성 선언 파일(`pyproject.toml`, `requirements.txt`)도 없다.

## 3. 목표 상태

- ARCHITECTURE.md §2 디렉터리 구조가 그대로 존재하고, `main.py` 실행 시 콘솔 메뉴가 뜬다.
- PRD.md §9 인수 기준 10개 항목이 모두 수동으로 재현 가능하다.
- `pytest`로 서비스 계층(승인 판정/생산 계산/재고 상태 판정/CRUD) 전체가 콘솔 I/O 없이 검증된다.
- `data/samples.json`, `data/orders.json`이 원자적으로 쓰여지고, 앱 재시작 후에도 상태가 유지된다.

## 4. 작업 범위 (In Scope)

- PRD.md §3 In Scope 전체: 메인 메뉴 + 6개 하위 메뉴, JSON 영속성, 승인 시 재고 판정/생산라인 자동 등록, FIFO 생산 시뮬레이션, 모니터링, 출고 처리, 더미 데이터 생성 도구.
- 서비스 계층 단위 테스트, Repository/JsonStore 통합 테스트.
- `docs/` 문서 갱신(구현 중 SPEC/ARCHITECTURE와 실제 코드가 어긋나는 부분 발견 시).

## 5. 비작업 범위 (Out of Scope)

- PRD.md §3 Out of Scope 전체(웹/GUI, 다중 사용자, 다중 생산라인, 외부 DB, 파일 락).
- CI 파이프라인 구축, 배포 자동화 — 이번 계획은 로컬 구현·테스트까지만 다룬다.
- 성능/부하 테스트 — 콘솔 단일 프로세스 규모를 벗어나는 검증은 하지 않는다.

## 6. Phase 목록 (파일별 1개, 순서대로 진행)

| Phase | 파일 | 내용 |
|---|---|---|
| 0 | [001-phase0-scaffolding.md](./001-phase0-scaffolding.md) | 프로젝트 스캐폴딩 |
| 1 | [002-phase1-domain-model.md](./002-phase1-domain-model.md) | 도메인 모델 & 예외 |
| 2 | [003-phase2-persistence.md](./003-phase2-persistence.md) | 영속성 계층 (JsonFileStore + Repository) |
| 3 | [004-phase3-calculations.md](./004-phase3-calculations.md) | 계산 공식 단일 모듈 |
| 4 | [005-phase4-sample-management.md](./005-phase4-sample-management.md) | 시료 관리 (FR-1.1~1.3) |
| 5 | [006-phase5-order-intake.md](./006-phase5-order-intake.md) | 주문 접수 (FR-2.1) |
| 6 | [007-phase6-order-approval.md](./007-phase6-order-approval.md) | 주문 승인/거절 + 생산라인 연동 (FR-3.1~3.3, FR-5.2) |
| 7 | [008-phase7-production-line.md](./008-phase7-production-line.md) | 생산라인 FIFO 시뮬레이션 (FR-5.1, 5.3~5.5) |
| 8 | [009-phase8-monitoring.md](./009-phase8-monitoring.md) | 모니터링 (FR-4.1~4.2) |
| 9 | [010-phase9-shipping.md](./010-phase9-shipping.md) | 출고 처리 (FR-6.1~6.2) |
| 10 | [011-phase10-main-integration.md](./011-phase10-main-integration.md) | 메인 메뉴 통합 및 진입점 |
| 11 | [012-phase11-dummy-data.md](./012-phase11-dummy-data.md) | 더미 데이터 생성 도구 |
| 12 | [013-phase12-final-verification.md](./013-phase12-final-verification.md) | 통합 검증 및 문서 마감 |

각 Phase 파일은 공통적으로 다음 항목을 포함한다: 목표 / 선행 조건 / 작업 범위·비작업 범위 / 수정·생성 파일 / 구현 단계 / 검증 방법 / 테스트 계획 / 완료 조건. 전체에 걸친 위험·롤백 전략은 아래 7~8절에서 한 번만 다룬다(Phase별 중복 서술 방지).

## 7. 예상 위험 (전체 공통)

| 위험 | 영향 | 완화 방안 |
|---|---|---|
| 승인 판정(FR-3.2)과 생산 큐 계산(FR-5.1)이 각각 다른 곳에서 계산식을 재구현해 값이 어긋남 | 화면마다 다른 부족분/실생산량이 표시되는 버그 | Phase 3에서 `calculations.py`를 먼저 만들고, Phase 6/7은 반드시 이를 import만 하도록 강제(ARCHITECTURE.md §2) |
| `order_id` 날짜별 채번 로직이 동시에 여러 건 생성 시 순번이 꼬임 | 같은 `order_id`가 중복 발급될 가능성 | Phase 2에서 같은 날짜 내 2건 이상 연속 생성 테스트 케이스를 반드시 포함 |
| 생산 진행 상태 갱신(Phase 7)을 메뉴 4/5/6 진입 지점 중 일부에서 누락 | 화면마다 재고/상태 수치가 불일치(ADR-0003 후속 영향에 명시된 위험) | Phase 10에서 `main_controller`가 각 하위 컨트롤러 진입 전에 `production_service.advance()`를 호출하는지 스모크 테스트로 확인 |
| 한글 폭 정렬(`formatting.py`)이 실제 터미널에서 깨짐 | 표 형식이 SPEC.md 예시와 다르게 보임 | Phase 4에서 만들어 이후 모든 View가 공유, 수동 검증 시 실제 터미널에서 표 정렬 육안 확인 |
| PoC 원본과 실제 요구사항(SPEC.md) 간 세부 차이(예: 메시지 문구) | PoC 코드를 그대로 복붙하면 SPEC.md 문구와 달라질 수 있음 | 문구는 항상 SPEC.md를 최종 기준으로 하고, PoC는 구조/패턴만 참고(ARCHITECTURE.md §9 명시) |

## 8. 롤백 방법 (전체 공통)

- 각 Phase는 별도 커밋 단위로 진행한다(CLAUDE.md 커밋 규율: 작은 단위 완료 시마다 커밋). 특정 Phase에서 문제가 발견되면 `git revert <해당 Phase 커밋>`으로 해당 단위만 되돌리고, 이전 Phase까지의 결과물은 보존한다.
- `data/` 디렉터리는 `.gitignore` 대상(런타임 생성물)이므로, 데이터 손상 시 파일만 삭제하고 `tools/dummy_data_cli.py`(Phase 11)로 재시딩하면 코드 롤백과 무관하게 복구 가능하다.
- 계층 간 의존 방향(View→Controller→Service→Repository)을 지키는 한, 특정 Phase(예: Phase 8 모니터링)를 통째로 되돌려도 다른 Phase(예: Phase 9 출고)는 영향받지 않는다 — 이는 ADR-0002가 의도한 격리 효과다.

## 9. 전체 테스트 전략

- **단위 테스트**: 계층별로 순수 함수/서비스 로직 테스트(콘솔 I/O 없음). `tests/conftest.py`의 `tmp_path` fixture로 실제 `data/`를 훼손하지 않는다(NFR-8). 시간 의존 로직(`production_service`)은 고정 `now_fn` fixture로 결정론적으로 검증한다(NFR-4).
- **통합 테스트**: Phase 10의 `test_main_controller_smoke.py`(디스패치 스모크), Phase 2의 Repository↔JsonFileStore 통합 테스트.
- **수동 시나리오 테스트**: 각 Phase 말미에 SPEC.md의 해당 절 예시 화면과 실제 콘솔 출력을 대조. Phase 12에서 PRD.md §9 인수 기준 전체를 한 번에 재현.
- **테스트 우선순위**: 계산식(Phase 3) > 승인 판정(Phase 6) > 생산 완료 처리(Phase 7) — 이 세 곳이 PRD.md 인수 기준에서 가장 자주 언급되는 로직이므로 가장 두텁게 테스트한다.

## 10. 전체 완료 조건

- [x] Phase 0~12 파일이 모두 완료 체크됨.
- [x] `pytest` 전체 스위트가 통과함(NFR-8) — 68 passed.
- [x] PRD.md §9 인수 기준 10개 항목이 모두 수동 재현으로 확인됨(`docs/plans/completed/013-phase12-final-verification.md` 참고).
- [x] `python main.py`를 재시작해도 이전 세션의 시료/주문 데이터가 유지됨(NFR-1) — 단, 생산라인 큐 자체는 메모리 전용이라 재시작 시 유실되는 한계가 있음(아래 "전체 완료 후 남은 위험" 참고).
- [x] SPEC.md에 정의된 모든 화면 문구/계산식이 실제 콘솔 출력과 정확히 일치함(수동 시나리오로 Phase별 확인).
- [x] 완료 후 본 계획(overview + 13개 Phase 파일)은 `docs/plans/completed/`로 이동함.

## 11. 전체 완료 후 남은 위험 (Phase 10에서 발견, Phase 12에서 최종 확인)

생산라인 큐(`ProductionService._queue`)는 메모리에만 존재하고 JSON으로 영속화되지 않는다. `PRODUCING` 상태로 승인된 주문이 있는 상태에서 앱을 재시작하면, `orders.json`의 상태는 `PRODUCING`으로 정상 유지되지만 큐 자체(부족분/실생산량/총생산시간/시작 시각)는 사라져 `advance()`를 아무리 호출해도 그 주문은 다시 큐에 들어가지 않는 한 영원히 `PRODUCING`에 머무른다.

- 데이터 손상/유실은 아니다(JSON 파일 자체는 항상 일관된 상태로 저장됨) — 재고·주문 데이터 자체의 NFR-1 요구사항은 충족한다.
- PRD.md §9 인수 기준 10개 항목 자체는 "앱을 껐다 켜도 데이터가 유지되는가"를 요구할 뿐 "PRODUCING 상태에서 재시작해도 생산이 이어지는가"까지는 명시하지 않아, 좁은 의미의 인수 기준은 통과한다.
- 다만 ARCHITECTURE.md §5(저장 파일이 `samples.json`/`orders.json` 2개뿐)와 NFR-1의 "이전 상태를 그대로 복원"이라는 문구 사이에는 간극이 있으며, 이는 계획 문서 어디에도 큐 영속화가 명시되지 않았던 설계 공백이다.
- 이번 계획 범위에서는 각 Phase의 명시된 비작업 범위(신규 비즈니스 로직 없음)를 지키기 위해 임의로 복구 로직을 추가하지 않았다. 필요 시 별도 후속 작업(예: 앱 시작 시 `PRODUCING` 주문을 스캔해 큐를 재구성하는 기능)으로 사용자 확인 후 진행해야 한다.
