# Naming

## Modules and packages

| Thing | Pattern | Example |
|---|---|---|
| Package | `<app>_<role>` | `acme_api`, `acme_core` |
| Route module | plural noun | `routes/invoices.py`, `routes/spend_limits.py` |
| Model module | singular noun | `models/invoice.py` |
| Service module | `<domain>_service.py` | `invoice_service.py` |
| Repository module | `<entity>_repository.py` | `invoice_repository.py` |
| Middleware module | `<thing>_middleware.py`, or `exception_handler.py` | `edge_caller_middleware.py` |
| Migration | `NNNN_snake_slug.py` | `0007_invoice_due_date.py` |
| Test file | `test_<behaviour or resource>.py` | `test_invoices.py`, `test_patch_is_strict.py` |

## Classes

| Role | Pattern | Example |
|---|---|---|
| Table model | singular PascalCase noun, **no suffix** | `Invoice`, `ApiCredential` |
| Create body (only if it differs from the model) | `<Entity>Create` | `InvoiceCreate` |
| Command body | `<Verb><Noun>Request` | `SendInvoiceRequest` |
| Page / list shapes | `<Entity>Page`, `<Entity>ListItem`, `<Entity>Summary` | `InvoicePage{items, next_cursor}` |
| Worker payloads | `<Verb><Noun>Input`, `<Verb><Noun>Result` | `RenderInvoiceInput` |
| Service | `<Domain>Service` | `InvoiceService` |
| Repository | `<Entity>Repository` | `InvoiceRepository` |
| Settings | `CoreSettings` (shared infra), `<Role>Settings` (one service) | `ApiSettings`, `WorkerSettings`, `AuthSettings` |
| Exception root | `<App>Exception` | `AcmeException` |
| Exception | `<Meaning>Error` | `NotFoundError`, `ConflictError`, `UpstreamError` |
| Middleware | `<Thing>Middleware` | `EdgeCallerMiddleware` |
| Plugin ABC | `Base<Kind>` | `BaseProvider` |
| Catalog spec | `<Kind>Spec` | `ProviderSpec` |
| Protocol seam | capability noun | `FileStore`, `RunScope` |
| Value object | plain noun | `Decision`, `ForwardedScope`, `SecurityContext` |
| Infra client | the thing it wraps | `Database`, `HttpPool`, `RedisClient`, `Storage` |
| Enum | singular noun | `InvoiceStatus` |

**Never** name a class `*Response`, `*Read`, `*Update`, `*DTO`, `*Schema`, `*Manager` or
`*Helper`.

## Functions and methods

**Route handlers** are `verb_noun`:

| Verb | Use |
|---|---|
| `list_<plural>` | collection read |
| `get_<singular>` | item read |
| `create_<singular>` | create |
| `update_<singular>` | patch |
| `delete_<singular>` | delete |
| `<action>_<singular>` | commands: `cancel_invoice`, `send_invoice` |

**Repository methods:**

| Prefix | Meaning |
|---|---|
| `get_by_<field>` | single lookup by a field |
| `get_for_<scope>` | single lookup bound to a scope |
| `list_by_<field>`, `list_for_<owner>` | filtered lists |
| `list_page` | keyset-paginated list |
| `delete_by_<field>`, `delete_for_<scope>` | scoped deletes |
| `ensure_<thing>` | race-safe get-or-create |
| `get_or_404`, `get_for_update_or_404` | load, or raise `NotFoundError` |
| `is_<condition>`, `exists_<thing>` | boolean queries |

**Service methods:** use the CRUD verbs plus these prefixes:
- `validated_<thing>` / `checked_<thing>` return a validated value
- `resolve_*`, `apply_*`, `sync_*`, `record_*`, `seed_*`
- `delete_for_scope` is the hook a parent calls when it deletes its children

**Dependencies:**

| Pattern | Meaning |
|---|---|
| `get_<thing>` | yield or build a resource (`get_session`) |
| `require_<condition>` | gate: raise, or return the principal (`require_user`, `require_admin_secret`) |
| `require_<x>_permission(perm)` | factory returning an inner `async def gate(...)` |
| `load_<thing>` | parse trusted input into a context (`load_context`) |
| `<Thing>Dep` | the `Annotated[T, Depends(...)]` alias (`SessionDep`, `UserDep`) |

**Constructors and conversions:**
- Named constructors are classmethods: `of(...)`, `from_<source>(...)`, `for_<purpose>(...)`.
- Serializers are `to_<format>()`: `to_envelope`, `to_headers`.
- Cursor helpers are `encode_cursor` / `decode_cursor`.

**Leading underscore:** only for instance state (`self._client`). There are no private
functions, private modules or private constants. Everything a module defines is public and
documented.

## Variables, constants and fields

- **Constants:** `UPPER_SNAKE`. **Units go in the name:** `TTL_SECONDS`, `READ_CHARS`,
  `POLL_MS`, `TIMEOUT_MINUTES`. Use numeric separators: `20_000`. Constants are public and carry
  an attribute docstring.
- **Booleans:**
  - Stored flags: `is_<state>` (`is_default`, `is_active`).
  - Toggles: `<feature>_enabled` in settings, `include_<thing>` for query switches.
  - Abilities: `can_<verb>`.
  - Computed predicates are adjective `@property`s (`settled`, `expired`, `live`).
- **Columns:**
  - Foreign keys: `<entity>_id`.
  - Owner: `created_by_user_id`.
  - Tenancy: `org_id`, `project_id`.
  - Human label: `display_name`. Never `name`, which is reserved for a derived identifier or
    path.
  - Timestamps: `created_at`, `updated_at`, `<event>_at` (`sent_at`, `expires_at`).
  - Counts: `<thing>_count`.
- **Enums:** `StrEnum` with UPPER members and lowercase values:
  `PENDING = "pending"`.
- **Loggers:** `logger = get_logger("<area>.<module>")`. The name is a short dotted string,
  never `__name__`: `"api.notes"`, `"services.invoices"`, `"auth.verify"`.
- **Collections:** plural nouns (`invoices`, `line_items`). A mapping is `<value>_by_<key>`
  (`invoices_by_id`), or a `roles`-style plural when the key is obvious.
- **Loop variables:** a real noun (`for invoice in invoices`). Single letters only in
  comprehensions over obvious things (`[p for p in projects if p.id in roles]`).

## Tests

- **Behaviour sentences:** `test_a_viewer_cannot_create_an_invoice`,
  `test_an_unknown_patch_field_is_refused_not_dropped`, `test_health_is_open_for_probes`.
- Fixture factories are `make_<thing>`; value fixtures are plain nouns (`org_id`, `user`).
- Module test constants: `TEST_<THING>_ID = "<prefix>_test_fixture"`.

## Env vars

See `config.md`. In short: env var = `<APP>_` + the settings field name, upper-cased. The
field name carries the subsystem prefix (`database_url`, `s3_bucket`) and the unit suffix
(`invite_ttl_days`).
