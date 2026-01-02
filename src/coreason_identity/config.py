from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreasonIdentityConfig(BaseSettings):
    """
    Configuration for Coreason Identity package.
    """

    domain: str
    audience: str

    model_config = SettingsConfigDict(env_prefix="COREASON_AUTH_")
