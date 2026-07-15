# Phase 0: 프로젝트 스캐폴딩

> 개요/공통 위험·롤백은 [000-overview.md](./000-overview.md) 참고.

## 목표

`src/sampleorder/`, `tests/`, `tools/`, `data/` 디렉터리와 패키지 골격, 의존성 선언 파일을 만들어 이후 모든 Phase가 코드를 채워 넣을 수 있는 빈 구조를 준비한다.

## 선행 조건

없음(첫 Phase).

## 작업 범위

- `pyproject.toml`/`requirements.txt` 작성(pytest 의존성 포함).
- `src/sampleorder/`, `src/sampleorder/repositories/`, `src/sampleorder/services/`, `src/sampleorder/views/`, `src/sampleorder/controllers/`, `tests/`, `tools/`, `data/` 디렉터리 생성.
- 각 패키지에 빈 `__init__.py` 생성.
- `main.py`는 placeholder(`print("not implemented")` 수준)만 둔다.

## 비작업 범위

- 실제 도메인 로직, 모델, 서비스 구현 — 다음 Phase부터 시작.

## 수정하거나 생성할 파일

```
pyproject.toml
requirements.txt
main.py
src/sampleorder/__init__.py
src/sampleorder/repositories/__init__.py
src/sampleorder/services/__init__.py
src/sampleorder/views/__init__.py
src/sampleorder/controllers/__init__.py
tests/__init__.py (필요 시)
data/.gitkeep
```

## 구현 단계

1. `pyproject.toml`에 프로젝트 메타데이터 + pytest를 dev 의존성으로 선언.
2. 디렉터리 구조 생성 및 빈 `__init__.py` 배치.
3. `main.py`에 placeholder 진입점 작성(`if __name__ == "__main__":` 블록).
4. `data/.gitkeep`으로 빈 디렉터리를 커밋 가능하게 하되, 실제 `*.json`은 `.gitignore`에 추가.

## 검증 방법

- `pip install -e .`(또는 `pip install -r requirements.txt`) 실행 후 에러 없이 완료.
- `pytest --collect-only` 실행 시 에러 없이 0개 테스트 수집(아직 테스트 파일 없음).
- `python main.py` 실행 시 예외 없이 placeholder 문구 출력.

## 테스트 계획

이 Phase는 구조 생성만 다루므로 별도 자동화 테스트를 작성하지 않는다. 위 "검증 방법"의 명령어 실행 결과로 충분하다.

## 완료 조건

- [x] 디렉터리/파일 구조가 ARCHITECTURE.md §2와 일치.
- [x] `pytest --collect-only`, `python main.py`가 에러 없이 실행됨.
- [x] `git status`에서 의도한 파일만 추가됨을 확인.

## 진행 기록

- `pyproject.toml`(setuptools, `src/` 레이아웃), `requirements.txt`(pytest), `main.py`(placeholder) 생성.
- `src/sampleorder/{repositories,services,views,controllers}/__init__.py`, `tests/__init__.py`, `data/.gitkeep` 생성.
- `.gitignore`에 `__pycache__/`, `*.pyc`, `.pytest_cache/`, `*.egg-info/`, `data/*.json`, `.venv/` 추가.
- `tools/` 디렉터리는 Phase 11(더미 데이터 도구)에서 실제 파일과 함께 생성하기로 하고 이번 Phase에서는 만들지 않음(빈 디렉터리는 git에 추적되지 않으므로 실익 없음) — ARCHITECTURE.md §2 구조와 차이 없음.
- 검증: `.venv/bin/python -m pytest --collect-only` → 0 items 수집(에러 없음), `.venv/bin/python main.py` → `not implemented` 출력.
