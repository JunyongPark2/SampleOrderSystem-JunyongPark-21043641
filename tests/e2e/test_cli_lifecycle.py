import json


def test_full_order_lifecycle_via_real_cli(run_cli):
    inputs = [
        "1",            # 메인: 시료 관리
        "1",            # 시료 관리: 시료 등록
        "테스트시료",
        "10",           # 평균 생산시간(분)
        "0.9",          # 수율
        "100",          # 재고
        "0",            # 시료 관리 메뉴 뒤로가기
        "2",            # 메인: 시료 주문
        "S-001",
        "고객A",
        "20",           # 주문 수량
        "Y",            # 예약 접수 확인
        "3",            # 메인: 주문 승인/거절
        "1",            # 승인 대기 목록 1번 선택
        "Y",            # 승인
        "4",            # 메인: 모니터링
        "1",            # 주문량 확인
        "2",            # 재고량 확인
        "0",            # 모니터링 메뉴 뒤로가기
        "6",            # 메인: 출고 처리
        "1",            # 출고 가능 목록 1번 선택
        "0",            # 종료
    ]

    result = run_cli(inputs)

    assert result.returncode == 0, result.stderr
    assert "등록 완료." in result.stdout
    assert "예약 접수 완료." in result.stdout
    assert "승인 완료." in result.stdout
    assert "상태 변경   RESERVED → CONFIRMED" in result.stdout
    assert "CONFIRMED   1건" in result.stdout
    assert "출고 처리 완료." in result.stdout
    assert "상태       CONFIRMED → RELEASE" in result.stdout

    samples = result.read_json("samples.json")
    orders = result.read_json("orders.json")
    assert len(samples) == 1
    assert samples[0]["stock"] == 80  # 100 - 출고수량 20
    assert len(orders) == 1
    assert orders[0]["status"] == "RELEASE"
    assert orders[0]["quantity"] == 20


def test_shortage_approval_enqueues_production_and_blocks_shipping(run_cli):
    inputs = [
        "1",            # 메인: 시료 관리
        "1",            # 시료 관리: 시료 등록
        "부족시료",
        "10",           # 평균 생산시간(분)
        "0.8",          # 수율
        "30",           # 재고 (주문 수량보다 적음)
        "0",            # 시료 관리 메뉴 뒤로가기
        "2",            # 메인: 시료 주문
        "S-001",
        "고객B",
        "200",          # 주문 수량 (재고 부족)
        "Y",            # 예약 접수 확인
        "3",            # 메인: 주문 승인/거절
        "1",
        "Y",            # 부족분 확인 화면에서 승인
        "Y",            # 부족분 승인 확정
        "5",            # 메인: 생산라인 조회
        "6",            # 메인: 출고 처리 (아직 CONFIRMED 아니므로 목록 비어야 함)
        "0",            # 종료
    ]

    result = run_cli(inputs)

    assert result.returncode == 0, result.stderr
    assert "재고 부족. 부족분 170 ea 승인하시겠습니까?" in result.stdout
    assert "승인 완료." in result.stdout
    assert "상태 변경   RESERVED → PRODUCING" in result.stdout
    assert "현재 처리 중" in result.stdout
    assert "출고 가능한 주문이 없습니다." in result.stdout

    orders = result.read_json("orders.json")
    assert len(orders) == 1
    assert orders[0]["status"] == "PRODUCING"


def test_rejecting_reserved_order_transitions_to_rejected(run_cli):
    inputs = [
        "1", "1", "거절시료", "10", "0.9", "50", "0",
        "2", "S-001", "고객C", "10", "Y",
        "3",            # 메인: 주문 승인/거절
        "1",
        "N",            # 거절
        "0",
    ]

    result = run_cli(inputs)

    assert result.returncode == 0, result.stderr
    assert "거절 처리 완료." in result.stdout
    assert "상태 변경   RESERVED → REJECTED" in result.stdout

    orders = result.read_json("orders.json")
    assert orders[0]["status"] == "REJECTED"


def test_no_pending_approval_or_shippable_orders_shows_empty_messages(run_cli):
    result = run_cli(["3", "6", "0"])

    assert result.returncode == 0, result.stderr
    assert "승인 대기 중인 주문이 없습니다." in result.stdout
    assert "출고 가능한 주문이 없습니다." in result.stdout


def test_sample_registration_reprompts_on_invalid_stock_then_succeeds(run_cli):
    inputs = [
        "1",            # 메인: 시료 관리
        "1",            # 시료 등록
        "검증시료",
        "10",
        "0.9",
        "-5",           # 잘못된 재고 (음수) -> 재입력 요구
        "50",           # 올바른 재고
        "0",
        "0",
    ]

    result = run_cli(inputs)

    assert result.returncode == 0, result.stderr
    assert "재고는 0 이상의 정수여야 합니다. 다시 입력해주세요." in result.stdout
    assert "등록 완료." in result.stdout

    samples = result.read_json("samples.json")
    assert samples[0]["stock"] == 50


def test_shipping_reports_insufficient_stock_when_stock_drops_after_confirmation(run_cli):
    setup_inputs = [
        "1", "1", "품절시료", "10", "0.9", "50", "0",
        "2", "S-001", "고객D", "50", "Y",
        "3", "1", "Y",
        "0",
    ]
    setup_result = run_cli(setup_inputs)
    assert setup_result.returncode == 0, setup_result.stderr

    samples_path = setup_result.data_dir / "samples.json"
    samples = json.loads(samples_path.read_text(encoding="utf-8"))
    samples[0]["stock"] = 0  # 확정 이후 외부 요인으로 재고가 소진된 상황을 재현
    samples_path.write_text(json.dumps(samples, ensure_ascii=False), encoding="utf-8")

    shipping_result = run_cli(["6", "1", "0"], data_dir=setup_result.data_dir)

    assert shipping_result.returncode == 0, shipping_result.stderr
    assert "재고가 부족하여 출고할 수 없습니다. 재고를 확인해주세요." in shipping_result.stdout

    orders = shipping_result.read_json("orders.json")
    assert orders[0]["status"] == "CONFIRMED"


def test_ordering_unknown_sample_id_shows_error_and_creates_no_order(run_cli):
    inputs = [
        "2",            # 메인: 시료 주문
        "S-999",        # 존재하지 않는 시료 ID
        "0",            # 종료
    ]

    result = run_cli(inputs)

    assert result.returncode == 0, result.stderr
    assert "존재하지 않는 시료 ID입니다. 주문을 생성하지 않았습니다." in result.stdout
    assert result.read_json("orders.json") == []


def test_invalid_main_menu_choice_shows_message_and_redisplays_menu(run_cli):
    from sampleorder.views.formatting import INVALID_CHOICE_MESSAGE

    result = run_cli(["9", "0"])

    assert result.returncode == 0, result.stderr
    assert INVALID_CHOICE_MESSAGE in result.stdout
