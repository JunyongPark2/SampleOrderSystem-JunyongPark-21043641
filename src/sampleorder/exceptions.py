class NotFoundError(Exception):
    def __init__(self, entity_name: str, entity_id: str):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} not found: {entity_id}")


class DuplicateError(Exception):
    def __init__(self, entity_name: str, entity_id: str):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} already exists: {entity_id}")


class ValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
