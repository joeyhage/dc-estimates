from typing import TypedDict, List


class JWTClaims(TypedDict):
    aud: str
    iss: str
    iat: int
    exp: int
    groups: List[str]
    ipaddr: str
    name: str
    oid: str
    tid: str
    unique_name: str
    upn: str


class SessionIdentity(TypedDict):
    employee_id: str
    exp: int
    is_admin: bool
    name: str
    payload: JWTClaims
    user_principal_name: str
