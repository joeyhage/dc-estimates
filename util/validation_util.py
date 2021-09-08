import re

from werkzeug.exceptions import BadRequest


def require_numeric(value: str) -> None:
    if not (re.search(r'^\d+$', value)):
        raise BadRequest('Value must be numeric')


def require_alphanumeric(value: str) -> None:
    if not (re.search(r'^[A-Za-z\d]+$', value)):
        raise BadRequest('Value must be alphanumeric')
