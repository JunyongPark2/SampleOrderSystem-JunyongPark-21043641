from sampleorder.exceptions import NotFoundError
from sampleorder.json_store import JsonFileStore
from sampleorder.models import Sample


def _to_dict(sample: Sample) -> dict:
    return {
        "sample_id": sample.sample_id,
        "name": sample.name,
        "avg_production_time": sample.avg_production_time,
        "yield_rate": sample.yield_rate,
        "stock": sample.stock,
    }


def _to_sample(record: dict) -> Sample:
    return Sample(
        sample_id=record["sample_id"],
        name=record["name"],
        avg_production_time=record["avg_production_time"],
        yield_rate=record["yield_rate"],
        stock=record["stock"],
    )


class SampleRepository:
    def __init__(self, store: JsonFileStore):
        self._store = store

    def _next_id(self, records: list) -> str:
        return f"S-{len(records) + 1:03d}"

    def create(self, name: str, avg_production_time: float, yield_rate: float) -> Sample:
        records = self._store.load()
        sample = Sample(
            sample_id=self._next_id(records),
            name=name,
            avg_production_time=avg_production_time,
            yield_rate=yield_rate,
            stock=0,
        )
        records.append(_to_dict(sample))
        self._store.save(records)
        return sample

    def get(self, sample_id: str) -> Sample:
        for record in self._store.load():
            if record["sample_id"] == sample_id:
                return _to_sample(record)
        raise NotFoundError("Sample", sample_id)

    def list_all(self) -> list:
        return [_to_sample(record) for record in self._store.load()]

    def search(self, name_query: str) -> list:
        query = name_query.lower()
        return [sample for sample in self.list_all() if query in sample.name.lower()]

    def update(self, sample_id: str, **fields) -> Sample:
        records = self._store.load()
        for record in records:
            if record["sample_id"] == sample_id:
                record.update(fields)
                self._store.save(records)
                return _to_sample(record)
        raise NotFoundError("Sample", sample_id)
