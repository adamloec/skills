"""Per-request trusted context: who the verified caller is."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Principal:
    """A verified caller and the organization they act in.

    Attributes:
        user_id: Stable id of the verified user.
        org_id: The organization every scoped read and write is bound to.
    """

    user_id: str
    org_id: str
