"""Caller identity — the seam every authenticated route depends on.

``require_user`` fails closed until a real verifier is wired in: an OIDC access token verified
offline against the issuer's JWKS, or an identity asserted by a trusted proxy and proven by a
shared secret. Tests override it.
"""

from typing import Annotated

from fastapi import Depends

from {{pkg}}.api.context import Principal
from {{pkg}}.lib.exceptions import UnauthenticatedError


async def require_user() -> Principal:
    """Resolve the verified caller.

    Raises:
        UnauthenticatedError: Always, until an identity verifier is configured.
    """
    raise UnauthenticatedError("No identity verifier is configured")


UserDep = Annotated[Principal, Depends(require_user)]
