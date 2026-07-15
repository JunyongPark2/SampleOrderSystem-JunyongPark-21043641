# ADR-0002: MVC + Service + Repository 계층형 아키텍처 채택

## 상태
Accepted (2026-07-15)

## 배경
콘솔 애플리케이션이라 화면(View)과 로직을 한 파일에 몰아 넣는 스크립트 형태로도 PDF 명세(Chapter 2)를 충족시킬 수 있다. 그러나 PRD.md NFR-4(테스트 가능성)와 NFR-7(코드 품질/단일 책임)이 "모든 비즈니스 로직은 콘솔 I/O와 분리되어 단위 테스트 가능해야 한다"고 명시하고 있어, 코드를 어떤 계층으로 나눌지는 이후 전체 모듈 구조와 테스트 전략을 좌우하는 결정이다. 한 번 View와 로직이 뒤섞인 채로 개발이 진행되면 나중에 계층을 분리하는 리팩터링 비용이 크다.

## 결정
`views/`(콘솔 입출력 전담) → `controllers/`(메뉴 디스패치·조립) → `services/`(승인 판정/생산 계산/집계 등 비즈니스 로직) → `repositories/`(CRUD) → `json_store.py`(파일 I/O)의 단방향 의존 계층 구조를 채택한다(ARCHITECTURE.md §1). `services/`는 콘솔 I/O를 import하지 않으며, 계산식은 `calculations.py` 한 곳에만 구현한다(SPEC.md §8 Single Source of Truth).

## 고려한 대안
1. **단일 스크립트/트랜잭션 스크립트 패턴** — 메뉴별 함수 하나에 입력→계산→출력을 모두 넣는 방식. 구현 속도는 빠르나 로직이 `input()`/`print()`와 뒤섞여 pytest로 검증하기 어려움.
2. **Fat Controller (View-Controller 2계층만)** — Service 계층 없이 Controller가 재고 비교/생산 계산을 직접 수행. ConsoleMVC 원본 골격과 유사해 보이지만, 계산 로직이 여러 Controller에 중복될 위험(FR-3.2와 FR-5.1이 같은 공식을 쓰는데도 각 Controller에 따로 구현될 수 있음).
3. **MVC + Service + Repository 4계층(채택)** — 미션1 PoC 4종의 검증된 패턴을 통합.

## 선택 이유
- 미션1의 `ConsoleMVC`가 이미 View/Controller 분리와 메뉴 디스패치 패턴(`MainController._actions` 딕셔너리)을 검증했고, `DataPersistence`가 Repository/JsonFileStore 계층을, `DataMonitor`가 Service격 집계 로직(`DataMonitor.order_status_counts` 등)의 분리 방식을 검증했다 — 4개 계층 구조는 새로 설계하는 것이 아니라 이미 검증된 패턴들을 조합하는 것이다.
- SPEC.md §8이 "5개 공식은 서비스 계층에 단일 구현으로 존재해야 하며 화면/메뉴 간 중복 계산을 두지 않는다"고 명시적으로 요구한다 — 이는 Service 계층의 존재를 사실상 전제한다.
- 승인 판정(FR-3.2)과 생산 큐 계산(FR-5.1)이 동일한 계산식(부족분/실생산량/총생산시간)을 공유해야 하므로, Controller가 아닌 별도 계층에 계산 로직을 모아야 중복 구현을 물리적으로 막을 수 있다.

## 장점
- 비즈니스 로직(Service)이 `input()`/`print()`와 완전히 분리되어 pytest 단위 테스트가 콘솔 상호작용 없이 가능(NFR-4, NFR-8).
- 계산식이 한 곳에만 있어 SPEC.md의 계산 규칙이 변경되어도 수정 지점이 하나로 고정됨.
- View를 교체(예: 웹 UI로 전환)해도 Controller 이하 계층을 그대로 재사용 가능.
- 각 계층의 책임이 명확해 NFR-7(단일 책임)을 구조적으로 강제.

## 단점
- 계층이 늘어난 만큼 파일 수와 간접 호출(View→Controller→Service→Repository)이 늘어나, 소규모 기능 하나를 추가할 때도 여러 파일을 오가야 함.
- 과제 규모(개인 콘솔 앱)에 비해 초기 설계/보일러플레이트 비용이 상대적으로 큼 — 팀 개발이 아닌 개인 과제에서는 과설계로 보일 여지가 있음.

## 후속 영향
- 신규 기능 추가 시에도 계산/판정 로직은 반드시 `services/`(또는 `services/calculations.py`)에 두어야 하며, Controller/View에 조건 분기나 계산식을 직접 넣지 않는다.
- 코드 리뷰 시 "Controller/View에 비즈니스 로직이 없는가"를 체크리스트 항목으로 삼을 수 있다.
