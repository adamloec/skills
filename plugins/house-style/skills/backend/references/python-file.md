# Python file anatomy

## Order

1. Module docstring
2. `from __future__ import annotations` (only when forward refs need it)
3. Imports: stdlib, then third-party, then first-party
4. Module constants, each followed by an attribute docstring
5. `logger = get_logger("...")`
6. Type aliases (`Name = Annotated[...]` plus an attribute docstring)
7. Public classes and functions
8. Private `_helpers`, placed just below their first caller

A router module is: docstring → imports → `router = APIRouter(...)` → private helpers →
handlers.

```python
"""Note routes — CRUD over the caller's notes.

Handlers validate the request shape and delegate to ``NoteService``.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Query

from acme_api.api.deps.session import SessionDep
from acme_api.models.note import Note, NotePage
from acme_api.services.note_service import NoteService

PAGE_SIZE_MAX = 200
"""The largest page a list route returns."""

router = APIRouter()
```

## Docstrings: the one rule

**Documentation attaches to a declaration, never to a statement.** A module, class, function
or field gets a docstring. Nothing inside a function body gets a comment.

- **Summary line first.** It is one line, imperative mood, and ends with a period. A blank line
  follows before anything else. If the summary needs two lines, the function needs a better
  name or a smaller job.
- **Google style.** Use `Args:`, `Returns:`, `Raises:` and `Attributes:`. Omit any section that
  would be empty. A one-argument function whose name says everything gets no `Args:`. A
  one-line docstring is normal.
- **Never restate a type.** The annotation is the type. Describe the meaning and the
  constraint.
- **Document the contract.** Say what a caller must know and cannot read from the signature:
  ordering, `None` behaviour, mutation, commit behaviour ("The session is not committed."),
  lifecycle ownership, failure mode.
- **Always list `Raises:`** for typed errors a caller may want to handle.
- **Module docstrings.** One line when the filename plus a clause covers it. Write a paragraph
  when the module is a seam: say what is here and what deliberately is not. Many open with
  `Name — role.`
- **Constants and type aliases** carry an attribute docstring, a bare string on the next
  line.
- **Fields carry their own description** via `Field(description=...)`. It reaches OpenAPI,
  where a `#` comment never would.
- **`__init__.py`:** an empty one stays zero bytes. A facade gets a package docstring.
- **Tests:** a test file gets a docstring only when its setup is non-obvious. A test function
  gets one only when its name cannot carry the case.

```python
def resolve_reference(ref: str, sources: dict[str, Any], *, strict: bool = False) -> Any:
    """Resolve a ``{{node.field}}`` reference against upstream outputs.

    Args:
        ref: Reference expression, e.g. ``"{{parser.rows[0].total}}"``.
        sources: Node id to that node's output value.
        strict: Raise on an unresolvable path instead of returning ``None``.

    Returns:
        The resolved value, preserving its type. A ref embedded in text returns a string.

    Raises:
        BadRequestError: The path does not exist and ``strict`` is set.
    """
```

**Delete on sight:**
- comments in function bodies
- section banners (`# ---- helpers ----`)
- rationale paragraphs above assignments
- commented-out code
- author, date and changelog headers
- restatements
- a `TODO` with no issue link

If a line needs explaining, extract a well-named local or function. Design rationale belongs in
an ADR or a doc, not in the code.

**Keep:**
- tool pragmas (`# noqa: F401`, `# type: ignore[arg-type]`, `# pragma: no cover`)
- shebangs
- generated-file headers

The only exception is a **non-obvious external constraint**: an upstream's undocumented
behaviour, or a library bug being worked around. It becomes one sentence in the enclosing
function's docstring.

Alembic migration bodies are exempt from the no-comment rule.

## Imports

- **Absolute only.** There are no relative imports anywhere.
- Three groups, each sorted, with one blank line between groups: stdlib, third-party,
  first-party. A shared library (`<app>_core`) and the app itself go in **one** first-party
  block.
- Import modules' names directly: `from sqlmodel import Field, select`. Use `import uuid` for
  stdlib modules used as namespaces.
- `if TYPE_CHECKING:` only to break a real import cycle. Lazy in-function imports only for heavy
  optional dependencies.
- If a name collides, alias it: `from pydantic import BaseModel as PydanticBaseModel` when the
  db `BaseModel` is also in scope.

## Typing

- Annotate every parameter and every return, including `-> None`.
- Use `X | None`, `list[...]`, `dict[...]` and `tuple[...]`. Never use `Optional`, `List`,
  `Dict` or `Union`.
- Import `AsyncGenerator`, `Callable`, `Mapping` and `Sequence` from `collections.abc`. Use
  `AsyncGenerator[T]` with a single argument.
- Use `typing.Self` for fluent and validator returns, `Literal[...]` for small closed modes, and
  `StrEnum` for vocabularies that persist.
- Type aliases use `Name = Annotated[...]`. Do not use `type X = ...`, and do not use
  `TypeAlias`.
- `# type: ignore[...]` always names the rule. It is a last resort.

## Formatting

There is no formatter. Lint with ruff (`E`, `F`, `I`, `UP`, `B`, `D`) and format by hand to
these rules:

- **Line length: 100.**
- Double quotes.
- 4-space indent.
- Two blank lines between top-level definitions, one between methods.
- **Wrapped calls are compact, with a trailing comma.** Put several arguments per continuation
  line and the closing bracket on its own line. Do not explode to one argument per line unless
  the arguments are long.
  ```python
  raise HTTPException(
      status_code=503, detail="Operator actions are disabled (no admin secret configured)",
  )
  ```
- Long signatures break one parameter per line, with a trailing comma, when they would not fit
  on two lines.
- Use numeric separators for big literals: `20_000`.
- Use f-strings for interpolation, except in log messages (see `errors-and-logging.md`).
