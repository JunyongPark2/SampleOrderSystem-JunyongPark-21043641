# SampleOrderSystem

반도체 시료 생산주문관리 시스템 — 콘솔 기반 Python 애플리케이션.

가상의 반도체 회사 "S-Semi"가 고객 주문에 따라 시료(Sample)를 생산·검수·출고하는 과정을
관리한다. 시료 등록, 주문 접수, 승인/거절, 생산라인(FIFO) 시뮬레이션, 모니터링, 출고 처리를
하나의 콘솔 메뉴에서 수행한다.

## 요구 사항

- Python 3.10 이상

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

`requirements.txt`를 사용해도 된다(`pytest`만 설치):

```bash
pip install -r requirements.txt
```

## 실행

```bash
python main.py
```

`main.py`는 실행 시 `src/`를 `sys.path`에 직접 추가하므로, 별도 설치 없이 시스템 파이썬으로
바로 실행해도 동작한다:

```bash
python3 main.py
```

단, `pytest`는 이 방식이 적용되지 않으므로 테스트를 실행하려면 위 설치 과정(`pip install -e .`)이
반드시 필요하다.

실행하면 메인 메뉴가 표시된다.

```
[1] 시료 관리        [2] 시료 주문
[3] 주문 승인/거절    [4] 모니터링
[5] 생산라인 조회     [6] 출고 처리
[0] 종료
```

데이터는 `data/samples.json`, `data/orders.json`에 저장되며, 앱을 재시작해도 유지된다.

## 더미 데이터 생성

빈 상태로 처음 실행하면 시료/주문이 하나도 없다. 시연·테스트용 초기 데이터를 채우려면:

```bash
python tools/dummy_data_cli.py --samples 12 --orders 36 --seed 42
```

- `--samples`: 생성할 시료 종수 (기본 12)
- `--orders`: 생성할 주문 건수 (기본 36)
- `--seed`: 재현 가능한 난수 시드 (생략 시 매번 다른 데이터)

## 테스트

```bash
pytest
```

서비스 계층(승인 판정, 생산 계산, 재고 상태 판정, CRUD 등)을 콘솔 입출력과 분리해 단위/통합
테스트로 검증한다. `tests/conftest.py`가 `tmp_path` 기반 격리 저장소를 제공하므로 테스트 실행이
실제 `data/`를 훼손하지 않는다.

## 프로젝트 구조

```
main.py                  # 진입점
src/sampleorder/
  models.py               # Sample, Order, OrderStatus
  exceptions.py           # NotFoundError, DuplicateError, ValidationError
  json_store.py           # 원자적 JSON 파일 입출력
  clock.py                # 시간 소스 주입(now_fn)
  repositories/            # CRUD + 조건 조회
  services/                # 비즈니스 로직(계산식, 승인/생산/모니터링/출고)
  views/                   # 콘솔 입출력
  controllers/              # 메뉴 디스패치
tools/
  dummy_data_cli.py        # 더미 데이터 생성 도구
data/                       # samples.json, orders.json (런타임 생성, git 추적 제외)
tests/                      # pytest 테스트 스위트
docs/                       # PRD, SPEC, ARCHITECTURE, ADR, 구현 계획
```

## 문서

- [`docs/PRD.md`](docs/PRD.md) — 배경/목표/범위/기능 요구사항/인수 기준
- [`docs/SPEC.md`](docs/SPEC.md) — 메뉴별 화면 입출력, 검증 메시지, 계산식
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — 계층 구조, 디렉터리 구성, 시퀀스, 영속성/예외/테스트 전략
- [`docs/adr/`](docs/adr/) — 되돌리기 어려운 설계 결정 기록
- [`docs/plans/completed/`](docs/plans/completed/) — Phase별 구현 계획 및 진행 기록
- [`CLAUDE.md`](CLAUDE.md) — 개발 가이드/컨벤션

## 알려진 제한 사항

생산라인 큐는 메모리에만 존재하며 JSON으로 영속화되지 않는다. `PRODUCING` 상태 주문이 있는
채로 앱을 재시작하면 큐 자체(부족분/실생산량/총생산시간/시작 시각)가 사라져 해당 주문은 큐에
다시 등록되지 않는 한 계속 `PRODUCING`에 머무른다. 자세한 내용은
[`docs/plans/completed/000-overview.md`](docs/plans/completed/000-overview.md) §11 참고.
