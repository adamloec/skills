"""Root of the app's exception hierarchy.

HTTP-layer subclasses live in ``http.py`` and envelope serialization in ``serialization.py``.
"""

from typing import Any, ClassVar


class {{App}}Exception(Exception):
    """Base for every app-defined exception.

    Attributes:
        code: Stable wire identifier. Subclasses override it; it never changes for one.
        status_code: The HTTP status the API layer responds with.
        message: A natural-language sentence, readable by a person or an agent.
        context: Structured fields a programmatic caller would inspect.
        hint: An optional next step for whoever hit this.
        is_retryable: Whether retrying the same input could help.
    """

    code: ClassVar[str] = "{{app}}_error"
    status_code: ClassVar[int] = 500
    default_message: ClassVar[str] = "Something went wrong."

    def __init__(
        self,
        message: str | None = None,
        *,
        context: dict[str, Any] | None = None,
        hint: str | None = None,
        is_retryable: bool = False,
    ) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)
        self.context: dict[str, Any] = dict(context or {})
        self.hint = hint
        self.is_retryable = is_retryable

    def __repr__(self) -> str:
        return f"{type(self).__name__}(code={self.code!r}, message={self.message!r})"
