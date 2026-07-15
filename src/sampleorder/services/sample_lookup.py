from sampleorder.repositories.sample_repository import SampleRepository


def sample_name_map(orders: list, sample_repository: SampleRepository) -> dict:
    return {order.sample_id: sample_repository.get(order.sample_id).name for order in orders}
