import pytest

from sampleorder.exceptions import ValidationError
from sampleorder.services.sample_service import (
    AVG_PRODUCTION_TIME_ERROR,
    STOCK_ERROR,
    YIELD_RATE_ERROR,
    SampleService,
)


@pytest.fixture
def sample_service(sample_repository):
    return SampleService(sample_repository)


def test_register_rejects_non_positive_avg_production_time(sample_service):
    with pytest.raises(ValidationError) as excinfo:
        sample_service.register("A", 0, 0.9, 10)
    assert str(excinfo.value) == AVG_PRODUCTION_TIME_ERROR
    assert sample_service.list_all() == []


def test_register_rejects_yield_rate_out_of_range(sample_service):
    for invalid_rate in (0, -0.1, 1.1):
        with pytest.raises(ValidationError) as excinfo:
            sample_service.register("A", 0.5, invalid_rate, 10)
        assert str(excinfo.value) == YIELD_RATE_ERROR
    assert sample_service.list_all() == []


def test_register_rejects_invalid_stock(sample_service):
    for invalid_stock in (-1, 1.5, "10", True):
        with pytest.raises(ValidationError) as excinfo:
            sample_service.register("A", 0.5, 0.9, invalid_stock)
        assert str(excinfo.value) == STOCK_ERROR
    assert sample_service.list_all() == []


def test_register_succeeds_with_user_supplied_stock_and_sequential_ids(sample_service):
    first = sample_service.register("A", 0.5, 0.9, 25)
    second = sample_service.register("B", 0.3, 0.8, 0)
    assert first.stock == 25
    assert second.stock == 0
    assert first.sample_id == "S-001"
    assert second.sample_id == "S-002"


def test_search_is_case_insensitive_substring(sample_service):
    sample_service.register("GaN 에피택셜", 0.3, 0.8, 5)
    results = sample_service.search("gan")
    assert len(results) == 1


def test_search_returns_empty_list_when_no_match(sample_service):
    sample_service.register("A", 0.5, 0.9, 5)
    assert sample_service.search("존재하지않음") == []
