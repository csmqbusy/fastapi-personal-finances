from pathlib import Path

from pydantic import BaseModel, AmqpDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_correct_cwd(
    additional_workdir_path: str | None = None,
    sources_dir_name: str = "app",
) -> Path:
    """
    This function is needed to correctly launch the application from
    the app/main.py file and alembic commands from the project root folder.

    :param additional_workdir_path:
    """
    cwd = Path.cwd()
    if additional_workdir_path:
        cwd = cwd.joinpath(additional_workdir_path)
    if cwd.name == sources_dir_name:
        cwd = cwd.parent
    return cwd


class MessageBrokerConfig(BaseModel):
    url: str
    charts_service_queue_name: str = "charts-service-queue"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=get_correct_cwd(
            additional_workdir_path="charts_service") / ".env.dev",
        case_sensitive=False,
        env_nested_delimiter="__",
    )

    broker: MessageBrokerConfig


settings = Settings()  # type: ignore
