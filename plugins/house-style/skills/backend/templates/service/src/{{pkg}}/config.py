"""Service settings and the live infra instances the rest of the app imports.

``CoreSettings`` and ``ServiceSettings`` are two parallel reads of the same environment, each
owning only its own fields. ``db`` is constructed here; its lifecycle belongs to ``main.py``.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

from {{pkg}}.lib.config import CoreSettings
from {{pkg}}.lib.db import Database
from {{pkg}}.lib.utils.logger import setup_logging


class ServiceSettings(BaseSettings):
    """Settings only this service reads, from ``{{APP}}_``-prefixed environment variables.

    ``public_url`` is the web app's public origin, which links in emails and redirects point
    at and which no request to this service can reveal.
    """

    model_config = SettingsConfigDict(env_prefix="{{APP}}_", extra="ignore")

    public_url: str = "http://localhost:3000"


core = CoreSettings()
settings = ServiceSettings()

setup_logging(debug=core.debug)

db = Database(
    core.database_url,
    echo=core.database_echo,
    pool_size=core.database_pool_size,
    max_overflow=core.database_max_overflow,
    pool_timeout_seconds=core.database_pool_timeout_seconds,
    pool_recycle_seconds=core.database_pool_recycle_seconds,
)
