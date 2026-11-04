"""Infrastructure settings shared by every process of the app.

This module defines the class only. ``config.py`` instantiates it beside the service's own
settings and owns the lifecycle of what it configures; nothing here reads the environment on
import.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    """Infrastructure config: logging, the database pool, and outbound HTTP.

    Apps instantiate this beside their own settings class rather than inheriting from it: two
    parallel reads of the same ``{{APP}}_`` environment, each owning only its own fields.
    """

    model_config = SettingsConfigDict(env_prefix="{{APP}}_", extra="ignore")

    debug: bool = True

    database_url: str = "postgresql+asyncpg://{{app}}:{{app}}@localhost:5432/{{app}}"
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_pool_timeout_seconds: int = 30
    database_pool_recycle_seconds: int = 3600
