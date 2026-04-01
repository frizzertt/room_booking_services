from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import APIError
from app.core.security import Principal, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Principal:
    if credentials is None:
        raise APIError(status_code=401, code="UNAUTHORIZED", message="authorization required")

    if credentials.scheme.lower() != "bearer":
        raise APIError(status_code=401, code="UNAUTHORIZED", message="invalid auth scheme")

    return decode_access_token(credentials.credentials)


def require_roles(*roles: str) -> Callable[[Principal], Principal]:
    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in roles:
            raise APIError(status_code=403, code="FORBIDDEN", message="insufficient permissions")
        return principal

    return dependency
