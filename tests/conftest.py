from datetime import datetime, timezone

import pytest

from sampleorder.json_store import JsonFileStore
from sampleorder.repositories.order_repository import OrderRepository
from sampleorder.repositories.sample_repository import SampleRepository


@pytest.fixture
def fixed_now():
    return datetime(2026, 4, 16, 9, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_store(tmp_path):
    return JsonFileStore(tmp_path / "samples.json")


@pytest.fixture
def order_store(tmp_path):
    return JsonFileStore(tmp_path / "orders.json")


@pytest.fixture
def sample_repository(sample_store):
    return SampleRepository(sample_store)


@pytest.fixture
def order_repository(order_store, fixed_now):
    return OrderRepository(order_store, now_fn=lambda: fixed_now)


@pytest.fixture
def queue_store(tmp_path):
    return JsonFileStore(tmp_path / "production_queue.json")
