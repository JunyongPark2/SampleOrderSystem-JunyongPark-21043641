from sampleorder.exceptions import NotFoundError


def find_record(records: list, id_field: str, id_value: str, entity_name: str) -> dict:
    for record in records:
        if record[id_field] == id_value:
            return record
    raise NotFoundError(entity_name, id_value)
