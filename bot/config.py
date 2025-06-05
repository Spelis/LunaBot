from pydantic import DirectoryPath, FilePath, PostgresDsn
from pydantic_settings import BaseSettings

from .banner import builtin_banner_path
from .modules import builtin_directory


class LoggerSettings(BaseSettings):
    directory: str = "logs"
    file_name: str = "luna.log"
    max_bytes: int = 10 * 1024 * 1024  # 10 MiB
    debug: bool = False

    class Config:
        env_file = ".env"
        env_prefix = "logging_"
        extra = "allow"


class Settings(BaseSettings):
    token: str
    prefix: str = "!"
    developer_ids: list[int] = []
    postgres_uri: PostgresDsn | None = None
    db_file: FilePath | None = None
    banner_file: FilePath | None = builtin_banner_path
    show_banner: bool = True
    logger_settings: LoggerSettings = LoggerSettings()
    modules_dir: DirectoryPath = builtin_directory

    @property
    def sqlite_uri(self) -> str:
        """
        The URI to use for connecting to the SQLite database.

        This is only used if `postgres_uri` is not set. If `sqlite_file` is not set,
        an in-memory SQLite database is used.
        """
        return (
            f"sqlite+aiosqlite:///{self.db_file}"
            if self.db_file
            else "sqlite+aiosqlite:///:memory:"
        )

    @property
    def database_uri(self) -> str:
        """
        The URI to use for the database connection.

        If `postgres_uri` is set, that is used. Otherwise, if `sqlite_file` is set,
        that is used. Otherwise, an in-memory SQLite database is used.
        """
        return str(self.postgres_uri) if self.postgres_uri else self.sqlite_uri

    @property
    def modules_import_prefix(self) -> str:
        return self.modules_dir.as_posix().replace("/", ".")

    @property
    def modules_directory(self) -> FilePath:
        return self.modules_dir.resolve()

    class Config:
        env_file = ".env"
        env_prefix = "luna_"
        extra = "allow"


settings: Settings = Settings()  # type: ignore

if __name__ == "__main__":
    print(settings.model_dump_json(indent=4))
