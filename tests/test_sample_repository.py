import pytest

from sampleorder.exceptions import NotFoundError


def test_create_initializes_stock_to_zero(sample_repository):
    sample = sample_repository.create("실리콘 웨이퍼", 0.5, 0.9)
    assert sample.stock == 0


def test_sample_ids_are_sequential(sample_repository):
    first = sample_repository.create("A", 0.5, 0.9)
    second = sample_repository.create("B", 0.3, 0.8)
    assert first.sample_id == "S-001"
    assert second.sample_id == "S-002"


def test_search_matches_substring_case_insensitive(sample_repository):
    sample_repository.create("GaN 에피택셜", 0.3, 0.8)
    sample_repository.create("SiC 파워기판", 0.8, 0.92)

    results = sample_repository.search("gan")

    assert len(results) == 1
    assert results[0].name == "GaN 에피택셜"


def test_get_raises_not_found_for_unknown_id(sample_repository):
    with pytest.raises(NotFoundError):
        sample_repository.get("S-999")


def test_update_overwrites_given_fields(sample_repository):
    sample = sample_repository.create("A", 0.5, 0.9)
    updated = sample_repository.update(sample.sample_id, stock=42)
    assert updated.stock == 42
