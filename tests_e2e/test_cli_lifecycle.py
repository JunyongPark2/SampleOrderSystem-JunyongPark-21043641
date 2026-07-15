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
        "0",            # 종료
    ]

    result = run_cli(inputs)

    assert result.returncode == 0, result.stderr
    assert "등록 완료." in result.stdout
    assert "예약 접수 완료." in result.stdout
    assert "승인 완료." in result.stdout
    assert "상태 변경   RESERVED → CONFIRMED" in result.stdout
    assert "CONFIRMED   1건" in result.stdout

    samples = result.read_json("samples.json")
    orders = result.read_json("orders.json")
    assert len(samples) == 1
    assert samples[0]["stock"] == 100
    assert len(orders) == 1
    assert orders[0]["status"] == "CONFIRMED"
    assert orders[0]["quantity"] == 20


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
